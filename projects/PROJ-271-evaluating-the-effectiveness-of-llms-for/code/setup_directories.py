"""Script to set up project directory structure."""
import os
from pathlib import Path
from config import PROJECT_ROOT, DATA_DIR, DATA_RAW_DIR, DATA_PROCESSED_DIR, RESULTS_DIR

def create_project_directories() -> None:
    """Create all required project directories."""
    dirs = [
        PROJECT_ROOT / "code",
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        RESULTS_DIR,
        PROJECT_ROOT / "tests" / "unit",
        PROJECT_ROOT / "tests" / "contract",
        PROJECT_ROOT / "specs",
        PROJECT_ROOT / "contracts",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print(f"Created {len(dirs)} directories.")
