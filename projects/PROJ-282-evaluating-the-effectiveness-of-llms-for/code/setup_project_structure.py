import os
import sys
from pathlib import Path


def create_structure():
    """
    Creates the required directory hierarchy for the project.
    Ensures compliance with T001 requirements.
    """
    project_root = Path(__file__).parent.parent
    directories = [
        "src",
        "src/data",
        "src/services",
        "src/models",
        "src/utils",
        "src/analysis",
        "tests",
        "tests/unit",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "data/human_review",
        "state",
        "state/projects",
        "contracts",
        "figures",
        "specs"
    ]

    created = []
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
        else:
            created.append(f"{dir_path} (exists)")

    print(f"Created/Verified {len(created)} directories in {project_root}")
    return created


if __name__ == "__main__":
    create_structure()
