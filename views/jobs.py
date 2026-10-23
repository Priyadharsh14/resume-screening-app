import streamlit as st
from sqlalchemy import func, select

from app import audit, models as m
from app.services import pipeline
from app.services.skills import canonical
import ui

EDU = ["", "diploma", "bachelor", "master", "phd"]


def _split(s: str) -> list[str]:
    seen, out = set(), []
    for x in s.split(","):
        x = canonical(x.strip())
        if x and x.lower() not in seen:
            seen.add(x.lower())
            out.append(x)
    return out


def job_form(db, user, job: m.Job | None):
    with st.form(f"jobform_{job.id if job else 'new'}", clear_on_submit=job is None):
        title = st.text_input("Title", job.title if job else "", placeholder="e.g. Backend Engineer")
        desc = st.text_area("Job description (semantic matching · 15 pts)", job.description if job else "", height=120)
        a, b = st.columns(2)
        req = a.text_input("Required skills · 45 pts", ", ".join(job.required_skills) if job else "", placeholder="Python, FastAPI, PostgreSQL")
        pref = b.text_input("Preferred skills · 10 pts", ", ".join(job.preferred_skills) if job else "", placeholder="Docker, Redis")
        c, d, e = st.columns(3)
        exp = c.number_input("Min experience (years) · 20 pts", 0.0, 50.0, float(job.min_experience_years) if job else 0.0, 0.5)
        edu = d.selectbox("Min education · 10 pts", EDU, index=EDU.index(job.required_education) if job else 0,
                          format_func=lambda x: x.title() or "Not required")
        thr = e.number_input("Pass threshold (≥ → Shortlisted)", 0, 100, int(job.pass_threshold) if job else 60)
        is_open = st.checkbox("Open for applications", job.is_open if job else True)
        if st.form_submit_button("Save job", type="primary"):
            if not title.strip():
                st.error("Title is required")
                return False
            req_l = _split(req)
            pref_l = [s for s in _split(pref) if s not in req_l]
            if job is None:
                job = m.Job(created_by=user.id)
                db.add(job)
            job.title, job.description, job.required_skills, job.preferred_skills = title.strip(), desc, req_l, pref_l
            job.min_experience_years, job.required_education, job.pass_threshold, job.is_open = exp, edu, thr, is_open
            db.flush()
            audit.log(db, user, "job_saved", "job", job.id, title=job.title)
            db.commit()
            pipeline.rescore_job(db, job.id)  # criteria changed → refresh scores
            st.session_state.flash = "Job saved"
            return True
    return False


def render(db, user):
    ui.topbar("Jobs", "Define what a good match looks like", user)
    manager = user.role in ("admin", "hr_manager")
    if manager:
        _, r = st.columns([5, 1])
        if r.button("＋ New job", type="primary", use_container_width=True):
            st.session_state.edit_job = 0
    if manager and st.session_state.get("edit_job") == 0:
        with st.container(key="card_newjob"):
            st.markdown(ui.card_title("New job"), unsafe_allow_html=True)
            if job_form(db, user, None):
                st.session_state.pop("edit_job")
                st.rerun()
        st.write("")

    jobs = db.scalars(select(m.Job).order_by(m.Job.id.desc())).all()
    if not jobs:
        ui.empty("No jobs yet. " + ("Create one to start screening." if manager else "Ask an HR manager to create one."))
    for j in jobs:
        n = db.scalar(select(func.count()).select_from(m.Application).where(m.Application.job_id == j.id))
        with st.container(key=f"card_job_{j.id}"):
            st.markdown(
                f'<div class="card-title">{ui.esc(j.title)} <span class="pill" style="background:{"#d9f6ef" if j.is_open else "#eceffa"};'
                f'color:{"#0f8f78" if j.is_open else "#5b6690"}">{"Open" if j.is_open else "Closed"}</span></div>'
                f'<div style="color:{ui.MUTED};font-size:.82rem;margin-bottom:.6rem">{j.min_experience_years:g}+ yrs · '
                f'{ui.esc((j.required_education or "any education").title())} · pass ≥ {j.pass_threshold:g} · {n} candidates</div>'
                f'<div style="margin-bottom:.3rem"><small style="color:{ui.MUTED}">REQUIRED</small> {ui.chips(j.required_skills, "b")}</div>'
                f'<div><small style="color:{ui.MUTED}">PREFERRED</small> {ui.chips(j.preferred_skills, "n")}</div>',
                unsafe_allow_html=True)
            c = st.columns([1.2, 1, 1, 4])
            if c[0].button("Candidates", key=f"jc{j.id}"):
                st.session_state.update(page="Candidates", cand_job=j.id)
                st.rerun()
            if manager:
                if c[1].button("Edit", key=f"je{j.id}"):
                    st.session_state.edit_job = j.id
                with c[2]:
                    st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                    if st.button("Delete", key=f"jd{j.id}"):
                        st.session_state.confirm_del = j.id
                    st.markdown("</div>", unsafe_allow_html=True)
            if manager and st.session_state.get("confirm_del") == j.id:
                st.warning(f"Delete “{j.title}” and its {n} applications?")
                y, _ = st.columns([1, 5])
                if y.button("Yes, delete", key=f"jdy{j.id}", type="primary"):
                    audit.log(db, user, "job_deleted", "job", j.id, title=j.title)
                    db.delete(j)
                    db.commit()
                    st.session_state.pop("confirm_del")
                    st.rerun()
            if manager and st.session_state.get("edit_job") == j.id:
                st.markdown("---")
                if job_form(db, user, j):
                    st.session_state.pop("edit_job")
                    st.rerun()
        st.write("")
