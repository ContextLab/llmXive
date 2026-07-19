import os
import sys
import shutil
import tempfile
from pathlib import Path
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup_project import create_directory_structure, write_setup_log

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root."""
    tmp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(tmp_dir)
    yield Path(tmp_dir)
    os.chdir(original_cwd)
    shutil.rmtree(tmp_dir)

def test_create_directory_structure(temp_project_root):
    """Test that all required directories are created."""
    created = create_directory_structure()
    
    expected_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "artifacts/models",
        "artifacts/plots",
        "artifacts/reports",
        "logs"
    ]
    
    assert len(created) == len(expected_dirs)
    
    for d in expected_dirs:
        p = temp_project_root / d
        assert p.exists(), f"Directory {d} was not created"
        assert p.is_dir(), f"{d} is not a directory"

def test_write_setup_log(temp_project_root):
    """Test that the setup log is written correctly."""
    # Create dirs first
    create_directory_structure()
    
    # Write log
    log_path = write_setup_log(["code", "logs"])
    
    assert log_path.exists(), "logs/setup.log was not created"
    
    with open(log_path, "r") as f:
        content = f.read()
    
    assert "successful" in content.lower(), "Log does not contain success message"
    assert "directories created" in content.lower(), "Log does not contain count"
    
    # Check timestamp format (basic check)
    assert "[" in content and "]" in content, "Log does not contain timestamp"

def test_full_t001_flow(temp_project_root):
    """Test the full flow of T001: create dirs and write log."""
    from setup_project import main
    
    # Capture stdout or just run
    try:
        main()
    except Exception as e:
        pytest.fail(f"main() raised an exception: {e}")
    
    # Verify artifacts
    assert (temp_project_root / "logs" / "setup.log").exists()
    assert (temp_project_root / "data" / "raw").exists()
    assert (temp_project_root / "artifacts" / "models").exists()