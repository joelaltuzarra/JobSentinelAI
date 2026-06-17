from collections import Counter
from llm_manager import get_llm_connector
import re

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
    "ci/cd (bitbucket pipelines)": "ci/cd"
}

def normalize_skills(skill: str) -> str:
    clean = skill.lower().strip()

    if clean in SKILL_ALIASES:
        return SKILL_ALIASES[clean]
    
    clean = re.sub(r'\s+(advanced|basic|intermediate|expert)$', '', clean)
    clean = re.sub(r'^(advanced|basic|intermediate|expert)\s+', '', clean)
    
    if 'sql' in clean and 'nosql' not in clean:
        return 'sql'
    
    if 'c#' in clean:
        return 'c#'
    
    if 'react' in clean and 'native' not in clean:
        return 'react'

    return clean

def calculate_skill_gap(cv_text: str, jobs: list, provider: str = "gemini"):
    llm = get_llm_connector(provider)

    raw_user_skills = llm.extract_skills_from_cv(cv_text)

    user_skills_set = set(normalize_skills(s) for s in raw_user_skills)

    all_required_skills = []

    for job in jobs:
        raw_job_skills = llm.extract_skills_from_job(job.get("description", ""))
        normalized_job_skills = [normalize_skills(s) for s in raw_job_skills]
        all_required_skills.extend(normalized_job_skills)

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