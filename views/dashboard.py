import streamlit as st
from sqlalchemy import select

from app import models as m, store
import ui


def stat(col, icon, bg, n, label):
    with col:
        with st.container(key=f"card_stat_{label}"):
            st.markdown(f'<div class="stat"><span class="ico" style="background:{bg}">{icon}</span>'
                        f'<div><div class="n">{n if n is not None else "–"}</div><div class="l">{label}</div></div></div>',
                        unsafe_allow_html=True)


def render(db, user):
    ui.topbar("Dashboard", "Screening activity at a glance", user)
    jobs = db.scalars(select(m.Job).order_by(m.Job.title)).all()
    _, right = st.columns([3, 1])
    pick = right.selectbox("Job", [None] + [j.id for j in jobs], label_visibility="collapsed",
                           format_func=lambda i: "All jobs" if i is None else next(j.title for j in jobs if j.id == i))
    s = store.stats(db, pick)

    c = st.columns(4)
    stat(c[0], "📄", "#e6ebff", s["applications"], "Applications")
    stat(c[1], "👥", "#dff0ff", s["candidates"], "Candidates")
    stat(c[2], "✅", "#d9f6ef", s["avg"], "Average score")
    stat(c[3], "✉️", "#fff4dc", s["by_status"]["Shortlisted"], "Awaiting approval")
    st.write("")

    left, right = st.columns(2)
    with left:
        with st.container(key="card_pipeline"):
            st.markdown(ui.card_title("Pipeline"), unsafe_allow_html=True)
            total = max(s["applications"], 1)
            for k, v in s["by_status"].items():
                st.markdown(f'<div class="hbar"><span class="lbl">{k}</span><span class="tr"><i style="width:{v / total * 100:.0f}%;'
                            f'background:{ui.STATUS_DOT[k]}"></i></span><span class="ct">{v}</span></div>', unsafe_allow_html=True)
    with right:
        with st.container(key="card_dist"):
            st.markdown(ui.card_title("Score distribution"), unsafe_allow_html=True)
            st.markdown(ui.hbars([(f"{i * 10}–{i * 10 + 10 if i < 9 else 100}", n) for i, n in enumerate(s["dist"])], "#6b7fe8"),
                        unsafe_allow_html=True)
    st.write("")
    left, right = st.columns(2)
    with left:
        with st.container(key="card_skills"):
            st.markdown(ui.card_title("Top candidate skills"), unsafe_allow_html=True)
            rows = [(n, c) for n, c in s["skills"]]
            st.markdown(ui.hbars(rows, "#12b79b") if rows else '<div class="empty">Upload resumes to see skills</div>',
                        unsafe_allow_html=True)
    with right:
        with st.container(key="card_emails"):
            st.markdown(ui.card_title("Emails"), unsafe_allow_html=True)
            e = s["emails"]
            st.markdown("".join(f'<div style="display:inline-block;width:32%;text-align:center"><div style="font-size:2rem;font-weight:600">'
                                f'{e.get(k, 0)}</div>{ui.pill(k)}</div>' for k in ("sent", "queued", "failed")), unsafe_allow_html=True)
