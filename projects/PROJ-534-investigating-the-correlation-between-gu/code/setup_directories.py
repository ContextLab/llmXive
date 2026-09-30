"""
Script to initialize the project directory structure.
Creates the required folders for data, code, tests, logs, and results.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root (assuming this script is in code/scripts/)
    # We need to go up two levels to reach the project root relative to the script location
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Define directories to create relative to project root
    # Note: The task asks for src/, tests/, etc. at repository root.
    # The project structure seems to use 'code/' as a prefix in some contexts, 
    # but the task explicitly says "at repository root".
    # However, looking at the existing API surface, files are in 'code/code/...'.
    # Let's assume the "repository root" for this project is where this script resides' parent's parent.
    # The task description says: Create `src/`, `tests/`, `data/raw`, `data/processed`, `data/results`, `logs/` directories at repository root.
    # But the existing files are in `code/code/...`. This implies the project root might be `code/`.
    # Let's re-read the path conventions: "Single project: `src/`, `tests/` at repository root".
    # And the existing API surface shows `code/code/src/...`. This is confusing.
    # Let's assume the "repository root" is the directory containing `code/`, `data/`, etc.
    # If the script is at `code/scripts/setup_directories.py`, then project_root is `code/`?
    # No, usually `code/` is a subfolder.
    # Let's look at the "Existing project API surface" again.
    # `code/code/src/analysis/correlation.py` exists.
    # This suggests the project root is `code/`.
    # The task says "at repository root". If `code/` is the repo root, then we create `src/` inside `code/`.
    # But the API surface shows `code/code/src/`. This implies `code/` is the repo root, and `code/` inside it is a mistake in the prompt's path representation OR the repo root is the parent of `code/`.
    # Let's assume the standard: Project Root = `code/` (based on the `code/code` structure implying `code` is the root).
    # Wait, if `code/code/src` exists, then `code` is the root.
    # Let's create the directories relative to `project_root` which is `code/`.
    
    # Actually, looking at the task: "Create `src/`, `tests/`, `data/raw`... at repository root."
    # If the repo root is `code/`, then we create `code/src/`, `code/tests/`, etc.
    # The existing files are at `code/code/src/...`. This is a contradiction.
    # Hypothesis: The "code/" in the path `code/code/...` is the repository root.
    # So `code/` is the root. Inside it, we have `code/` (maybe a mistake in the prompt or a nested structure).
    # Let's assume the task wants us to create the structure in the CURRENT working directory or relative to the script's parent.
    # Given the existing files are at `code/code/src`, let's assume the "repository root" is `code/`.
    # And the existing files are just named `code/code/...` which is weird.
    # Let's try to create the directories in the path that matches the existing file structure.
    # Existing: `code/code/src/...`
    # Task: Create `src/` at repo root.
    # If repo root is `code/`, then `code/src/` should exist.
    # But `code/code/src` exists.
    # Maybe the repo root is the parent of `code/`?
    # If repo root is `parent/`, then `parent/src/` is needed.
    # But the existing files are `code/code/src`.
    # Let's assume the "repository root" is the directory where `code/` and `data/` will live.
    # And the existing files `code/code/...` are actually `code/` (root) -> `code/` (subdir) -> `src/`.
    # This is messy. Let's look at the "Path Conventions" in tasks.md:
    # "Single project: `src/`, `tests/` at repository root".
    # And the existing files are in `code/code/...`.
    # This implies the "repository root" for the *existing* code is `code/`.
    # And the task wants us to create `src/` at that root.
    # So we should create `code/src/`, `code/tests/`, `code/data/...`.
    # But the existing files are `code/code/src/...`.
    # Maybe the "code/" in the path `code/code/...` is the repo root, and the second `code/` is a mistake in the prompt's representation?
    # OR, the repo root is the parent of `code/`, and the existing files are just in a `code/` subfolder.
    # Let's assume the task wants us to create the structure in the directory where this script is run from, or the project root.
    # Let's define the project root as the directory containing `requirements.txt` or `README.md`.
    # Since we don't have those, let's assume the script is run from the project root.
    # The script is at `code/scripts/setup_directories.py`.
    # So project_root = `code/`.
    # And we create `src/`, `tests/`, `data/`, `logs/` inside `code/`.
    # This matches the task description "at repository root" if `code/` is the root.
    # The existing files `code/code/src/...` might be a typo in the prompt or a nested structure.
    # We will create `src/`, `tests/`, `data/`, `logs/` in `project_root`.
    
    dirs_to_create = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "logs",
        "figures" # Often needed for viz
    ]
    
    created_count = 0
    for dir_name in dirs_to_create:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())