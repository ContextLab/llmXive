import os
import sys
from pathlib import Path

def create_project_structure(project_path):
    """Creates the project directory structure."""

    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "code/tests",
        "results",
        "artifacts",
        "specs/001-reward-fidelity-error-recovery/contracts",
    ]

    for directory in directories:
        path = Path(project_path) / directory
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")

if __name__ == "__main__":
    project_path = "projects/PROJ-1052-llmxive-follow-up-extending-long-horizon"
    create_project_structure(project_path)