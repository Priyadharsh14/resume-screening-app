from types import SimpleNamespace

import pytest

from app.services.parser import parse_text
from app.services.scoring import score_candidate
from app.services.skills import extract_skills


def test_skill_boundaries():
    assert extract_skills("I know JavaScript and C++") == ["JavaScript", "C++"]
    assert "Java" not in extract_skills("javascript only")
    assert "Go" not in extract_skills("I will go home")


def test_parse_fields():
    p = parse_text("JOHN SMITH\njohn@x.io\n+1 (415) 555-2671\n7 years of experience in Python\nM.Sc Data Science\n")
    assert (p.name, p.email, p.experience_years, p.education_level) == ("John Smith", "john@x.io", 7, "master")
    assert "Python" in p.skills and p.phone.startswith("+1")


def test_experience_from_date_ranges_merges_overlap():
    p = parse_text("Dev\nA  2015 - 2019\nB  2018 - 2020\n")
    assert p.experience_years == 5


def job(**kw):
    d = dict(title="Dev", description="python developer", required_skills=["Python", "SQL"], preferred_skills=["Docker"],
             min_experience_years=4, required_education="bachelor")
    return SimpleNamespace(**{**d, **kw})


def test_score_weights():
    full = score_candidate(job(), ["Python", "SQL", "Docker"], 5, "master", "python developer sql docker")
    assert full["score"] > 90
    assert full["breakdown"]["required_skills"]["points"] == 45 and full["breakdown"]["experience"]["points"] == 20
    half = score_candidate(job(), ["Python"], 2, "", "")
    b = half["breakdown"]
    assert b["required_skills"]["points"] == 22.5 and b["preferred_skills"]["points"] == 0
    assert b["experience"]["points"] == 10 and b["education"]["points"] == 0 and half["missing_skills"] == ["SQL"]


def test_empty_requirements_dont_divide_by_zero():
    r = score_candidate(job(required_skills=[], preferred_skills=[], min_experience_years=0, required_education=""), [], 0, "", "")
    assert r["score"] == pytest.approx(85, abs=0.1)
