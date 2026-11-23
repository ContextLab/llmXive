"""
test_structure.py
-----------------
Simple unit test to verify that the project directory scaffolding
created by `code/create_structure.py` exists.
"""
import sys
from pathlib import Path

# Ensure the project root is on the import path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

def test_directories_exist():
    """
    Assert that all required top‑level directories are present.
    """
    required_dirs = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "models",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        project_root / "state",
    ]

    missing = [str(d) for d in required_dirs if not d.is_dir()]
    assert not missing, f"Missing required directories: {missing}"