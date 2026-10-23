"""Data operations used by the Streamlit views (the API layer of the original FastAPI app, minus HTTP)."""
import csv
import io
import uuid
from collections import Counter
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from . import audit, models as m
from .config import settings
from .security import hash_password
from .services import emailer, pipeline

ALLOWED = {".pdf": b"%PDF", ".docx": b"PK"}
DECISION_STATUS = {"selected": "Selected", "rejected": "Rejected", "on_hold": "On Hold"}
FINAL = {"Selected", "Rejected"}


def bootstrap(db: Session) -> None:
    for kind, (subj, body) in emailer.DEFAULT_TEMPLATES.items():
        if not db.scalar(select(m.EmailTemplate).where(m.EmailTemplate.kind == kind)):
            db.add(m.EmailTemplate(kind=kind, subject=subj, body=body))
    if settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD and not db.scalar(select(m.User).limit(1)):
        db.add(m.User(email=settings.ADMIN_EMAIL.lower(), full_name="Administrator", role="admin",
                      password_hash=hash_password(settings.ADMIN_PASSWORD)))
    db.commit()


def has_users(db: Session) -> bool:
    return db.scalar(select(m.User.id).limit(1)) is not None


def create_user(db: Session, email: str, name: str, password: str, role: str, actor=None) -> m.User:
    email = email.strip().lower()
    if "@" not in email or len(password) < 8:
        raise ValueError("Enter a valid email and a password of at least 8 characters")
    if db.scalar(select(m.User).where(m.User.email == email)):
        raise ValueError("That email is already registered")
    u = m.User(email=email, full_name=name.strip() or email, role=role, password_hash=hash_password(password))
    db.add(u)
    db.flush()
    audit.log(db, actor, "user_created", "user", u.id, role=role)
    db.commit()
    return u


def add_resumes(db: Session, user, job: m.Job, files: list[tuple[str, bytes]]):
    """files: [(filename, bytes)]. Parses + scores synchronously. Returns (accepted_ids, rejected[(name, why)])."""
    accepted, rejected = [], []
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    for name, data in files:
        ext = Path(name).suffix.lower()
        if ext not in ALLOWED:
            rejected.append((name, "Only PDF and DOCX files are accepted"))
        elif len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
            rejected.append((name, f"File exceeds {settings.MAX_UPLOAD_MB} MB"))
        elif not data.startswith(ALLOWED[ext]):
            rejected.append((name, "File content does not match its extension"))
        else:
            path = Path(settings.UPLOAD_DIR) / f"{uuid.uuid4().hex}{ext}"
            path.write_bytes(data)
            c = m.Candidate(resume_path=str(path), resume_blob=data, original_filename=Path(name).name[:255])
            c.applications.append(m.Application(job_id=job.id))
            db.add(c)
            db.flush()
            audit.log(db, user, "resume_uploaded", "candidate", c.id, filename=c.original_filename, job_id=job.id)
            accepted.append(c.id)
    db.commit()
    for cid in accepted:
        pipeline.process_candidate(db, cid)
    return accepted, rejected


def app_query(job_id=None, status=None, q=None, skill=None, min_score=None):
    stmt = select(m.Application).join(m.Candidate).options(
        joinedload(m.Application.candidate), joinedload(m.Application.job))
    if job_id:
        stmt = stmt.where(m.Application.job_id == job_id)
    if status:
        stmt = stmt.where(m.Application.status == status)
    if min_score:
        stmt = stmt.where(m.Application.score >= min_score)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(m.Candidate.name).like(like) | func.lower(m.Candidate.email).like(like)
                          | func.lower(m.Candidate.original_filename).like(like))
    if skill:
        sk = skill.strip().lower()
        stmt = stmt.where(m.Application.candidate_id.in_(
            select(m.CandidateSkill.candidate_id).join(m.Skill).where(func.lower(m.Skill.name) == sk)))
    return stmt.order_by(m.Application.score.desc().nulls_last(), m.Application.id)


def notify(db: Session, app: m.Application, decision: str, user) -> m.EmailLog:
    """Human-approved notification: logs, sends, records the outcome. Raises ValueError if it can't."""
    c = app.candidate
    if not c.email:
        raise ValueError("No email address was found on this resume")
    if db.scalar(select(m.EmailLog).where(m.EmailLog.application_id == app.id, m.EmailLog.kind == decision,
                                          m.EmailLog.status.in_(["queued", "sent"]))):
        raise ValueError(f"A '{decision.replace('_', ' ')}' email was already sent for this application")
    tpl = db.scalar(select(m.EmailTemplate).where(m.EmailTemplate.kind == decision))
    subject, body = (tpl.subject, tpl.body) if tpl else emailer.DEFAULT_TEMPLATES[decision]
    ctx = {"name": c.name or "Candidate", "job_title": app.job.title}
    row = m.EmailLog(application_id=app.id, to_email=c.email, kind=decision, approved_by=user.id,
                     subject=emailer.render(subject, **ctx), body=emailer.render(body, **ctx))
    db.add(row)
    app.status = DECISION_STATUS[decision]
    app.pending_decision = ""
    db.flush()
    audit.log(db, user, "approved_and_notified", "application", app.id, decision=decision, email_log_id=row.id)
    db.commit()
    pipeline.deliver_email(db, row.id)
    db.refresh(row)
    return row


def stats(db: Session, job_id=None) -> dict:
    base = select(m.Application)
    if job_id:
        base = base.where(m.Application.job_id == job_id)
    apps = db.scalars(base).all()
    scores = [a.score for a in apps if a.score is not None]
    by_status = Counter(a.status for a in apps)
    buckets = Counter(min(int(s // 10), 9) for s in scores)
    skill_q = (select(m.Skill.name, func.count()).select_from(m.CandidateSkill).join(m.Skill)
               .group_by(m.Skill.name).order_by(func.count().desc()).limit(8))
    if job_id:
        skill_q = skill_q.where(m.CandidateSkill.candidate_id.in_(
            select(m.Application.candidate_id).where(m.Application.job_id == job_id)))
    emails = Counter(db.scalars(select(m.EmailLog.status)).all())
    return {
        "applications": len(apps), "avg": round(sum(scores) / len(scores), 1) if scores else None,
        "by_status": {s.value: by_status.get(s.value, 0) for s in m.AppStatus},
        "dist": [buckets.get(i, 0) for i in range(10)],
        "skills": db.execute(skill_q).all(), "emails": emails,
        "candidates": db.scalar(select(func.count()).select_from(m.Candidate)),
        "open_jobs": db.scalar(select(func.count()).select_from(m.Job).where(m.Job.is_open.is_(True))),
    }


def _safe(v):
    s = "" if v is None else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@", "\t", "\r") else s  # block CSV formula injection


def export_csv(apps) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Job", "Name", "Email", "Phone", "Experience (yrs)", "Education", "Score", "Status",
                "Matched skills", "Missing skills", "All skills"])
    for a in apps:
        c = a.candidate
        w.writerow([_safe(x) for x in [a.job.title, c.name, c.email, c.phone, c.experience_years, c.education_level,
                                       a.score, a.status, "; ".join(a.matched_skills or []),
                                       "; ".join(a.missing_skills or []),
                                       "; ".join(sorted(cs.skill.name for cs in c.skills))]])
    return buf.getvalue()
