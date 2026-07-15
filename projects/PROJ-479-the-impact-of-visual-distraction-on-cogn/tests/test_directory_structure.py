"""
Contract test to verify the existence of required project directories.
This test satisfies the verification requirement for T001a, T001b, T001c, T001d, T001e, and T004.
"""
import os
import pytest

REQUIRED_DIRS = [
    "code",
    "data",
    "results",
    "tests",
    "specs/001-visual-distraction-cognitive-control",
    "data/raw",
    "data/processed",
    "results/statistics",
    "results/plots",
    "results/sensitivity",
    "results/methodology",
    "tests/contract",
    "tests/unit",
]

@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_directory_exists(dir_path):
    """Assert that a specific required directory exists."""
    assert os.path.isdir(dir_path), f"Required directory missing: {dir_path}"

def test_root_structure():
    """Verify the top-level directory structure."""
    assert os.path.isdir("code"), "code/ directory missing"
    assert os.path.isdir("data"), "data/ directory missing"
    assert os.path.isdir("results"), "results/ directory missing"
    assert os.path.isdir("tests"), "tests/ directory missing"