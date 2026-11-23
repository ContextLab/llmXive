import json
import os
import re
from datetime import datetime, timezone
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def extract_function_name(code_str: str) -> str:
    if not code_str:
        return "unknown_func"
    match = re.search(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', code_str)
    return match.group(1) if match else "unknown_func"

def fix_tasks(tasks_data):
    """
    Ensure each task conforms to contracts/task.schema.yaml.
    Specifically ensures 'ground_truth_skills' and 'solution_path' exist.
    """
    tasks_list = tasks_data['tasks'] if isinstance(tasks_data, dict) and 'tasks' in tasks_data else tasks_data
    if not isinstance(tasks_list, list):
        return tasks_data

    for task in tasks_list:
        # 1. Ensure ground_truth_skills exists
        if 'ground_truth_skills' not in task:
            if 'ground_truth_path' in task:
                task['ground_truth_skills'] = task['ground_truth_path']
            else:
                # Fallback for synthetic data: create a dummy if absolutely missing
                task['ground_truth_skills'] = []

        # 2. Ensure solution_path exists (Required by schema)
        if 'solution_path' not in task:
            # In synthetic data, if solution_path is missing, we use ground_truth_skills as the path
            task['solution_path'] = task.get('ground_truth_skills', [])

    return tasks_data

def fix_skills(skills_data):
    """
    Ensure each skill conforms to contracts/skill.schema.yaml.
    Specifically renames 'embedding_vector' -> 'embedding' and ensures required fields.
    """
    skills_list = skills_data['skills'] if isinstance(skills_data, dict) and 'skills' in skills_data else skills_data
    if not isinstance(skills_list, list):
        return skills_data

    for skill in skills_list:
        # 1. Rename embedding_vector to embedding (CRITICAL for schema)
        if 'embedding_vector' in skill:
            skill['embedding'] = skill.pop('embedding_vector')
        
        # 2. Ensure 'name' exists
        if 'name' not in skill:
            skill['name'] = extract_function_name(skill.get('code', ''))

        # 3. Ensure 'usage_count' exists
        if 'usage_count' not in skill:
            skill['usage_count'] = 0

        # 4. Ensure 'last_used' exists
        if 'last_used' not in skill:
            skill['last_used'] = datetime.now(timezone.utc).isoformat()

    return skills_data

def main():
    tasks_path = paths.data("raw", "tasks.json")
    skills_path = paths.data("raw", "skills.json")

    # Fix Tasks
    tasks_data = load_json(tasks_path)
    if tasks_data:
        log.info(f"Fixing tasks at {tasks_path}")
        fixed_tasks = fix_tasks(tasks_data)
        save_json(fixed_tasks, tasks_path)
    else:
        log.error(f"Tasks file not found at {tasks_path}")

    # Fix Skills
    skills_data = load_json(skills_path)
    if skills_data:
        log.info(f"Fixing skills at {skills_path}")
        fixed_skills = fix_skills(skills_data)
        save_json(fixed_skills, skills_path)
    else:
        log.error(f"Skills file not found at {skills_path}")

if __name__ == "__main__":
    main()
