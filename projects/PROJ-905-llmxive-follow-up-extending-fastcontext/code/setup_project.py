import os
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-905-llmxive-follow-up-extending-fastcontext.
    Executes the equivalent of:
    mkdir -p data/raw data/processed data/results code tests/unit tests/integration specs/contracts state
    """
    project_root = Path(__file__).resolve().parent.parent
    base_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests/unit",
        "tests/integration",
        "specs/contracts",
        "state"
    ]

    for base_dir in base_dirs:
        dir_path = project_root / base_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()