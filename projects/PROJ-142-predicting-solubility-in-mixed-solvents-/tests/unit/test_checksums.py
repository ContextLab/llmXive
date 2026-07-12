"""
Unit tests for the checksums utility module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.checksums import generate_checksums, verify_checksums

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with sample files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "data"
        data_path.mkdir()
        
        # Create a subdirectory
        sub_dir = data_path / "processed"
        sub_dir.mkdir()
        
        # Create sample files
        file1 = data_path / "sample.txt"
        file1.write_text("Hello, World!")
        
        file2 = sub_dir / "data.csv"
        file2.write_text("col1,col2\n1,2\n3,4")
        
        yield data_path

def test_generate_checksums_creates_file(temp_data_dir):
    """Test that generate_checksums creates the JSON manifest file."""
    output_file = temp_data_dir / ".checksums.json"
    
    # Run generation
    manifest = generate_checksums(temp_data_dir, output_file)
    
    # Verify file exists
    assert output_file.exists()
    
    # Verify manifest structure
    assert "version" in manifest
    assert "algorithm" in manifest
    assert "checksums" in manifest
    assert manifest["algorithm"] == "sha256"
    
    # Verify checksums were calculated for our files
    assert "sample.txt" in manifest["checksums"]
    assert "processed/data.csv" in manifest["checksums"]

def test_generate_checksums_skips_checksum_file(temp_data_dir):
    """Test that the checksum file itself is not included in the manifest."""
    output_file = temp_data_dir / ".checksums.json"
    
    # Create a dummy checksum file first
    output_file.write_text("{}")
    
    manifest = generate_checksums(temp_data_dir, output_file)
    
    # The checksum file should not appear in the manifest keys
    assert ".checksums.json" not in manifest["checksums"]

def test_verify_checksums_success(temp_data_dir):
    """Test that verify_checksums returns True when files match."""
    output_file = temp_data_dir / ".checksums.json"
    generate_checksums(temp_data_dir, output_file)
    
    is_valid = verify_checksums(temp_data_dir, output_file)
    
    assert is_valid is True

def test_verify_checksums_failure_on_modification(temp_data_dir):
    """Test that verify_checksums returns False when a file is modified."""
    output_file = temp_data_dir / ".checksums.json"
    
    # Generate initial checksums
    generate_checksums(temp_data_dir, output_file)
    
    # Modify a file
    sample_file = temp_data_dir / "sample.txt"
    sample_file.write_text("Modified content!")
    
    # Verification should fail
    is_valid = verify_checksums(temp_data_dir, output_file)
    
    assert is_valid is False

def test_verify_checksums_missing_file(temp_data_dir):
    """Test that verify_checksums handles missing files correctly."""
    output_file = temp_data_dir / ".checksums.json"
    
    # Generate initial checksums
    generate_checksums(temp_data_dir, output_file)
    
    # Delete a file
    (temp_data_dir / "sample.txt").unlink()
    
    # Verification should fail
    is_valid = verify_checksums(temp_data_dir, output_file)
    
    assert is_valid is False
