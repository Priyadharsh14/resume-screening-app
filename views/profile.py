import streamlit as st
from sqlalchemy import select

from app import audit, models as m, store
from app.services.skills import canonical
import ui

STATUSES = [s.value for s in m.AppStatus]
DECISIONS = [("selected", "Select"), ("on_hold", "Hold"), ("rejected", "Reject")]
ROWS = [("required_skills", "Required skills"), ("preferred_skills", "Preferred skills"), ("experience", "Experience"),
        ("education", "Education"), ("semantic", "Semantic similarity")]


def _detail(k, v):
    return {"required_skills": f"{v.get('matched')}/{v.get('total')} matched", "preferred_skills": f"{v.get('matched')}/{v.get('total')} matched",
            "experience": f"{v.get('have')}y of {v.get('need')}y needed", "education": f"{v.get('have')} · need {v.get('need')}",
            "semantic": f"similarity {v.get('similarity')}"}[k]


def _size(n):
    return f"{n / 1024:.0f}kb" if n >= 1024 else f"{n}b"


def render(db, user):
    a = db.get(m.Application, st.session_state.get("app_id") or 0)
    if not a:
        st.session_state.page = "Candidates"
        st.rerun()
    c, job = a.candidate, a.job
    manager = user.role in ("admin", "hr_manager")

    h1, h2, h3, h4 = st.columns([1, 4.6, 1.3, 1.7])
    if h1.button("← Back"):
        st.session_state.page = "Candidates"
        st.rerun()
    h2.markdown(f'<h1 style="margin:0;font-size:2rem;font-weight:600">Candidate profile</h1>'
                f'<div style="color:{ui.MUTED};font-size:.88rem">{ui.esc(job.title)}</div>', unsafe_allow_html=True)
    blob = c.resume_blob
    if blob:
        h3.download_button("Resume", blob, c.original_filename or "resume", use_container_width=True)
    if manager:
        if h4.button("Approve & notify", type="primary", use_container_width=True):
            st.session_state.profile_tab_hint = True
    st.markdown('<hr style="margin:.6rem 0 1rem 0">', unsafe_allow_html=True)

    left, right = st.columns([2.15, 1])
    with left:
        p1, p2 = st.columns([1, 1.25])
        with p1:
            with st.container(key="card_profile"):
                name = c.name or c.original_filename
                st.markdown(
                    f'<div class="profile">{ui.avatar(name, 120)}<div class="name">{ui.esc(name)}</div>'
                    f'<div class="phone">{ui.esc(c.phone or "no phone found")}</div>'
                    f'<div class="mail">{ui.esc(c.email or "no email found")}</div>'
                    f'<div style="margin-top:.8rem">{ui.pill(a.status)}</div>'
                    f'<div style="margin-top:.9rem;display:flex;justify-content:center">{ui.ring(a.score, 64, 7)}</div></div>',
                    unsafe_allow_html=True)
        with p2:
            with st.container(key="card_general"):
                st.markdown(ui.card_title("General information", edit=True), unsafe_allow_html=True)
                assigned = db.get(m.User, a.assigned_to) if a.assigned_to else None
                st.markdown(ui.kv([
                    ("Applied for", ui.esc(job.title)), ("Experience", f"{c.experience_years:g} years"),
                    ("Education", ui.esc((c.education_level or "not detected").title())),
                    ("Registration date", a.created_at.strftime("%A, %b %d")),
                    ("Assigned to", ui.esc(assigned.full_name) if assigned else "Unassigned"),
                ]), unsafe_allow_html=True)
        st.write("")
        with st.container(key="card_tabs"):
            email_logs = db.scalars(select(m.EmailLog).where(m.EmailLog.application_id == a.id).order_by(m.EmailLog.id.desc())).all()
            t1, t2, t3 = st.tabs(["Score breakdown", "Decision & workflow", f"Email history ({len(email_logs)})"])
            with t1:
                st.write("")
                if not a.breakdown:
                    ui.empty("Not scored yet")
                for i, (k, label) in enumerate(ROWS):
                    v = (a.breakdown or {}).get(k)
                    if not v:
                        continue
                    pct = v["points"] / v["max"] * 100
                    state = "Full" if pct >= 99.9 else "None" if pct == 0 else "Partial"
                    st.markdown(
                        f'<div class="trow {"p" if i % 2 == 0 else "t"}"><div class="col" style="width:160px"><small>Component</small><b>{label}</b></div>'
                        f'<div class="col grow"><small>{_detail(k, v)}</small><div class="bar"><i style="width:{pct:.0f}%"></i></div></div>'
                        f'<div class="col" style="width:90px"><small>Points</small><b>{v["points"]} / {v["max"]}</b></div>'
                        f'<div class="col"><span class="pill" style="background:#fff;color:{"#0f8f78" if state == "Full" else "#d1304f" if state == "None" else "#b27a06"}">{state}</span></div></div>',
                        unsafe_allow_html=True)
            with t2:
                st.write("")
                w1, w2 = st.columns(2)
                new_status = w1.selectbox("Status", STATUSES, index=STATUSES.index(a.status), key=f"st_{a.id}")
                staff = db.scalars(select(m.User).where(m.User.is_active.is_(True))).all()
                opts = [None] + [u.id for u in staff]
                new_as = w2.selectbox("Assigned to", opts, index=opts.index(a.assigned_to) if a.assigned_to in opts else 0,
                                      key=f"as_{a.id}", format_func=lambda i: "Unassigned" if i is None else next(u.full_name for u in staff if u.id == i))
                if new_status != a.status or new_as != a.assigned_to:
                    if new_status in store.FINAL and not manager:
                        st.error("Selected/Rejected must be set by an HR Manager or Admin.")
                    elif st.button("Save changes", type="primary", key=f"sv_{a.id}"):
                        if new_status != a.status:
                            audit.log(db, user, "status_changed", "application", a.id, old=a.status, new=new_status)
                        if new_as != a.assigned_to:
                            audit.log(db, user, "assigned", "application", a.id, to=new_as)
                        a.status, a.assigned_to = new_status, new_as
                        db.commit()
                        st.session_state.flash = "Saved"
                        st.rerun()
                st.markdown("---")
                if manager:
                    st.markdown("**Approve & notify** — nothing is emailed until you confirm.")
                    if a.pending_decision:
                        st.info(f"Recruiter recommends: {a.pending_decision.replace('_', ' ')}")
                    if not c.email:
                        st.warning("No email address found on this resume — cannot notify.")
                    d = st.columns(3)
                    for col, (dec, label) in zip(d, DECISIONS):
                        if col.button(f"Approve & {label.lower()}", key=f"dec_{dec}_{a.id}", disabled=not c.email):
                            st.session_state.confirm = dec
                    dec = st.session_state.get("confirm")
                    if dec:
                        st.warning(f"Send the **{dec.replace('_', ' ')}** email to {c.name} <{c.email}>? This cannot be undone.")
                        y, n, _ = st.columns([1, 1, 4])
                        if y.button("Confirm & send", type="primary", key="confirm_yes"):
                            try:
                                row = store.notify(db, a, dec, user)
                                st.session_state.flash = "Email sent" if row.status == "sent" else f"Email {row.status}: {row.error}"
                            except ValueError as ex:
                                st.session_state.flash = str(ex)
                            st.session_state.pop("confirm", None)
                            st.rerun()
                        if n.button("Cancel", key="confirm_no"):
                            st.session_state.pop("confirm", None)
                            st.rerun()
                else:
                    st.markdown("Only an HR Manager can approve and send. You can recommend an outcome:")
                    rec = ["", "selected", "on_hold", "rejected"]
                    pick = st.selectbox("Recommendation", rec, index=rec.index(a.pending_decision or ""),
                                        format_func=lambda x: x.replace("_", " ").title() or "None", key=f"rec_{a.id}")
                    if pick != (a.pending_decision or "") and st.button("Save recommendation", type="primary"):
                        a.pending_decision = pick
                        audit.log(db, user, "decision_proposed", "application", a.id, decision=pick)
                        db.commit()
                        st.rerun()
            with t3:
                st.write("")
                if not email_logs:
                    ui.empty("No emails sent for this candidate")
                for i, l in enumerate(email_logs):
                    st.markdown(
                        f'<div class="trow {"p" if i % 2 == 0 else "t"}"><div class="col" style="width:150px"><small>{l.created_at.strftime("%d %b %Y %H:%M")}</small><b>{l.kind.replace("_", " ").title()}</b></div>'
                        f'<div class="col grow"><small>Subject</small><b>{ui.esc(l.subject)}</b>{f"<small style=color:#d1304f>{ui.esc(l.error)}</small>" if l.error else ""}</div>'
                        f'<div class="col">{ui.pill(l.status)}</div></div>', unsafe_allow_html=True)
                    if l.status != "sent" and manager and st.button("Resend", key=f"rs_{l.id}"):
                        from app.services import pipeline
                        pipeline.deliver_email(db, l.id)
                        st.rerun()

    with right:
        with st.container(key="card_skills_p"):
            st.markdown(ui.card_title("Skills & match", edit=True), unsafe_allow_html=True)
            st.markdown(ui.kv([
                ("Matched", ui.chips(a.matched_skills or [], "g", "none")),
                ("Missing required", ui.chips(a.missing_skills or [], "r", "none 🎉")),
                ("All detected", ui.chips(sorted(cs.skill.name for cs in c.skills), "n")),
            ]), unsafe_allow_html=True)
        st.write("")
        with st.container(key="card_files"):
            st.markdown('<div class="card-title">Files <span style="margin-left:auto" class="outline">RESUME</span></div>', unsafe_allow_html=True)
            size = _size(len(blob)) if blob else ""
            st.markdown(f'<div class="filerow"><span class="ic">📄</span>{ui.esc(c.original_filename)}<span class="sz">{size}</span></div>', unsafe_allow_html=True)
            with st.expander("Parsed resume text"):
                st.text(c.resume_text[:6000] or "(empty)")
        st.write("")
        with st.container(key="card_notes"):
            st.markdown('<div class="card-title">Notes <span style="margin-left:auto" class="outline">COMMENTS</span></div>', unsafe_allow_html=True)
            if not a.comments:
                st.markdown(f'<div style="color:{ui.MUTED};font-size:.85rem">No notes yet.</div>', unsafe_allow_html=True)
            for cm in a.comments:
                who = cm.user.full_name if cm.user else "System"
                st.markdown(f'<div class="filerow" style="align-items:flex-start"><span class="ic">📝</span><div>{ui.esc(cm.body)}'
                            f'<div style="color:{ui.MUTED};font-size:.74rem">{ui.esc(who)} · {cm.created_at.strftime("%d %b %H:%M")}</div></div></div>',
                            unsafe_allow_html=True)
            with st.form(f"note_{a.id}", clear_on_submit=True):
                body = st.text_area("Add a note", height=70, label_visibility="collapsed", placeholder="Write a note…")
                if st.form_submit_button("Add note", type="primary") and body.strip():
                    db.add(m.Comment(application_id=a.id, user_id=user.id, body=body.strip()[:5000]))
                    audit.log(db, user, "comment_added", "application", a.id)
                    db.commit()
                    st.rerun()
