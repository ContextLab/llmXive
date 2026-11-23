import os
from pathlib import Path
from config import PROJECT_ROOT, DATA_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR

def create_project_directories():
    """Creates the required project directories."""
    dirs = [
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        RESULTS_DIR,
        PROJECT_ROOT / "tests" / "unit",
        PROJECT_ROOT / "tests" / "contract"
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")

if __name__ == "__main__":
    create_project_directories()
