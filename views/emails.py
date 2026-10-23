import streamlit as st
from sqlalchemy import select

from app import audit, models as m
from app.services import emailer, pipeline
import ui


def render(db, user):
    ui.topbar("Emails", "Templates and delivery log — sent only after approval", user)
    tpls = {t.kind: t for t in db.scalars(select(m.EmailTemplate))}
    cols = st.columns(3)
    for col, kind in zip(cols, ["selected", "on_hold", "rejected"]):
        t = tpls.get(kind)
        with col:
            with st.container(key=f"card_tpl_{kind}"):
                st.markdown(ui.card_title(kind.replace("_", " ").title(), edit=True), unsafe_allow_html=True)
                with st.form(f"tpl_{kind}"):
                    subj = st.text_input("Subject", t.subject if t else emailer.DEFAULT_TEMPLATES[kind][0])
                    body = st.text_area("Body", t.body if t else emailer.DEFAULT_TEMPLATES[kind][1], height=200)
                    st.caption("Placeholders: {{name}}, {{job_title}}")
                    if st.form_submit_button("Save", type="primary"):
                        if not t:
                            t = m.EmailTemplate(kind=kind, subject=subj, body=body)
                            db.add(t)
                        t.subject, t.body = subj, body
                        audit.log(db, user, "template_updated", "email_template", None, kind=kind)
                        db.commit()
                        st.session_state.flash = "Template saved"
                        st.rerun()
    st.write("")
    with st.container(key="card_logs"):
        a, b = st.columns([4, 1])
        a.markdown(ui.card_title("Email log"), unsafe_allow_html=True)
        flt = b.selectbox("Status", [None, "queued", "sent", "failed"], format_func=lambda x: x or "All", label_visibility="collapsed")
        stmt = select(m.EmailLog).order_by(m.EmailLog.id.desc()).limit(100)
        if flt:
            stmt = stmt.where(m.EmailLog.status == flt)
        logs = db.scalars(stmt).all()
        if not logs:
            ui.empty("No emails yet")
        for i, l in enumerate(logs):
            st.markdown(
                f'<div class="trow {"p" if i % 2 == 0 else "t"}"><div class="col" style="width:150px"><small>{l.created_at.strftime("%d %b %Y %H:%M")}</small><b>{ui.esc(l.to_email)}</b></div>'
                f'<div class="col grow"><small>{l.kind.replace("_", " ").title()}</small><b>{ui.esc(l.subject)}</b>'
                f'{f"<small style=color:#d1304f>{ui.esc(l.error)}</small>" if l.error else ""}</div>'
                f'<div class="col"><small>Tries {l.attempts}</small>{ui.pill(l.status)}</div></div>', unsafe_allow_html=True)
            if l.status != "sent" and st.button("Resend", key=f"rs{l.id}"):
                pipeline.deliver_email(db, l.id)
                st.rerun()
