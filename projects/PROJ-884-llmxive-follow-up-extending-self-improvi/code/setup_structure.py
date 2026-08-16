import os
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).parent.parent
PROJECT_NAME = "PROJ-884-llmxive-follow-up-extending-self-improvi"
PROJECT_PATH = PROJECT_ROOT / "projects" / PROJECT_NAME

def setup_data_directories() -> None:
    """
    Creates the project directory structure as defined in T001a.
    
    Structure:
    projects/PROJ-884-llmxive-follow-up-extending-self-improvi/
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── code/
    │   ├── dataset/
    │   ├── symbolic/
    │   ├── bes/
    │   ├── analysis/
    │   └── utils/
    └── tests/
        ├── unit/
        └── integration/
    """
    directories: List[Path] = [
        PROJECT_PATH / "data" / "raw",
        PROJECT_PATH / "data" / "processed",
        PROJECT_PATH / "code" / "dataset",
        PROJECT_PATH / "code" / "symbolic",
        PROJECT_PATH / "code" / "bes",
        PROJECT_PATH / "code" / "analysis",
        PROJECT_PATH / "code" / "utils",
        PROJECT_PATH / "tests" / "unit",
        PROJECT_PATH / "tests" / "integration",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

    print(f"Setup complete. Created {created_count} new directories.")

def main() -> int:
    """Entry point for CLI execution."""
    try:
        setup_data_directories()
        return 0
    except PermissionError as e:
        print(f"Permission denied: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
