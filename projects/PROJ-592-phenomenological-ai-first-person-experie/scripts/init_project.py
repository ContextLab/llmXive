"""Project initialization script.

Creates the necessary directory structure for the phenomenological AI pipeline.
"""
from pathlib import Path
import sys

def main():
    project_root = Path(__file__).parent.parent
    directories = [
        "code",
        "code/analysis",
        "code/generation",
        "code/utils",
        "code/validation",
        "data/raw",
        "data/processed",
        "data/qualitative",
        "tests/unit",
        "tests/integration",
        "specs/contracts",
        "figures",
        "scripts",
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")

    print("Project structure initialized successfully.")

if __name__ == "__main__":
    main()