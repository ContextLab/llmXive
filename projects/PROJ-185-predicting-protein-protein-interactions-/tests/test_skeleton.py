import pytest
from pathlib import Path

def test_repository_skeleton_exists():
    """
    Verify that the required top‑level repository skeleton directories exist.
    This test is intended to be run in CI after the `T001` skeleton creation step.
    """
    # The repository root is three levels up from this test file:
    #   tests/test_skeleton.py -> code/tests -> code -> repository root
    repo_root = Path(__file__).resolve().parents[3]

    required_dirs = ["src", "tests", "data", "results", "docs", "contracts"]
    missing = [d for d in required_dirs if not (repo_root / d).is_dir()]

    assert not missing, f"Missing required skeleton directories: {', '.join(missing)}"