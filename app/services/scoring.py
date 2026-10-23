"""Score (0-100) = required 45 + preferred 10 + experience 20 + education 10 + semantic 15.

Only skills, experience, education and text similarity are used. Name, gender, age, photo,
religion and address are never inputs."""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .parser import LEVEL_RANK
from .skills import canonical

W_REQ, W_PREF, W_EXP, W_EDU, W_SEM = 45, 10, 20, 10, 15
SEM_FULL_AT = 0.35  # cosine similarity treated as a "full" semantic match (TF-IDF cosines are low)


def semantic_similarity(jd_text: str, resume_text: str) -> float:
    if not jd_text.strip() or not resume_text.strip():
        return 0.0
    try:
        m = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True).fit_transform(
            [jd_text, resume_text])
        return float(cosine_similarity(m[0], m[1])[0][0])
    except ValueError:  # empty vocabulary
        return 0.0


def score_candidate(job, candidate_skills: list[str], experience_years: float, education_level: str,
                    resume_text: str) -> dict:
    have = {canonical(s).lower() for s in candidate_skills}
    req = [canonical(s) for s in (job.required_skills or [])]
    pref = [canonical(s) for s in (job.preferred_skills or [])]
    req_hit = [s for s in req if s.lower() in have]
    pref_hit = [s for s in pref if s.lower() in have]

    req_pts = W_REQ * (len(req_hit) / len(req)) if req else W_REQ
    pref_pts = W_PREF * (len(pref_hit) / len(pref)) if pref else W_PREF

    need = job.min_experience_years or 0
    exp_pts = W_EXP if need <= 0 else W_EXP * min(experience_years / need, 1.0)

    need_edu = LEVEL_RANK.get((job.required_education or "").lower(), 0)
    got_edu = LEVEL_RANK.get((education_level or "").lower(), 0)
    if need_edu == 0:
        edu_pts = W_EDU
    elif got_edu >= need_edu:
        edu_pts = W_EDU
    elif got_edu == need_edu - 1 and got_edu > 0:
        edu_pts = W_EDU / 2
    else:
        edu_pts = 0.0

    jd_text = " ".join([job.title or "", job.description or "", " ".join(req), " ".join(pref)])
    sim = semantic_similarity(jd_text, resume_text)
    sem_pts = W_SEM * min(sim / SEM_FULL_AT, 1.0)

    total = round(req_pts + pref_pts + exp_pts + edu_pts + sem_pts, 1)
    return {
        "score": total,
        "matched_skills": req_hit + pref_hit,
        "missing_skills": [s for s in req if s not in req_hit],
        "missing_preferred": [s for s in pref if s not in pref_hit],
        "breakdown": {
            "required_skills": {"points": round(req_pts, 1), "max": W_REQ, "matched": len(req_hit), "total": len(req)},
            "preferred_skills": {"points": round(pref_pts, 1), "max": W_PREF, "matched": len(pref_hit), "total": len(pref)},
            "experience": {"points": round(exp_pts, 1), "max": W_EXP, "have": experience_years, "need": need},
            "education": {"points": round(edu_pts, 1), "max": W_EDU, "have": education_level or "unknown",
                          "need": job.required_education or "none"},
            "semantic": {"points": round(sem_pts, 1), "max": W_SEM, "similarity": round(sim, 3)},
        },
    }
