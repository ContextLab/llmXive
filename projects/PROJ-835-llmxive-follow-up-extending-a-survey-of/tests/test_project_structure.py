"""
test_project_structure.py

Verifies that the core project directories have been created by
`code/create_project_structure.py`.
"""
from pathlib import Path

def test_directories_exist():
    # Project root is two levels up from this test file (tests/..)
    project_root = Path(__file__).resolve().parents[2]

    required_dirs = ["src", "tests", "data", "models", "results"]
    for d in required_dirs:
        dir_path = project_root / d
        assert dir_path.is_dir(), f"Required directory missing: {dir_path}"