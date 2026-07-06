"""
Tests to verify the project structure created by T001.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture
def base_dir():
    """Return the current working directory as the base."""
    return Path.cwd()

required_dirs = [
    "src",
    "tests",
    "data",
    "data/logs",
    "data/results",
    "data/reports",
    "specs/001-evaluate-prompting-strategies/contracts",
    "state/projects",
]

@pytest.mark.parametrize("rel_path", required_dirs)
def test_directory_exists(base_dir, rel_path):
    """Assert that each required directory exists."""
    full_path = base_dir / rel_path
    assert full_path.exists(), f"Directory {rel_path} does not exist"
    assert full_path.is_dir(), f"{rel_path} exists but is not a directory"

def test_data_logs_writable(base_dir):
    """Assert that data/logs is writable (basic permission check)."""
    log_dir = base_dir / "data" / "logs"
    if not log_dir.exists():
        pytest.skip("data/logs does not exist yet; run setup first")
    
    test_file = log_dir / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
    except PermissionError:
        pytest.fail(f"Cannot write to {log_dir}")
    except Exception as e:
        pytest.fail(f"Unexpected error writing to {log_dir}: {e}")