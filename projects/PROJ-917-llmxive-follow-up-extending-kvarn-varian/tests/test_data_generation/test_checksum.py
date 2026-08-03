import pytest
import os
import tempfile
import yaml
from pathlib import Path
from data_generation.utils import compute_checksum, compute_and_store_checksums

@pytest.fixture
def temp_data_dir():
    """Creates a temporary directory with some test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        
        # Create a few test files
        (data_dir / "file1.txt").write_text("Hello World")
        (data_dir / "subdir").mkdir()
        (data_dir / "subdir" / "file2.txt").write_text("Test Data")
        
        yield data_dir

@pytest.fixture
def temp_state_file():
    """Creates a temporary state file path."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        f.write("{}")
        state_path = Path(f.name)
    yield state_path
    if state_path.exists():
        os.remove(state_path)

def test_checksum_deterministic(temp_data_dir):
    """Test that the checksum for a file is deterministic."""
    file_path = temp_data_dir / "file1.txt"
    checksum1 = compute_checksum(file_path)
    checksum2 = compute_checksum(file_path)
    assert checksum1 == checksum2

def test_checksum_unique(temp_data_dir):
    """Test that different files have different checksums."""
    file1 = temp_data_dir / "file1.txt"
    file2 = temp_data_dir / "subdir" / "file2.txt"
    checksum1 = compute_checksum(file1)
    checksum2 = compute_checksum(file2)
    assert checksum1 != checksum2

def test_compute_and_store_checksums(temp_data_dir, temp_state_file):
    """Test the full checksum computation and storage process."""
    result = compute_and_store_checksums(temp_data_dir, temp_state_file)
    
    # Check that result contains expected files
    assert "file1.txt" in result
    assert "subdir/file2.txt" in result
    
    # Check that state file was updated
    assert temp_state_file.exists()
    with open(temp_state_file, 'r') as f:
        state_data = yaml.safe_load(f)
    
    assert "artifact_hashes" in state_data
    assert len(state_data["artifact_hashes"]) == 2
    assert state_data["artifact_hashes"]["file1.txt"] == result["file1.txt"]
