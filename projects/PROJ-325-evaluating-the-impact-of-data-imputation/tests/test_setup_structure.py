"""
Test to verify that the project structure created by setup_project.py exists.
This serves as a basic validation that T001 was executed correctly.
"""
import os
from pathlib import Path

def test_project_structure_exists():
    """Verify required directories exist."""
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/figures",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "specs/contracts",
        "figures",
        "state"
    ]

    root = Path(".")
    missing = []
    for d in required_dirs:
        path = root / d
        if not path.exists() or not path.is_dir():
            missing.append(str(path))

    assert len(missing) == 0, f"Missing required directories: {missing}"

def test_code_dir_is_writable():
    """Verify code directory is writable."""
    code_dir = Path("code")
    assert code_dir.exists() and code_dir.is_dir()
    # Try creating a temp file to ensure writability
    test_file = code_dir / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
    except Exception as e:
        raise AssertionError(f"Code directory is not writable: {e}")

def test_data_dirs_are_writable():
    """Verify data directories are writable."""
    data_dirs = ["data/raw", "data/processed", "data/figures"]
    for d_str in data_dirs:
        d = Path(d_str)
        assert d.exists() and d.is_dir(), f"Directory {d} does not exist"
        test_file = d / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            raise AssertionError(f"Directory {d} is not writable: {e}")
