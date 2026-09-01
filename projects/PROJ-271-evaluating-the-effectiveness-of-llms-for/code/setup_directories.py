import os
from pathlib import Path
from config import PROJECT_ROOT, DATA_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR


def create_project_directories() -> None:
    """Create all necessary project directories."""
    directories = [
        PROJECT_ROOT / "code",
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        RESULTS_DIR,
        PROJECT_ROOT / "tests" / "unit",
        PROJECT_ROOT / "tests" / "contract",
        PROJECT_ROOT / "contracts",
        PROJECT_ROOT / "models"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    print("All project directories created successfully.")
