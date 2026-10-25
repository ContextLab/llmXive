"""
Script to clean up the generated tasks.json so that it conforms to the
task.schema.yaml contract. The original synthetic generator includes a
number of auxiliary fields (e.g., embedding_vector, edge_case, id,
num_steps) that are not permitted by the schema. This script retains only
the fields required by the schema and renames ``ground_truth_path`` to
``ground_truth_skills`` when necessary.
"""

import json
import os
from pathlib import Path

# Paths (relative to project root)
TASKS_PATH = Path("data") / "raw" / "tasks.json"

def load_tasks(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "tasks" in data:
        return data["tasks"]
    return data

def save_tasks(tasks, path: Path):
    # Preserve the original outer structure if it existed
    with open(path, "r", encoding="utf-8") as f:
        original = json.load(f)
    if isinstance(original, dict) and "tasks" in original:
        original["tasks"] = tasks
        out_data = original
    else:
        out_data = tasks
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, sort_keys=False)

def clean_task(task):
    """
    Return a new dict containing only the fields allowed by the schema:
    - task_id
    - description
    - ground_truth_skills (list of skill IDs)
    - complexity (derived from number of steps if not present)
    """
    cleaned = {
        "task_id": task.get("task_id"),
        "description": task.get("description")
    }

    # Prefer the explicit ``ground_truth_skills`` field; otherwise fall back
    # to ``ground_truth_path`` which is what the generator currently emits.
    gt = task.get("ground_truth_skills")
    if gt is None:
        gt = task.get("ground_truth_path", [])
    cleaned["ground_truth_skills"] = gt

    # Derive a simple complexity metric – number of steps in the ground‑truth path.
    if "complexity" in task:
        cleaned["complexity"] = task["complexity"]
    else:
        cleaned["complexity"] = len(gt)

    return cleaned

def main():
    if not TASKS_PATH.is_file():
        raise FileNotFoundError(f"Tasks file not found at {TASKS_PATH}")

    tasks = load_tasks(TASKS_PATH)
    cleaned_tasks = [clean_task(t) for t in tasks]

    save_tasks(cleaned_tasks, TASKS_PATH)
    print(f"Cleaned {len(cleaned_tasks)} tasks and wrote back to {TASKS_PATH}")

if __name__ == "__main__":
    main()
