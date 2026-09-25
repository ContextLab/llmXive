import os
import sys
import tempfile
import hashlib
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.helpers import (
    compute_file_checksum,
    store_data_checksum,
    verify_data_checksum,
    get_state_file_path,
    get_submissions_csv_path,
    get_project_root
)
import yaml

def test_compute_file_checksum_valid_file():
    """Test that checksum is computed correctly for a valid file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)
    
    try:
        checksum = compute_file_checksum(temp_path)
        expected = hashlib.sha256(b"Hello, World!").hexdigest()
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_compute_file_checksum_nonexistent_file():
    """Test that FileNotFoundError is raised for nonexistent file."""
    fake_path = Path("/nonexistent/file.txt")
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(fake_path)

def test_store_and_verify_checksum():
    """Test storing and verifying checksums in state file."""
    # Create a temporary file to act as our data
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("id,value\n1,10\n2,20\n")
        data_path = Path(f.name)
    
    # Mock the get_submissions_csv_path to return our temp file
    # We need to patch the function or use a different approach.
    # Since we can't easily patch the function in helpers, we'll test the logic directly
    # by manipulating the state file.
    
    # Compute checksum
    checksum = compute_file_checksum(data_path)
    
    # Store it (using the real state path, but we'll clean up later)
    # To avoid polluting the real state file, we'll use a temporary state file logic
    # But for this test, let's assume the state file path is writable.
    # We'll create a minimal test that verifies the logic.
    
    # Instead, let's test the verification logic by manually creating the state
    state_path = get_state_file_path()
    original_state = None
    
    if state_path.exists():
        with open(state_path, 'r') as f:
            original_state = f.read()
    
    try:
        # Create a test state
        test_state = {
            'data_checksums': {
                'submissions.csv': {
                    'checksum': checksum,
                    'timestamp': '2024-01-01T00:00:00',
                    'file_path': str(data_path)
                }
            }
        }
        
        with open(state_path, 'w') as f:
            yaml.safe_dump(test_state, f)
        
        # Verify should pass
        # We need to mock get_submissions_csv_path to return data_path
        # Since we can't easily do that, we'll just verify the logic works
        # by temporarily replacing the path in the module
        import utils.helpers as helpers_module
        original_func = helpers_module.get_submissions_csv_path
        helpers_module.get_submissions_csv_path = lambda: data_path
        
        try:
            assert verify_data_checksum() is True
        finally:
            helpers_module.get_submissions_csv_path = original_func
            
    finally:
        # Restore original state
        if original_state:
            with open(state_path, 'w') as f:
                f.write(original_state)
        elif state_path.exists():
            os.unlink(state_path)
        
        os.unlink(data_path)

def test_verify_data_checksum_mismatch():
    """Test that RuntimeError is raised on checksum mismatch."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("id,value\n1,10\n2,20\n")
        data_path = Path(f.name)
    
    state_path = get_state_file_path()
    original_state = None
    
    if state_path.exists():
        with open(state_path, 'r') as f:
            original_state = f.read()
    
    try:
        # Create a state with a WRONG checksum
        wrong_checksum = "0" * 64
        test_state = {
            'data_checksums': {
                'submissions.csv': {
                    'checksum': wrong_checksum,
                    'timestamp': '2024-01-01T00:00:00',
                    'file_path': str(data_path)
                }
            }
        }
        
        with open(state_path, 'w') as f:
            yaml.safe_dump(test_state, f)
        
        import utils.helpers as helpers_module
        original_func = helpers_module.get_submissions_csv_path
        helpers_module.get_submissions_csv_path = lambda: data_path
        
        try:
            with pytest.raises(RuntimeError, match="DATA INTEGRITY FAILURE"):
                verify_data_checksum()
        finally:
            helpers_module.get_submissions_csv_path = original_func
            
    finally:
        if original_state:
            with open(state_path, 'w') as f:
                f.write(original_state)
        elif state_path.exists():
            os.unlink(state_path)
        
        os.unlink(data_path)

def test_verify_data_checksum_no_stored_checksum():
    """Test that verification passes if no checksum is stored."""
    state_path = get_state_file_path()
    original_state = None
    
    if state_path.exists():
        with open(state_path, 'r') as f:
            original_state = f.read()
    
    try:
        # Create empty state
        with open(state_path, 'w') as f:
            f.write("{}")
        
        # Should not raise
        assert verify_data_checksum() is True
        
    finally:
        if original_state:
            with open(state_path, 'w') as f:
                f.write(original_state)
        elif state_path.exists():
            os.unlink(state_path)