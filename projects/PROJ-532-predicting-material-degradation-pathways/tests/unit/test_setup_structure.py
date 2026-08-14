import os
from pathlib import Path
import pytest

from setup_project_structure import ensure_dir, create_placeholder_file, main

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary root to simulate the project structure."""
    # Change CWD to tmp_path to simulate running the script in a clean env
    os.chdir(tmp_path)
    return tmp_path

def test_ensure_dir_creates_directory(temp_project_root):
    target = temp_project_root / "new_dir"
    assert not target.exists()
    ensure_dir(target)
    assert target.exists()
    assert target.is_dir()

def test_ensure_dir_idempotent(temp_project_root):
    target = temp_project_root / "existing_dir"
    target.mkdir()
    ensure_dir(target)  # Should not raise
    assert target.exists()

def test_create_placeholder_file(temp_project_root):
    target = temp_project_root / "subdir" / "file.txt"
    assert not target.exists()
    create_placeholder_file(target, content="Hello World")
    assert target.exists()
    assert target.read_text() == "Hello World"

def test_create_placeholder_file_skips_existing(temp_project_root):
    target = temp_project_root / "file.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("Existing Content")
    create_placeholder_file(target)
    assert target.read_text() == "Existing Content"

def test_main_creates_structure(temp_project_root):
    # Run the main function which creates the full tree
    main()

    base = Path("projects/PROJ-532-predicting-material-degradation-pathways")
    assert (base / "code").exists()
    assert (base / "data").exists()
    assert (base / "data" / "raw").exists()
    assert (base / "data" / "processed").exists()
    assert (base / "results").exists()
    assert (base / "results" / "metrics").exists()
    assert (base / "results" / "plots").exists()
    assert (base / "results" / "artifacts").exists()
    assert (base / "tests").exists()
    assert (base / "tests" / "unit").exists()
    assert (base / "tests" / "integration").exists()
    assert (base / "specs").exists()
    assert (base / "docs").exists()
    assert (base / "README.md").exists()
    assert (base / "code" / "__init__.py").exists()
    assert (base / "tests" / "__init__.py").exists()