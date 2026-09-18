import os
import sys
import pytest
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from scripts.setup_project_structure import create_directories, create_init_files

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to act as project root."""
    return tmp_path

def test_create_directories(temp_project_root):
    """Test that create_directories creates all required directories."""
    create_directories(temp_project_root)

    # Check code subdirectories
    assert (temp_project_root / "code" / "data").exists()
    assert (temp_project_root / "code" / "modeling").exists()
    assert (temp_project_root / "code" / "utils").exists()
    assert (temp_project_root / "code" / "cli").exists()

    # Check test subdirectories
    assert (temp_project_root / "tests" / "unit").exists()
    assert (temp_project_root / "tests" / "integration").exists()

    # Check data subdirectories
    assert (temp_project_root / "data" / "raw").exists()
    assert (temp_project_root / "data" / "processed").exists()
    assert (temp_project_root / "data" / "interim").exists()

def test_create_init_files(temp_project_root):
    """Test that create_init_files creates all required __init__.py files."""
    # First create directories
    create_directories(temp_project_root)
    # Then create init files
    create_init_files(temp_project_root)

    # Check that all __init__.py files exist
    init_files = [
        temp_project_root / "code" / "__init__.py",
        temp_project_root / "code" / "data" / "__init__.py",
        temp_project_root / "code" / "modeling" / "__init__.py",
        temp_project_root / "code" / "utils" / "__init__.py",
        temp_project_root / "code" / "cli" / "__init__.py",
        temp_project_root / "tests" / "__init__.py",
    ]

    for init_file in init_files:
        assert init_file.exists(), f"Missing __init__.py file: {init_file}"
        assert init_file.is_file(), f"Not a file: {init_file}"