"""
Utility script to ensure that every task in `data/raw/tasks.json` contains the
required `ground_truth_skills` field.  The original data generator populates
`ground_truth_path`; the contract schema, however, expects an explicit
`ground_truth_skills` list.  This script copies the path list to the
`ground_truth_skills` field when it is missing.
"""

import json
import os
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main():
    tasks_path = paths.data("raw", "tasks.json")
    if not os.path.exists(tasks_path):
        log.error(f"Tasks file not found at {tasks_path}")
        raise FileNotFoundError(tasks_path)

    with open(tasks_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # The file may be a list or a dict with a 'tasks' key
    if isinstance(data, dict) and "tasks" in data:
        tasks = data["tasks"]
    else:
        tasks = data

    modified = False
    for task in tasks:
        if "ground_truth_skills" not in task:
            gt_path = task.get("ground_truth_path")
            if isinstance(gt_path, list):
                task["ground_truth_skills"] = gt_path
                modified = True
            else:
                task["ground_truth_skills"] = []
                modified = True

    if modified:
        # Preserve original container type
        if isinstance(data, dict) and "tasks" in data:
            data["tasks"] = tasks
        else:
            data = tasks

        with open(tasks_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        log.info(f"Updated tasks.json with missing 'ground_truth_skills' fields.")
    else:
        log.info("No modifications necessary; all tasks already contain 'ground_truth_skills'.")

if __name__ == "__main__":
    main()
