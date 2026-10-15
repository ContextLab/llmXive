"""T026-style verification for T001: project directory layout exists."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

REQUIRED_DIRECTORIES = [
    "code",
    "utils",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/interim",
    "data/processed",
]

def test_all_required_directories_exist():
    for rel in REQUIRED_DIRECTORIES:
        assert os.path.isdir(PROJECT_ROOT / rel), f"Missing directory: {rel}"

def test_setup_dirs_script_exists():
    assert (PROJECT_ROOT / "code" / "setup_dirs.py").is_file()