"""
Configuration and environment setup.
"""
import os
from pathlib import Path
from typing import Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Directories to ensure exist
DIRECTORIES = [
    DATA_DIR,
    DATA_DIR / "raw",
    DATA_DIR / "processed",
    DATA_DIR / "logs",
    DATA_DIR / "config",
    CODE_DIR,
    CODE_DIR / "data",
    CODE_DIR / "model",
    CODE_DIR / "analysis",
    CODE_DIR / "utils",
    TESTS_DIR,
    TESTS_DIR / "unit",
    TESTS_DIR / "contract",
    DOCS_DIR,
]

def ensure_directories() -> None:
    """Create all required project directories if they do not exist."""
    for directory in DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> dict:
    """Return a summary of the current configuration."""
    ensure_directories()
    return {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "code_dir": str(CODE_DIR),
        "tests_dir": str(TESTS_DIR),
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
    }

# Initialize directories on import if needed (or let main scripts call it)
# ensure_directories()
