"""Generates dummy resumes (fake people, example.com emails) as PDF/DOCX for testing."""
import random
from pathlib import Path

FIRST = ["Aarav", "Priya", "Rohan", "Sneha", "Vikram", "Ananya", "Karthik", "Meera", "Arjun", "Divya",
         "Rahul", "Neha", "Sanjay", "Pooja", "Amit", "Kavya", "Nikhil", "Ishita", "Varun", "Tara"]
LAST = ["Sharma", "Iyer", "Patel", "Reddy", "Nair", "Gupta", "Menon", "Singh", "Das", "Kulkarni"]
POOLS = {
    "backend": ["Python", "FastAPI", "PostgreSQL", "Docker", "REST API", "Redis", "Celery", "Git", "SQL", "Linux"],
    "frontend": ["JavaScript", "React", "HTML", "CSS", "Tailwind CSS", "TypeScript", "Git", "Node.js"],
    "data": ["Python", "Pandas", "NumPy", "scikit-learn", "Machine Learning", "SQL", "Tableau", "Excel"],
    "other": ["Java", "Spring Boot", "MySQL", "Agile", "Excel", "Communication"],
}
DEGREES = ["B.Tech in Computer Science", "M.Tech in Software Engineering", "B.Sc in Mathematics",
           "MCA", "Diploma in Computer Engineering", "PhD in Computer Science"]


def make_text(i: int, rng: random.Random) -> tuple[str, str]:
    name = f"{FIRST[i % len(FIRST)]} {LAST[(i // 2) % len(LAST)]}"
    email = f"{name.lower().replace(' ', '.')}.{i}@example.com"
    kind = rng.choice(list(POOLS))
    skills = rng.sample(POOLS[kind], k=rng.randint(3, len(POOLS[kind])))
    years = rng.randint(0, 9)
    start = 2025 - years
    text = (f"{name}\n{email}\n+91 98{rng.randint(10000000, 99999999)}\n\nSummary\n"
            f"{kind.title()} engineer with {years} years of experience building applications.\n\n"
            f"Skills\n{', '.join(skills)}\n\nExperience\nSoftware Engineer, Example Corp  {start} - Present\n"
            f"Built and maintained services using {', '.join(skills[:3])}.\n\n"
            f"Education\n{rng.choice(DEGREES)}, Example University, 2018\n")
    return email, text


def write_pdf(path: Path, text: str):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(path), pagesize=A4)
    y = 800
    for line in text.splitlines():
        c.drawString(50, y, line)
        y -= 16
    c.save()


def write_docx(path: Path, text: str):
    import docx
    d = docx.Document()
    for line in text.splitlines():
        d.add_paragraph(line)
    d.save(str(path))


def generate(out_dir: Path, n: int = 55, seed: int = 7) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    paths = []
    for i in range(n):
        _, text = make_text(i, rng)
        p = out_dir / f"resume_{i:03d}.{'pdf' if i % 3 else 'docx'}"
        (write_pdf if p.suffix == ".pdf" else write_docx)(p, text)
        paths.append(p)
    return paths


if __name__ == "__main__":
    import sys
    dest = Path(sys.argv[1] if len(sys.argv) > 1 else "sample_resumes")
    print(f"Wrote {len(generate(dest))} dummy resumes to {dest}")
