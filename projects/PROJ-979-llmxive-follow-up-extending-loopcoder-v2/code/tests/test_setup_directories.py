import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add code/src to path for imports if needed, though we test via script execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.run_setup import create_directory_structure, verify_directory_structure

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

def test_directory_structure_creation(temp_dir):
    """Test that all required directories are created."""
    # Create structure
    create_directory_structure(temp_dir)

    # Verify
    assert verify_directory_structure(temp_dir) is True

    # Check specific directories exist
    assert (temp_dir / "data" / "raw").exists()
    assert (temp_dir / "data" / "processed").exists()
    assert (temp_dir / "code" / "src").exists()
    assert (temp_dir / "code" / "tests").exists()
    assert (temp_dir / "code" / "notebooks").exists()
    assert (temp_dir / "code" / "scripts").exists()
    assert (temp_dir / "code" / "config").exists()
    assert (temp_dir / "paper").exists()
    assert (temp_dir / "state").exists()
    assert (temp_dir / "contracts").exists()

def test_no_overwrite_existing_files(temp_dir):
    """Test that existing directories are not removed/overwritten."""
    # Create a dummy file in one of the target directories
    data_raw = temp_dir / "data" / "raw"
    data_raw.mkdir(parents=True)
    dummy_file = data_raw / "test.txt"
    dummy_file.write_text("test content")

    # Run creation again
    create_directory_structure(temp_dir)

    # Verify dummy file still exists
    assert dummy_file.exists()
    assert dummy_file.read_text() == "test content"