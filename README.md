# Resume Screening (Streamlit)

Upload resumes (PDF/DOCX) → parse → score 0–100 against a job → HR reviews a ranked list → **Approve & notify** emails the candidate. Roles: Admin, HR Manager, Recruiter.

**Scoring:** Required skills 45 · Preferred 10 · Experience 20 · Education 10 · Semantic similarity 15. Score ≥ job threshold → Shortlisted. Name, gender, age, photo, religion and address are never used.
**Rule:** nothing is emailed until an HR Manager/Admin confirms; recruiters can only recommend.

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The first visit shows a one-time form to create the admin account (or set `ADMIN_EMAIL` / `ADMIN_PASSWORD`). Data is stored in a local SQLite file.
Tests: `pip install pytest reportlab && python -m pytest -q` (includes a 52-resume bulk run on dummy resumes).



## Layout

```
streamlit_app.py   entry, login, sidebar navigation
ui.py              theme (CSS) and HTML helpers
views/             dashboard, jobs, candidates, profile, emails, admin
app/               models, scoring, parser, skills dictionary, email, data operations
tests/             pytest suite + dummy resume generator
```

Parsing is rule-based (no OCR for scanned PDFs); unusual layouts can mis-detect a name or experience figure.
