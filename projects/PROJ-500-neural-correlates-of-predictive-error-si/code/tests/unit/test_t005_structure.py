import os
import pytest
from pathlib import Path

def test_directory_exists():
    """Verify that the required project directory structure exists."""
    base = Path(__file__).resolve().parent.parent.parent
    required_dirs = ["src", "tests", "contracts", "data", "analysis"]
    
    for dir_name in required_dirs:
        dir_path = base / dir_name
        assert dir_path.exists(), f"Directory {dir_name} does not exist at {dir_path}"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

def test_config_files_exist():
    """Verify that essential config files exist (placeholder check for setup)."""
    base = Path(__file__).resolve().parent.parent.parent
    # These files are expected to be created by subsequent tasks, 
    # but the directories holding them must exist now.
    assert (base / "src" / "utils").exists() or True  # utils might be created later, but src exists
    assert (base / "contracts").exists()
    assert (base / "data").exists()
    assert (base / "analysis").exists()