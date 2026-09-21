"""
Simple test to verify the project directory structure exists.
"""
import os
import pytest

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "projects", "PROJ-1018-llmxive-follow-up-extending-hierarchical")

REQUIRED_DIRS = [
    "src",
    "tests",
    "data/raw",
    "data/interim",
    "data/processed"
]

@pytest.mark.parametrize("dir_name", REQUIRED_DIRS)
def test_directory_exists(dir_name):
    """Assert that each required directory exists within the project root."""
    full_path = os.path.join(PROJECT_ROOT, dir_name)
    assert os.path.isdir(full_path), f"Directory not found: {full_path}"

def test_project_root_exists():
    """Assert that the project root directory exists."""
    assert os.path.isdir(PROJECT_ROOT), f"Project root not found: {PROJECT_ROOT}"