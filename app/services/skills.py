"""Skills dictionary: canonical name -> (category, aliases). Matching is case-insensitive
and boundary-aware so "java" does not match "javascript" and "c" is excluded on purpose."""
import re

SKILLS: dict[str, tuple[str, list[str]]] = {
    "Python": ("language", ["python", "python3"]),
    "Java": ("language", ["java"]),
    "JavaScript": ("language", ["javascript", "js", "ecmascript", "es6"]),
    "TypeScript": ("language", ["typescript"]),
    "C++": ("language", ["c++", "cpp"]),
    "C#": ("language", ["c#", "csharp"]),
    "Go": ("language", ["golang", "go lang"]),
    "Rust": ("language", ["rust"]),
    "PHP": ("language", ["php"]),
    "Ruby": ("language", ["ruby"]),
    "Kotlin": ("language", ["kotlin"]),
    "Swift": ("language", ["swift"]),
    "R": ("language", ["r programming", "rstudio"]),
    "SQL": ("database", ["sql", "t-sql", "pl/sql"]),
    "PostgreSQL": ("database", ["postgresql", "postgres"]),
    "MySQL": ("database", ["mysql"]),
    "MongoDB": ("database", ["mongodb", "mongo"]),
    "Redis": ("database", ["redis"]),
    "SQLite": ("database", ["sqlite"]),
    "Elasticsearch": ("database", ["elasticsearch", "elastic search"]),
    "React": ("frontend", ["react", "reactjs", "react.js"]),
    "Angular": ("frontend", ["angular", "angularjs"]),
    "Vue": ("frontend", ["vue", "vuejs", "vue.js"]),
    "HTML": ("frontend", ["html", "html5"]),
    "CSS": ("frontend", ["css", "css3"]),
    "Tailwind CSS": ("frontend", ["tailwind", "tailwindcss", "tailwind css"]),
    "Node.js": ("backend", ["node.js", "nodejs", "node js"]),
    "Express": ("backend", ["express.js", "expressjs"]),
    "FastAPI": ("backend", ["fastapi"]),
    "Django": ("backend", ["django"]),
    "Flask": ("backend", ["flask"]),
    "Spring Boot": ("backend", ["spring boot", "springboot", "spring framework"]),
    ".NET": ("backend", [".net", "dotnet", "asp.net"]),
    "REST API": ("backend", ["rest api", "restful", "rest apis", "restful api"]),
    "GraphQL": ("backend", ["graphql"]),
    "Docker": ("devops", ["docker", "docker compose", "docker-compose"]),
    "Kubernetes": ("devops", ["kubernetes", "k8s"]),
    "AWS": ("cloud", ["aws", "amazon web services"]),
    "Azure": ("cloud", ["azure"]),
    "GCP": ("cloud", ["gcp", "google cloud"]),
    "Terraform": ("devops", ["terraform"]),
    "CI/CD": ("devops", ["ci/cd", "cicd", "github actions", "jenkins", "gitlab ci"]),
    "Git": ("devops", ["git", "github", "gitlab", "bitbucket"]),
    "Linux": ("devops", ["linux", "ubuntu", "bash scripting", "shell scripting"]),
    "Celery": ("backend", ["celery"]),
    "RabbitMQ": ("backend", ["rabbitmq"]),
    "Kafka": ("backend", ["kafka"]),
    "Machine Learning": ("data", ["machine learning", "ml"]),
    "Deep Learning": ("data", ["deep learning", "neural networks"]),
    "NLP": ("data", ["nlp", "natural language processing", "spacy"]),
    "TensorFlow": ("data", ["tensorflow"]),
    "PyTorch": ("data", ["pytorch"]),
    "scikit-learn": ("data", ["scikit-learn", "sklearn", "scikit learn"]),
    "Pandas": ("data", ["pandas"]),
    "NumPy": ("data", ["numpy"]),
    "Data Analysis": ("data", ["data analysis", "data analytics"]),
    "Power BI": ("data", ["power bi", "powerbi"]),
    "Tableau": ("data", ["tableau"]),
    "Excel": ("data", ["excel", "ms excel"]),
    "Selenium": ("testing", ["selenium"]),
    "Pytest": ("testing", ["pytest"]),
    "Unit Testing": ("testing", ["unit testing", "unit tests", "tdd", "jest", "junit"]),
    "Agile": ("process", ["agile", "scrum", "kanban"]),
    "Communication": ("soft", ["communication skills", "communication"]),
    "Leadership": ("soft", ["leadership", "team lead"]),
    "Project Management": ("soft", ["project management", "pmp"]),
}


def _pattern(alias: str) -> re.Pattern:
    # custom boundaries: not preceded/followed by an alphanumeric (or +/# for non-symbol aliases)
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(alias) + r"(?![A-Za-z0-9]|\+\+|#)", re.I)


AMBIGUOUS = {"Go", "R"}  # common English/letter tokens: only explicit aliases count
_PATTERNS = [(canon, _pattern(a)) for canon, (_, aliases) in SKILLS.items()
             for a in (aliases if canon in AMBIGUOUS else aliases + [canon.lower()])]
_LOOKUP = {canon.lower(): canon for canon in SKILLS}
for canon, (_, aliases) in SKILLS.items():
    for a in aliases:
        _LOOKUP[a.lower()] = canon


def canonical(name: str) -> str:
    """Map a free-text skill (from a JD form) to its canonical dictionary name if known."""
    n = name.strip()
    return _LOOKUP.get(n.lower(), n)


def category(name: str) -> str:
    return SKILLS.get(name, ("", []))[0]


def extract_skills(text: str) -> list[str]:
    found = []
    for canon, pat in _PATTERNS:
        if canon not in found and pat.search(text):
            found.append(canon)
    return found
