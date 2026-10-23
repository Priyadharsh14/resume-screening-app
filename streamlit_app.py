import os

import streamlit as st

st.set_page_config(page_title="Resume Screening", page_icon="📄", layout="wide", initial_sidebar_state="expanded")

# Copy Streamlit secrets into the environment before the app package reads its settings.
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, (str, int, float, bool)):
            os.environ.setdefault(str(_k).upper(), str(_v))
except Exception:  # no secrets file locally: fall back to env vars / defaults
    pass

from app import models as m, store  # noqa: E402
from app.database import SessionLocal, init_db  # noqa: E402
from app.security import verify_password  # noqa: E402
from sqlalchemy import select  # noqa: E402
import ui  # noqa: E402
from views import admin, candidates, dashboard, emails, jobs, profile  # noqa: E402

ui.inject()


@st.cache_resource
def _setup():
    init_db()
    with SessionLocal() as db:
        store.bootstrap(db)
    return True


_setup()

NAV = [("Dashboard", ":material/dashboard:", dashboard, None), ("Jobs", ":material/work:", jobs, None),
       ("Candidates", ":material/groups:", candidates, None), ("Emails", ":material/mail:", emails, "manager"),
       ("Team", ":material/shield_person:", admin, "admin")]


def login_screen(db):
    first_run = not store.has_users(db)
    _, mid, _ = st.columns([0.15, 3, 0.15])
    hero, form = mid.columns([1.15, 1], gap="medium")
    with hero:
        with st.container(key="card_hero"):
            st.markdown(
                '<div class="brand" style="padding:0;color:#fff">RESUME SCREENING</div><span class="tag">HIRING PLATFORM</span>'
                '<h2>Hire faster,<br>with clarity.</h2><ul style="padding:0">'
                '<li>Parse PDF &amp; DOCX resumes automatically</li><li>Transparent 100-point score for every candidate</li>'
                '<li>Role-based access for your whole HR team</li><li>A human approves every email that goes out</li></ul>',
                unsafe_allow_html=True)
    with form, st.container(key="card_login"):
        st.markdown('<div style="height:2.2rem"></div>', unsafe_allow_html=True)
        if first_run:
            st.markdown(ui.card_title("Create the first admin account"), unsafe_allow_html=True)
            with st.form("setup"):
                name, email = st.text_input("Full name"), st.text_input("Email")
                pw = st.text_input("Password (min 8 characters)", type="password")
                if st.form_submit_button("Create admin", type="primary"):
                    try:
                        u = store.create_user(db, email, name, pw, "admin")
                        st.session_state.uid = u.id
                        st.rerun()
                    except ValueError as ex:
                        st.error(str(ex))
        else:
            st.markdown(ui.card_title("Welcome back"), unsafe_allow_html=True)
            with st.form("login"):
                email, pw = st.text_input("Email"), st.text_input("Password", type="password")
                if st.form_submit_button("Sign in", type="primary"):
                    u = db.scalar(select(m.User).where(m.User.email == email.strip().lower()))
                    if u and u.is_active and verify_password(pw, u.password_hash):
                        st.session_state.uid = u.id
                        store_audit(db, u)
                        st.rerun()
                    st.error("Incorrect email or password")


def store_audit(db, u):
    from app import audit
    audit.log(db, u, "login", "user", u.id)
    db.commit()


def main():
    db = SessionLocal()
    try:
        user = db.get(m.User, st.session_state.get("uid") or 0)
        if not user or not user.is_active:
            st.session_state.pop("uid", None)
            return login_screen(db)

        allowed = [n for n in NAV if n[3] is None or (n[3] == "manager" and user.role in ("admin", "hr_manager")) or (n[3] == "admin" and user.role == "admin")]
        page = st.session_state.setdefault("page", "Dashboard")
        with st.sidebar:
            st.markdown('<div class="brand">RESUME SCREENING</div>', unsafe_allow_html=True)
            for label, icon, _, _ in allowed:
                active = page == label or (page == "Profile" and label == "Candidates")
                if st.button(label, icon=icon, key=f"nav_{label}", type="primary" if active else "secondary", use_container_width=True):
                    st.session_state.page = label
                    st.rerun()
            st.markdown("---")
            if st.button("Sign out", icon=":material/logout:", key="nav_out", use_container_width=True):
                st.session_state.clear()
                st.rerun()
            st.markdown(
                '<div class="promo"><b>How scoring works</b><small>Required skills 45 · Preferred 10 · Experience 20 · Education 10 · '
                'Semantic match 15. Name, gender, age, photo, religion and address are never used.</small>'
                f'<span class="pill">{ui.esc(user.full_name.upper())}</span></div>', unsafe_allow_html=True)

        if msg := st.session_state.pop("flash", None):
            st.toast(msg)
        if page == "Profile":
            ui.inject()
            profile.render(db, user)
        else:
            view = next((n[2] for n in allowed if n[0] == page), dashboard)
            view.render(db, user)
        st.markdown('<div class="sitefoot">© Resume Screening · Internal use only · Scores use skills, experience, education and text similarity only</div>', unsafe_allow_html=True)
    finally:
        db.close()


main()
