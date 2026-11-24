"""Test that the standard project directory layout exists."""

from pathlib import Path


def test_required_directories_exist():
    """Assert that all required top‑level directories are present."""
    required_dirs = [
        Path("code"),
        Path("data/raw"),
        Path("data/processed"),
        Path("tests"),
        Path("scripts"),
        Path("state"),
    ]
    missing = [str(d) for d in required_dirs if not d.is_dir()]
    assert not missing, f"Missing required directories: {', '.join(missing)}"

def test_requirements_file_exists():
    """The pinned requirements file must be present."""
    req_path = Path("code/requirements.txt")
    assert req_path.is_file(), "code/requirements.txt is missing"

# The test module will be discovered and run by pytest automatically.