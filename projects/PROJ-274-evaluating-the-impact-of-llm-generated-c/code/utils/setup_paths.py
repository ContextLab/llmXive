"""
Path setup utilities for the project.
Ensures standard directory structures exist.
"""
import os
import sys
from pathlib import Path

def ensure_project_dirs():
    """
    Ensure all required project directories exist.
    Creates directories relative to the project root.
    """
    # Determine project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define required directories
    dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "reports",
        project_root / "data" / "logs",
        project_root / "code" / "logs",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        project_root / "specs",
        project_root / "config",
        project_root / "state",
        project_root / "contracts",
        project_root / "data" / "processed" / "docs",
    ]

    created = []
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
    
    if created:
        print(f"Created directories: {created}")
    else:
        print("All required directories already exist.")
    
    return True

if __name__ == "__main__":
    ensure_project_dirs()
