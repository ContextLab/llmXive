import os
import json
import tempfile
import hashlib
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from verify_hashes import calculate_sha256, verify_and_update_hashes

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()
        (data_dir / "raw").mkdir()
        (data_dir / "processed").mkdir()
        
        # Create test files
        test_file_1 = data_dir / "raw" / "test1.csv"
        test_file_1.write_text("col1,col2\n1,2\n3,4")
        
        test_file_2 = data_dir / "processed" / "test2.json"
        test_file_2.write_text('{"key": "value"}')
        
        yield str(data_dir)
        # Cleanup handled by TemporaryDirectory

@pytest.fixture
def temp_state_dir():
    """Create a temporary state directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir) / "state"
        state_dir.mkdir()
        yield str(state_dir)

def test_calculate_sha256():
    """Test SHA256 calculation for a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        hash_result = calculate_sha256(temp_path)
        expected_hash = hashlib.sha256(b"test content").hexdigest()
        assert hash_result == expected_hash
    finally:
        os.unlink(temp_path)

def test_calculate_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("/nonexistent/file/path.txt")

def test_verify_and_update_hashes_creates_state(temp_data_dir, temp_state_dir):
    """Test that verify_and_update_hashes creates state file."""
    # Temporarily override data_dir and state_file paths for testing
    import verify_hashes as vh
    
    # We need to test the function with our temp directories
    # Since the function uses hardcoded paths, we'll test the core logic
    
    # Create a mock state file path
    state_file = os.path.join(temp_state_dir, "hashes.json")
    
    # The function expects relative paths from project root
    # For testing, we'll verify the core functionality
    result = verify_and_update_hashes(state_file, temp_data_dir)
    
    assert result is True
    assert os.path.exists(state_file)
    
    with open(state_file, 'r') as f:
        hashes = json.load(f)
    
    assert len(hashes) > 0
    assert any("test1.csv" in key for key in hashes.keys())
    assert any("test2.json" in key for key in hashes.keys())

def test_hash_consistency(temp_data_dir, temp_state_dir):
    """Test that hashes remain consistent across multiple runs."""
    state_file = os.path.join(temp_state_dir, "hashes.json")
    
    # First run
    result1 = verify_and_update_hashes(state_file, temp_data_dir)
    
    with open(state_file, 'r') as f:
        hashes1 = json.load(f)
    
    # Second run (should be identical)
    result2 = verify_and_update_hashes(state_file, temp_data_dir)
    
    with open(state_file, 'r') as f:
        hashes2 = json.load(f)
    
    assert result1 is True
    assert result2 is True
    assert hashes1 == hashes2

def test_hash_changes_when_file_modified(temp_data_dir, temp_state_dir):
    """Test that hash changes when file content is modified."""
    state_file = os.path.join(temp_state_dir, "hashes.json")
    test_file = Path(temp_data_dir) / "raw" / "test1.csv"
    
    # Initial run
    verify_and_update_hashes(state_file, temp_data_dir)
    
    with open(state_file, 'r') as f:
        hashes_before = json.load(f)
    
    initial_hash = hashes_before.get(str(test_file.relative_to(Path("."))))
    
    # Modify file
    test_file.write_text("modified content")
    
    # Run again
    verify_and_update_hashes(state_file, temp_data_dir)
    
    with open(state_file, 'r') as f:
        hashes_after = json.load(f)
    
    final_hash = hashes_after.get(str(test_file.relative_to(Path("."))))
    
    assert initial_hash != final_hash
    assert len(final_hash) == 64  # SHA256 hex length
