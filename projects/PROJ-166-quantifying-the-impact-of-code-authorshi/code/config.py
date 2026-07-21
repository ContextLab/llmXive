"""
Configuration and utility functions for the project.
"""
import os
from pathlib import Path
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Random seeds
RANDOM_SEED = 42

# API Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
NVD_API_KEY = os.getenv("NVD_API_KEY", "")

def ensure_directories():
    """
    Creates the required directory structure for the project.
    This function ensures that data/raw, data/processed, logs, and contracts directories exist.
    """
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        LOGS_DIR,
        CONTRACTS_DIR,
        PROJECT_ROOT / "code" / "data",
        PROJECT_ROOT / "code" / "analysis",
        PROJECT_ROOT / "tests" / "unit",
        PROJECT_ROOT / "tests" / "integration",
        PROJECT_ROOT / "tests" / "contract",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    # Initialize __init__.py files if missing
    init_files = [
        PROJECT_ROOT / "code" / "__init__.py",
        PROJECT_ROOT / "code" / "data" / "__init__.py",
        PROJECT_ROOT / "code" / "analysis" / "__init__.py",
        PROJECT_ROOT / "tests" / "__init__.py",
        PROJECT_ROOT / "tests" / "unit" / "__init__.py",
        PROJECT_ROOT / "tests" / "integration" / "__init__.py",
        PROJECT_ROOT / "tests" / "contract" / "__init__.py",
    ]
    for f in init_files:
        if not f.exists():
            f.touch()

if __name__ == "__main__":
    ensure_directories()
    print("Directories ensured.")
