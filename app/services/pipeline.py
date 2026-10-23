from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..audit import log
from . import emailer, parser, scoring
from .skills import category


def apply_score(app: m.Application, db: Session) -> None:
    c, job = app.candidate, app.job
    res = scoring.score_candidate(job, [cs.skill.name for cs in c.skills], c.experience_years,
                                  c.education_level, c.resume_text)
    app.score = res["score"]
    app.matched_skills = res["matched_skills"]
    app.missing_skills = res["missing_skills"]
    app.breakdown = {**res["breakdown"], "missing_preferred": res["missing_preferred"]}
    # Only automate the early pipeline stages; decisions (Selected/Rejected/On Hold) stay human-made.
    if app.status in (m.AppStatus.new.value, m.AppStatus.screened.value, m.AppStatus.shortlisted.value):
        app.status = (m.AppStatus.shortlisted if app.score >= job.pass_threshold else m.AppStatus.screened).value


def _get_or_create_skill(db: Session, name: str) -> m.Skill:
    sk = db.scalar(select(m.Skill).where(m.Skill.name == name))
    if not sk:
        sk = m.Skill(name=name, category=category(name))
        db.add(sk)
        db.flush()
    return sk


def process_candidate(db: Session, candidate_id: int) -> None:
    c = db.get(m.Candidate, candidate_id)
    if not c:
        return
    try:
        p = parser.parse_file(c.resume_path)
    except Exception as e:  # corrupt / unreadable file
        c.parse_status, c.parse_error = "failed", str(e)[:500]
        log(db, None, "resume_parse_failed", "candidate", c.id, error=str(e)[:200])
        db.commit()
        return

    # Duplicate by email: fold this upload into the existing candidate.
    if p.email:
        existing = db.scalar(select(m.Candidate).where(m.Candidate.email == p.email, m.Candidate.id != c.id))
        if existing:
            for app in list(c.applications):
                dup = db.scalar(select(m.Application).where(
                    m.Application.job_id == app.job_id, m.Application.candidate_id == existing.id))
                if dup:
                    db.delete(app)
                else:
                    app.candidate_id = existing.id
            db.flush()
            log(db, None, "duplicate_merged", "candidate", existing.id, merged_from=c.id)
            db.delete(c)
            db.flush()
            db.expire_all()
            c = existing
            c.resume_text = p.text  # newest resume text wins
            _fill(db, c, p)
            _rescore(db, c)
            db.commit()
            return

    c.email = p.email
    _fill(db, c, p)
    _rescore(db, c)
    log(db, None, "resume_parsed", "candidate", c.id, skills=len(p.skills))
    db.commit()


def _fill(db: Session, c: m.Candidate, p: parser.Parsed) -> None:
    c.name = p.name or c.name or ""
    c.phone, c.experience_years = p.phone, p.experience_years
    c.education_level, c.education = p.education_level, p.education
    c.resume_text = p.text
    c.parse_status, c.parse_error = "parsed", ""
    c.skills.clear()
    db.flush()
    for s in p.skills:
        c.skills.append(m.CandidateSkill(skill_id=_get_or_create_skill(db, s).id))
    db.flush()
    db.refresh(c)


def _rescore(db: Session, c: m.Candidate) -> None:
    for app in c.applications:
        apply_score(app, db)


def rescore_job(db: Session, job_id: int) -> int:
    apps = db.scalars(select(m.Application).join(m.Candidate).where(
        m.Application.job_id == job_id, m.Candidate.parse_status == "parsed")).all()
    for a in apps:
        apply_score(a, db)
    db.commit()
    return len(apps)


def deliver_email(db: Session, log_id: int) -> bool:
    """Send one queued/failed email; updates the log row. Returns success."""
    row = db.get(m.EmailLog, log_id)
    if not row or row.status == "sent":
        return bool(row)
    row.attempts += 1
    try:
        emailer.send(row.to_email, row.subject, row.body)
        row.status, row.error = "sent", ""
        row.sent_at = datetime.now(timezone.utc)
        ok = True
    except Exception as e:
        row.status, row.error = "failed", str(e)[:500]
        ok = False
    db.commit()
    return ok
