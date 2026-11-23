"""
Script to enforce the project directory structure as per plan.md.
Creates: code/, data/, state/, tests/, docs/
"""
import os
from pathlib import Path

ROOT_DIRS = [
    "code",
    "data",
    "state",
    "tests",
    "docs"
]

def main():
    base = Path.cwd()
    created = []
    for d in ROOT_DIRS:
        target = base / d
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created.append(str(target))
            print(f"Created directory: {target}")
        else:
            print(f"Directory exists: {target}")
    
    # Ensure .gitkeep files exist to preserve empty directories in git
    for d in ROOT_DIRS:
        target = base / d / ".gitkeep"
        if not target.exists():
            target.touch()
            print(f"Created .gitkeep in: {target.parent}")

    if not created:
        print("All required directories already exist.")
    else:
        print(f"Project structure initialized successfully.")

if __name__ == "__main__":
    main()
