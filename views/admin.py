import streamlit as st
from sqlalchemy import select

from app import models as m, store
import ui

ROLES = ["recruiter", "hr_manager", "admin"]


def render(db, user):
    ui.topbar("Team & activity", "Manage access and review who did what", user)
    t1, t2 = st.tabs(["Users", "Activity log"])
    with t1:
        with st.container(key="card_adduser"):
            st.markdown(ui.card_title("Add user"), unsafe_allow_html=True)
            with st.form("newuser", clear_on_submit=True):
                a, b = st.columns(2)
                name, email = a.text_input("Full name"), b.text_input("Email")
                c, d = st.columns(2)
                pw, role = c.text_input("Password (min 8)", type="password"), d.selectbox("Role", ROLES, format_func=lambda r: r.replace("_", " ").title())
                if st.form_submit_button("Add user", type="primary"):
                    try:
                        store.create_user(db, email, name, pw, role, user)
                        st.session_state.flash = "User added"
                        st.rerun()
                    except ValueError as ex:
                        st.error(str(ex))
        st.write("")
        with st.container(key="card_users"):
            for u in db.scalars(select(m.User).order_by(m.User.id)).all():
                c = st.columns([3, 1.4, 1, 0.8])
                c[0].markdown(f'<div class="crow">{ui.avatar(u.full_name)}<div><div class="nm">{ui.esc(u.full_name)}</div><div class="em">{ui.esc(u.email)}</div></div></div>', unsafe_allow_html=True)
                new_role = c[1].selectbox("Role", ROLES, index=ROLES.index(u.role), key=f"ur{u.id}", label_visibility="collapsed",
                                          format_func=lambda r: r.replace("_", " ").title(), disabled=u.id == user.id)
                active = c[2].checkbox("Active", u.is_active, key=f"ua{u.id}", disabled=u.id == user.id)
                if (new_role, active) != (u.role, u.is_active):
                    u.role, u.is_active = new_role, active
                    db.commit()
                    st.rerun()
    with t2:
        flt = st.text_input("Filter by action", placeholder="e.g. login, status_changed")
        stmt = select(m.AuditLog).order_by(m.AuditLog.id.desc()).limit(150)
        if flt:
            stmt = stmt.where(m.AuditLog.action == flt.strip())
        rows = db.scalars(stmt).all()
        with st.container(key="card_audit"):
            if not rows:
                ui.empty("No activity")
            for i, r in enumerate(rows):
                st.markdown(
                    f'<div class="trow {"p" if i % 2 == 0 else "t"}" style="padding:.55rem 1rem;margin-bottom:.4rem"><div class="col" style="width:150px"><small>{r.created_at.strftime("%d %b %Y %H:%M")}</small>'
                    f'<b>{ui.esc(r.user.full_name if r.user else "system")}</b></div><div class="col" style="width:190px"><small>Action</small><b>{ui.esc(r.action)}</b></div>'
                    f'<div class="col grow"><small>{ui.esc(r.entity)} {r.entity_id or ""}</small><span style="font-size:.78rem;color:#5b6690">{ui.esc(str(r.detail)[:140])}</span></div></div>',
                    unsafe_allow_html=True)
