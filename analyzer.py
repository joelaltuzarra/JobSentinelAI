from collections import Counter
from llm_manager import get_llm_connector
import re
import unicodedata

SKILL_ALIASES = {
    "react.js": "react",
    "reactjs": "react",
    "node.js": "node",
    "node js": "node",
    "c sharp": "c#",
    "c-sharp": "c#",
    "vue.js": "vue",
    "vuejs": "vue",
    "java/j2ee": "java",
    "golang": "go",
    "amazon web services": "aws",
    "google cloud platform": "gcp",
    "microsoft azure": "azure",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "docker": "docker",
    "sql advanced": "sql",
    "my sql": "sql",
    "mysql": "sql",
    "github copilot": "github", # o "copilot"
    "git / github": "git",
    "github": "git",
    "bitbucket": "git",
    "bitbucket pipelines": "ci/cd",
    "ci/cd (bitbucket pipelines)": "ci/cd",
    ".net core": ".net",
    "dotnetcore": ".net",
    "dotnet": ".net",
    ".net framework": ".net",
    ".net framework 4.x": ".net",
    "asp.net": ".net",
    "asp.net mvc": ".net",
    "asp net mvc": ".net",
    "nodejs": "node",
    "javascript": "js",
    "js": "js",
    "graphql": "graphql",
    "apis rest": "api rest",
    "api rest": "api rest",
    "rest": "api rest",
    "azure devops": "devops",
    "devops": "devops",
    "cicd": "ci/cd",
    "ci cd": "ci/cd",
    "mcp servers": "mcp",
    "oauth2": "oauth",
    "oidc/oauth2": "oauth",
    "jwt": "auth",
    "refresh tokens": "auth"
}


CANONICAL_PATTERNS = [
    (r"(?<!\w)(\.net(\s*core|\s*framework|\s*\d+(\+)?|framework)?|dotnet(core)?|asp\.?net(\s+mvc)?)\b", ".net"),
    (r"\b(c#|c\s*sharp|csharp)\b", "c#"),
    (r"\b(node\.?js|nodejs|node)\b", "node"),
    (r"\b(react\.?js|reactjs|react)\b", "react"),
    (r"\b(next\.?js|nextjs)\b", "next.js"),
    (r"\b(vue\.?js|vuejs|vue)\b", "vue"),
    (r"\b(k8s|kubernetes)\b", "kubernetes"),
    (r"\b(amazon web services|aws)\b", "aws"),
    (r"\b(microsoft azure|azure)\b", "azure"),
    (r"\b(ci\s*/\s*cd|ci\s*cd|cicd)\b", "ci/cd"),
    (r"\b(devops|azure devops)\b", "devops"),
    (r"\b(api|apis)\s*(rest)\b", "api rest"),
    (r"\bgraphql\b", "graphql"),
    (r"\b(sql|mysql|my\s*sql|stored?\s+procedure(s)?)\b", "sql"),
]


def _strip_accents(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))


def _normalize_text(skill: str) -> str:
    clean = _strip_accents(skill.lower()).strip()
    clean = re.sub(r"[\n\r\t]+", " ", clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean


def _split_compound_skill(skill: str) -> list:
    text = _normalize_text(skill)
    candidates = [text]

    inside_parentheses = re.findall(r"\((.*?)\)", text)
    outside_parentheses = re.sub(r"\(.*?\)", " ", text).strip()
    if outside_parentheses:
        candidates.append(outside_parentheses)

    for group in inside_parentheses:
        candidates.extend([part.strip() for part in re.split(r"[,;]", group) if part.strip()])

    expanded = []
    for item in candidates:
        expanded.extend([part.strip() for part in re.split(r"[,;]", item) if part.strip()])

    return expanded


def normalize_skills(skill: str) -> str:
    clean = _normalize_text(skill)

    if clean in SKILL_ALIASES:
        return SKILL_ALIASES[clean]

    clean = re.sub(r'\s+(advanced|basic|intermediate|expert)$', '', clean)
    clean = re.sub(r'^(advanced|basic|intermediate|expert)\s+', '', clean)

    for pattern, canonical in CANONICAL_PATTERNS:
        if re.search(pattern, clean):
            return canonical

    if 'sql' in clean and 'nosql' not in clean:
        return 'sql'

    if 'c#' in clean:
        return 'c#'

    if 'react' in clean and 'native' not in clean:
        return 'react'

    return clean


def explode_and_normalize_skill(skill: str) -> set:
    normalized = set()
    for part in _split_compound_skill(skill):
        canonical = normalize_skills(part)
        if canonical:
            normalized.add(canonical)

    # Casos compuestos frecuentes: "rest/graphql", "rpo/rto", etc.
    base = _normalize_text(skill)
    if "rest/graphql" in base or "rest / graphql" in base:
        normalized.add("api rest")
        normalized.add("graphql")
    if "rpo/rto" in base or "rpo / rto" in base:
        normalized.add("rpo")
        normalized.add("rto")

    return normalized

def calculate_skill_gap(
    cv_text: str,
    jobs: list,
    provider: str = "groq",
    model_name: str | None = None,
    api_key: str | None = None,
):
    llm = get_llm_connector(provider, model_name=model_name, api_key=api_key)

    raw_user_skills = llm.extract_skills_from_cv(cv_text)

    user_skills_set = set()
    for skill in raw_user_skills:
        user_skills_set.update(explode_and_normalize_skill(skill))

    all_required_skills = []

    for job in jobs:
        raw_job_skills = llm.extract_skills_from_job(job.get("description", ""))
        for skill in raw_job_skills:
            all_required_skills.extend(explode_and_normalize_skill(skill))

    skills_counter = Counter(all_required_skills)

    missing_skills = {}
    for skill, count in skills_counter.items():
        if skill not in user_skills_set and skill != "":
            missing_skills[skill] = count

    sorted_missing_skills = sorted(missing_skills.items(), key=lambda x: x[1], reverse=True)

    return {
        "user_skills": list(user_skills_set),
        "missing_skills_ranking": sorted_missing_skills
    } 