import enum
from datetime import datetime, timezone

from sqlalchemy import (
    JSON, Boolean, DateTime, LargeBinary, Float, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    admin = "admin"
    hr_manager = "hr_manager"
    recruiter = "recruiter"


class AppStatus(str, enum.Enum):
    new = "New"
    screened = "Screened"
    shortlisted = "Shortlisted"
    selected = "Selected"
    rejected = "Rejected"
    on_hold = "On Hold"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default=Role.recruiter.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    required_skills: Mapped[list] = mapped_column(JSON, default=list)
    preferred_skills: Mapped[list] = mapped_column(JSON, default=list)
    min_experience_years: Mapped[float] = mapped_column(Float, default=0)
    required_education: Mapped[str] = mapped_column(String(32), default="")  # "", bachelor, master, phd
    pass_threshold: Mapped[float] = mapped_column(Float, default=60)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(64), default="")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    skill = relationship("Skill")


class Candidate(Base):
    __tablename__ = "candidates"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    experience_years: Mapped[float] = mapped_column(Float, default=0)
    education_level: Mapped[str] = mapped_column(String(32), default="")
    education: Mapped[list] = mapped_column(JSON, default=list)
    resume_text: Mapped[str] = mapped_column(Text, default="")
    resume_path: Mapped[str] = mapped_column(String(512), default="")
    resume_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)  # keeps downloads working on ephemeral hosts
    original_filename: Mapped[str] = mapped_column(String(255), default="")
    parse_status: Mapped[str] = mapped_column(String(32), default="pending")  # pending|parsed|failed
    parse_error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    skills = relationship("CandidateSkill", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default=AppStatus.new.value, index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    matched_skills: Mapped[list] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, default=list)
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # Decision awaiting human approval (set by HR; email only sent on approve-and-notify)
    pending_decision: Mapped[str] = mapped_column(String(32), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    job = relationship("Job", back_populates="applications")
    candidate = relationship("Candidate", back_populates="applications")
    comments = relationship("Comment", cascade="all, delete-orphan", order_by="Comment.id")


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user = relationship("User")


class EmailTemplate(Base):
    __tablename__ = "email_templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), unique=True)  # selected | rejected | on_hold
    subject: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)


class EmailLog(Base):
    __tablename__ = "email_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int | None] = mapped_column(ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    to_email: Mapped[str] = mapped_column(String(255))
    kind: Mapped[str] = mapped_column(String(32))
    subject: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="queued")  # queued|sent|failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    entity: Mapped[str] = mapped_column(String(64), default="")
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    user = relationship("User")
