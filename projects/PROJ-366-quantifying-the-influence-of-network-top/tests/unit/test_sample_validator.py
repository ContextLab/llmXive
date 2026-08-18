"""
Unit tests for T013b: Sample Validator.
"""
import json
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from ingest.sample_validator import is_valid_xyz_file, scan_raw_directory

def test_is_valid_xyz_file_valid():
    """Test that a valid XYZ file returns True."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        # Header: 2 atoms
        f.write("2\n")
        f.write("Comment line\n")
        f.write("Si 0.0 0.0 0.0\n")
        f.write("Si 1.0 1.0 1.0\n")
        temp_path = Path(f.name)
    
    try:
        assert is_valid_xyz_file(temp_path) is True
    finally:
        temp_path.unlink()

def test_is_valid_xyz_file_invalid_header():
    """Test that an XYZ file with non-integer header returns False."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        f.write("invalid\n")
        f.write("Si 0.0 0.0 0.0\n")
        temp_path = Path(f.name)
    
    try:
        assert is_valid_xyz_file(temp_path) is False
    finally:
        temp_path.unlink()

def test_is_valid_xyz_file_insufficient_lines():
    """Test that an XYZ file with fewer lines than atom count returns False."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        f.write("5\n")
        f.write("Comment\n")
        f.write("Si 0.0 0.0 0.0\n")
        temp_path = Path(f.name)
    
    try:
        assert is_valid_xyz_file(temp_path) is False
    finally:
        temp_path.unlink()

def test_is_valid_xyz_file_not_found():
    """Test that a non-existent file returns False."""
    assert is_valid_xyz_file(Path("non_existent_file.xyz")) is False

def test_scan_raw_directory():
    """Test scanning a directory for valid XYZ files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create valid files
        for i in range(3):
            file_path = tmp_path / f"sample_{i}.xyz"
            with open(file_path, 'w') as f:
                f.write(f"{i+1}\n")
                f.write("Comment\n")
                for _ in range(i+1):
                    f.write("Si 0.0 0.0 0.0\n")
        
        # Create an invalid file
        invalid_path = tmp_path / "invalid.xyz"
        with open(invalid_path, 'w') as f:
            f.write("bad\n")
        
        # Create a non-xyz file
        txt_path = tmp_path / "readme.txt"
        with open(txt_path, 'w') as f:
            f.write("hello")

        valid_files = scan_raw_directory(tmp_path)
        
        assert len(valid_files) == 3
        assert all(f.suffix == '.xyz' for f in valid_files)
        assert all(f.exists() for f in valid_files)