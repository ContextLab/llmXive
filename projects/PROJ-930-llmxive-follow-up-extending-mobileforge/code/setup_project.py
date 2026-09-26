import os
import sys
from pathlib import Path

def main():
    """
    Initialize the Python 3.11 project structure and validate dependencies.
    This script ensures the directory structure exists and checks for the
    presence of the requirements.txt file.
    """
    project_root = Path(__file__).parent
    requirements_path = project_root / "requirements.txt"

    # Ensure directory structure exists
    dirs = [
        "data/raw", "data/processed", "data/evaluation",
        "models", "utils", "tests/unit", "tests/integration"
    ]
    for d in dirs:
        (project_root / d).mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified directory: {project_root / d}")

    # Verify requirements.txt exists
    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print("Project initialization complete.")
    print("Dependencies to install: torch, transformers, datasets, pandas, scikit-learn, pytest, statsmodels")
    return 0

if __name__ == "__main__":
    sys.exit(main())