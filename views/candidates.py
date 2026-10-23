import streamlit as st
from sqlalchemy import select

from app import models as m, store
import ui

PAGE = 15
STATUSES = [s.value for s in m.AppStatus]


def render(db, user):
    ui.topbar("Candidates", "Ranked by match score", user)
    manager = user.role in ("admin", "hr_manager")
    jobs = db.scalars(select(m.Job).order_by(m.Job.title)).all()
    jobmap = {j.id: j for j in jobs}

    with st.container(key="card_filters"):
        a, b, c, d, e = st.columns([1.4, 1.6, 1, 1, 0.8])
        job_id = a.selectbox("Job", [None] + list(jobmap), key="cand_job", format_func=lambda i: "All jobs" if i is None else jobmap[i].title)
        q = b.text_input("Search", placeholder="Name or email", key="cand_q")
        status = c.selectbox("Status", [None] + STATUSES, key="cand_status", format_func=lambda x: x or "Any status")
        skill = d.text_input("Skill", placeholder="e.g. Python", key="cand_skill")
        min_score = e.number_input("Min score", 0, 100, 0, key="cand_min")

    if job_id and jobmap[job_id].is_open:
        with st.container(key="card_upload"):
            st.markdown(ui.card_title(f"Upload resumes for {jobmap[job_id].title}"), unsafe_allow_html=True)
            files = st.file_uploader("PDF or DOCX, single or bulk", type=["pdf", "docx"], accept_multiple_files=True,
                                     key=f"up_{job_id}_{st.session_state.get('up_n', 0)}")
            if files and st.button(f"Screen {len(files)} resume(s)", type="primary"):
                with st.spinner("Parsing and scoring…"):
                    ok, bad = store.add_resumes(db, user, jobmap[job_id], [(f.name, f.getvalue()) for f in files])
                st.session_state.up_n = st.session_state.get("up_n", 0) + 1
                st.session_state.flash = f"{len(ok)} resume(s) screened" + (f" · {len(bad)} rejected: " + "; ".join(f"{n} ({w})" for n, w in bad) if bad else "")
                st.rerun()
        st.write("")
    elif job_id:
        st.info("This job is closed for new applications.")

    stmt = store.app_query(job_id, status, q or None, skill or None, min_score or None)
    rows = db.scalars(stmt).unique().all()
    total = len(rows)
    pages = max(1, -(-total // PAGE))
    pg = min(st.session_state.get("cand_page", 0), pages - 1)
    view = rows[pg * PAGE:(pg + 1) * PAGE]

    sel_key = "cand_sel"
    selected = st.session_state.setdefault(sel_key, set())
    h1, h2 = st.columns([4, 1])
    h1.markdown(f'<span style="color:{ui.MUTED};font-size:.85rem">{total} result(s)</span>', unsafe_allow_html=True)
    if manager and rows:
        h2.download_button("Export CSV", store.export_csv(rows), "candidates.csv", "text/csv", use_container_width=True)

    if manager and selected:
        with st.container(key="card_bulk"):
            st.markdown(f"**{len(selected)} selected** — approve & email:")
            x = st.columns([1, 1, 1, 4])
            for col, (dec, label) in zip(x, [("selected", "Select"), ("on_hold", "Hold"), ("rejected", "Reject")]):
                if col.button(label, key=f"bulk_{dec}"):
                    ok, errs = 0, []
                    for aid in list(selected):
                        a_ = db.get(m.Application, aid)
                        try:
                            store.notify(db, a_, dec, user)
                            ok += 1
                        except ValueError as ex:
                            errs.append(f"{a_.candidate.name or aid}: {ex}")
                    selected.clear()
                    st.session_state.flash = f"{ok} email(s) processed" + (" · " + "; ".join(errs) if errs else "")
                    st.rerun()

    with st.container(key="card_list"):
        if view:
            w = [0.3, 3.2, 0.8, 1.3, 0.7, 2.4, 0.9] if manager else [3.2, 0.8, 1.3, 0.7, 2.4, 0.9]
            names = (["", "Candidate", "Score", "Status", "Exp", "Missing required", ""] if manager
                     else ["Candidate", "Score", "Status", "Exp", "Missing required", ""])
            for col, n in zip(st.columns(w), names):
                col.markdown(f'<div style="color:{ui.MUTED};font-size:.7rem;letter-spacing:.09em;text-transform:uppercase">{n}</div>', unsafe_allow_html=True)
            st.markdown('<hr style="margin:.1rem 0 .5rem 0">', unsafe_allow_html=True)
        if not view:
            ui.empty("No candidates match. Pick a job and upload resumes, or loosen the filters.")
        for i, a in enumerate(view):
            c = a.candidate
            cols = st.columns([0.3, 3.2, 0.8, 1.3, 0.7, 2.4, 0.9] if manager else [3.2, 0.8, 1.3, 0.7, 2.4, 0.9])
            k = 0
            if manager:
                if cols[0].checkbox("sel", key=f"sel_{a.id}", value=a.id in selected, label_visibility="collapsed"):
                    selected.add(a.id)
                else:
                    selected.discard(a.id)
                k = 1
            cols[k].markdown(
                f'<div class="crow">{ui.avatar(c.name or c.original_filename, 38)}<div><div class="nm">{ui.esc(c.name or "(parsing…)")}</div>'
                f'<div class="em">{ui.esc(c.email or ("parse failed" if c.parse_status == "failed" else ""))}'
                f'{"" if job_id else " · " + ui.esc(a.job.title)}</div></div></div>', unsafe_allow_html=True)
            cols[k + 1].markdown(ui.ring(a.score), unsafe_allow_html=True)
            cols[k + 2].markdown(ui.pill(a.status), unsafe_allow_html=True)
            cols[k + 3].markdown(f'<span style="font-size:.85rem">{c.experience_years:g}y</span>', unsafe_allow_html=True)
            cols[k + 4].markdown(ui.chips(a.missing_skills or [], "r", "all required met"), unsafe_allow_html=True)
            if cols[k + 5].button("Open", key=f"open_{a.id}"):
                st.session_state.update(page="Profile", app_id=a.id)
                st.rerun()
            st.markdown('<hr style="margin:.2rem 0 .5rem 0">', unsafe_allow_html=True)

    if pages > 1:
        p1, p2, p3 = st.columns([1, 2, 1])
        if p1.button("← Prev", disabled=pg == 0):
            st.session_state.cand_page = pg - 1
            st.rerun()
        p2.markdown(f'<div style="text-align:center;color:{ui.MUTED}">Page {pg + 1} / {pages}</div>', unsafe_allow_html=True)
        if p3.button("Next →", disabled=pg + 1 >= pages):
            st.session_state.cand_page = pg + 1
            st.rerun()
