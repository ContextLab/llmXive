"""
fix_tasks_schema.py
-------------------
This script updates the generated synthetic ``tasks.json`` and ``skills.json`` files
so that they conform to the JSON schemas located in ``contracts/``.  The original
data generation step creates fields with legacy names (e.g. ``ground_truth_path``,
``function_code``, ``embedding_vector``) that do not match the contract
definitions.  The script performs a deterministic, in‑place transformation:

* **Tasks**
  - If ``ground_truth_skills`` is missing, copy the list from
    ``ground_truth_path``.
  - Ensure the required keys ``task_id``, ``description``, ``complexity``,
    ``ground_truth_skills`` and ``solution_path`` exist.  The generation step
    already creates all of these except ``ground_truth_skills``.

* **Skills**
  - Rename ``function_code`` → ``code``.
  - Rename ``embedding_vector`` → ``embedding``.
  - Add a ``name`` field derived from the function name inside ``code``.
    If the function definition cannot be parsed, fall back to the ``skill_id``.
  - Ensure ``last_used`` exists; if absent, populate it with the current UTC
    timestamp in ISO‑8601 format.

The script uses ``llmxive_toolkit.paths`` to resolve the data locations and
writes the corrected JSON back to the same files.  It is safe to run multiple
times – missing fields will be added only once and existing correct fields are
left unchanged.

The quick‑start guide runs this script after data generation, and the test
suite imports the module to guarantee the data are schema‑compliant before
validation.
"""

import json
import os
import re
from datetime import datetime, timezone

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

TASKS_PATH = paths.data("raw", "tasks.json")
SKILLS_PATH = paths.data("raw", "skills.json")

def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fix_tasks(tasks_data):
    """
    Ensure each task dictionary contains ``ground_truth_skills``.
    If the legacy field ``ground_truth_path`` exists, copy its value.
    """
    tasks = tasks_data["tasks"] if isinstance(tasks_data, dict) and "tasks" in tasks_data else tasks_data
    for task in tasks:
        if "ground_truth_skills" not in task:
            if "ground_truth_path" in task:
                task["ground_truth_skills"] = task["ground_truth_path"]
                log.info(f"Added missing ground_truth_skills to task {task.get('task_id')}")
            else:
                log.error(f"Task {task.get('task_id')} missing both ground_truth_skills and ground_truth_path")
    # Preserve original wrapper if present
    return {"tasks": tasks} if isinstance(tasks_data, dict) and "tasks" in tasks_data else tasks

def extract_function_name(code_str: str) -> str:
    """
    Very small parser that extracts the first function name after a ``def`` keyword.
    Falls back to ``None`` if parsing fails.
    """
    match = re.search(r"def\\s+([a-zA-Z_][a-zA-Z0-9_]*)\\s*\\(", code_str)
    return match.group(1) if match else None

def fix_skills(skills_data):
    """
    Transform each skill dictionary:
    - Rename legacy fields.
    - Add ``name`` derived from the function definition.
    - Ensure ``last_used`` timestamp exists.
    """
    skills = skills_data["skills"] if isinstance(skills_data, dict) and "skills" in skills_data else skills_data
    for skill in skills:
        # Rename ``function_code`` → ``code``
        if "function_code" in skill and "code" not in skill:
            skill["code"] = skill.pop("function_code")
            log.info(f"Renamed function_code to code for skill {skill.get('skill_id')}")

        # Rename ``embedding_vector`` → ``embedding``
        if "embedding_vector" in skill and "embedding" not in skill:
            skill["embedding"] = skill.pop("embedding_vector")
            log.info(f"Renamed embedding_vector to embedding for skill {skill.get('skill_id')}")

        # Add ``name`` if missing
        if "name" not in skill:
            code = skill.get("code", "")
            derived_name = extract_function_name(code)
            skill["name"] = derived_name if derived_name else skill.get("skill_id", "unnamed_skill")
            log.info(f"Set name for skill {skill.get('skill_id')} to '{skill['name']}'")

        # Ensure ``last_used`` exists
        if "last_used" not in skill:
            skill["last_used"] = datetime.now(timezone.utc).isoformat()
            log.info(f"Added missing last_used for skill {skill.get('skill_id')}")

    return {"skills": skills} if isinstance(skills_data, dict) and "skills" in skills_data else skills

def main():
    # Fix tasks
    if not os.path.exists(TASKS_PATH):
        log.error(f"Tasks file not found at {TASKS_PATH}")
        return
    tasks_raw = load_json(TASKS_PATH)
    fixed_tasks = fix_tasks(tasks_raw)
    save_json(fixed_tasks, TASKS_PATH)
    log.info(f"Tasks file rewritten to conform to schema at {TASKS_PATH}")

    # Fix skills
    if not os.path.exists(SKILLS_PATH):
        log.error(f"Skills file not found at {SKILLS_PATH}")
        return
    skills_raw = load_json(SKILLS_PATH)
    fixed_skills = fix_skills(skills_raw)
    save_json(fixed_skills, SKILLS_PATH)
    log.info(f"Skills file rewritten to conform to schema at {SKILLS_PATH}")

if __name__ == "__main__":
    main()
