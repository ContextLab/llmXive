"""
Script to set up the project structure.
"""
import os
import sys
from pathlib import Path

def main():
    """Create necessary directories and files."""
    project_root = Path(__file__).parent.parent
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/results/plots",
        "code/data",
        "code/preprocessing",
        "code/modeling",
        "code/visualization",
        "code/utils",
        "code/human_review",
        "tests/unit",
        "tests/integration",
        "docs",
        "specs/001-visual-motion-agency/contracts",
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    print("Project setup complete.")
