"""
Utility to ensure all required project directories exist before logging or file I/O.
This resolves the FileNotFoundError issues seen in the execution logs.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to this file (assuming code/utils/setup_paths.py)
# Project structure:
# PROJ-274...
#   code/
#     utils/
#       setup_paths.py
#   data/
#     raw/
#     processed/
#     reports/
#     logs/
#   state/
#   specs/

def ensure_project_dirs():
    """Creates all necessary directories for the project if they don't exist."""
    # Determine the project root: parent of 'code'
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    dirs_to_create = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "reports",
        project_root / "data" / "logs",
        project_root / "state",
        project_root / "specs" / "001-evaluating-the-impact-of-llm-generated-c",
        project_root / "config",
    ]

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return project_root

if __name__ == "__main__":
    root = ensure_project_dirs()
    print(f"Ensured project directories under: {root}")