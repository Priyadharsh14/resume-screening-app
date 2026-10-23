import os
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="st_test_")
os.environ.update({"DATABASE_URL": f"sqlite:///{_tmp}/t.db", "UPLOAD_DIR": f"{_tmp}/up", "ADMIN_EMAIL": "admin@example.com",
                   "ADMIN_PASSWORD": "AdminPass123!", "EMAIL_BACKEND": "smtp"})

import pytest  # noqa: E402
from sqlalchemy import select  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402

from app import models as m, store  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.services import emailer  # noqa: E402
from tests.sample_data import generate  # noqa: E402

ROOT = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
SENT = []


@pytest.fixture(scope="module")
def seeded():
    init_db()
    emailer.send = lambda to, subject, body: SENT.append((to, subject, body))
    with SessionLocal() as db:
        store.bootstrap(db)
        admin = db.scalar(select(m.User))
        job = m.Job(title="Backend Engineer", description="Python APIs FastAPI PostgreSQL", required_skills=["Python", "FastAPI", "PostgreSQL"],
                    preferred_skills=["Docker", "Redis"], min_experience_years=3, required_education="bachelor", pass_threshold=60)
        db.add(job)
        db.commit()
        files = [(p.name, p.read_bytes()) for p in generate(Path(_tmp) / "s", n=52)]
        ok, bad = store.add_resumes(db, admin, job, files)
        return {"ok": len(ok), "bad": bad, "job": job.id}


def test_bulk_upload_parsed_and_ranked(seeded):
    assert seeded["ok"] == 52 and not seeded["bad"]
    with SessionLocal() as db:
        apps = db.scalars(store.app_query(seeded["job"])).unique().all()
        assert len(apps) == 52 and all(a.candidate.parse_status == "parsed" and a.candidate.email for a in apps)
        scores = [a.score for a in apps]
        assert scores == sorted(scores, reverse=True)
        assert {"Shortlisted", "Screened"} <= {a.status for a in apps}


def test_upload_rejects_bad_files(seeded):
    with SessionLocal() as db:
        job = db.get(m.Job, seeded["job"])
        ok, bad = store.add_resumes(db, db.scalar(select(m.User)), job, [("x.pdf", b"nope"), ("x.txt", b"hi")])
        assert not ok and len(bad) == 2


def test_notify_requires_call_and_blocks_duplicates(seeded):
    with SessionLocal() as db:
        user = db.scalar(select(m.User))
        a = db.scalars(store.app_query(seeded["job"])).unique().first()
        assert SENT == []  # scoring never emails
        row = store.notify(db, a, "selected", user)
        assert row.status == "sent" and SENT[-1][0] == a.candidate.email and "{{" not in SENT[-1][2]
        assert a.status == "Selected"
        with pytest.raises(ValueError):
            store.notify(db, a, "selected", user)


def test_csv_neutralises_formulas(seeded):
    with SessionLocal() as db:
        a = db.scalars(store.app_query(seeded["job"])).unique().first()
        a.candidate.name = "=HYPERLINK(\"x\")"
        csv_text = store.export_csv([a])
        assert "'=HYPERLINK" in csv_text
        db.rollback()


def _app():
    at = AppTest.from_file(ROOT, default_timeout=60)
    return at.run()


def test_login_screen_then_all_pages_render(seeded):
    at = _app()
    assert not at.exception
    at.text_input[0].set_value("admin@example.com")
    at.text_input[1].set_value("wrong")
    at.button[0].click()
    at.run()
    assert at.error and "Incorrect" in at.error[0].value
    at.text_input[1].set_value("AdminPass123!")
    at.button[0].click()
    at.run()
    assert not at.exception and "uid" in at.session_state
    for page in ["Dashboard", "Jobs", "Candidates", "Emails", "Team"]:
        at.session_state.page = page
        at.run()
        assert not at.exception, f"{page}: {at.exception}"
    with SessionLocal() as db:
        aid = db.scalars(store.app_query(seeded["job"])).unique().all()[3].id
    at.session_state.page, at.session_state.app_id = "Profile", aid
    at.run()
    assert not at.exception, at.exception
