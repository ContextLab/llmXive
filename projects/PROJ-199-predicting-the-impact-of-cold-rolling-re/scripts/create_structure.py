"""
Script to create the top-level directory structure for the project.
Ensures code/, data/, tests/, and docs/ directories exist.
"""
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    directories = [
        "code",
        "data",
        "tests",
        "docs"
    ]

    created = []
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    if created:
        print(f"\nSuccessfully created {len(created)} directory(ies).")
    else:
        print("\nAll directories already existed.")

if __name__ == "__main__":
    main()