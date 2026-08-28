import os
import sys
from pathlib import Path

def ensure_project_dirs():
    """
    Creates the project directory structure for PROJ-274.
    This function is idempotent.
    """
    # Determine project root relative to the code directory
    # The project structure is:
    # projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/
    #   code/
    #   data/
    #   tests/
    #   specs/
    #   state/
    #   config/
    #   contracts/
    
    # We assume the script is run from the project root or code directory.
    # We will navigate up to find the project root.
    
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    project_name = "PROJ-274-evaluating-the-impact-of-llm-generated-c"
    
    # If we are already in the project root, use it.
    # If the project is nested (e.g., projects/PROJ-274), we might need to adjust.
    # Based on the task description, the root is `projects/PROJ-274...`
    # Let's assume the directory containing `code/` IS the project root.
    
    dirs_to_create = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "data/logs",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs",
        "state",
        "config",
        "contracts",
        "figures"
    ]
    
    created_dirs = []
    for d in dirs_to_create:
        full_path = project_root / d
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
        
    return created_dirs, project_root