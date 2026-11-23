import os
import tempfile
import hashlib
from pathlib import Path
import yaml
import pytest

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from checksums import (
    compute_sha256_file,
    scan_raw_data_directory,
    record_checksums_to_state,
    main
)

def test_compute_sha256_file():
    """Test SHA-256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test data")
        temp_path = Path(f.name)
    
    try:
        # "test data" SHA-256
        expected = "1c5261564314776795481211631008311233141111111111111111111111111" # Placeholder, actual calc below
        # Actual calculation:
        expected_hash = hashlib.sha256(b"test data").hexdigest()
        
        result = compute_sha256_file(temp_path)
        assert result == expected_hash
    finally:
        os.unlink(temp_path)

def test_scan_raw_data_directory():
    """Test scanning a directory for files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file1.txt").write_text("a")
        (tmp_path / "subdir" / "file2.txt").write_text("b")
        (tmp_path / ".hidden").write_text("c")
        
        files = scan_raw_data_directory(tmp_path)
        file_names = [f.name for f in files]
        
        assert "file1.txt" in file_names
        assert "file2.txt" in file_names
        assert ".hidden" not in file_names
        assert len(files) == 2

def test_record_checksums_to_state():
    """Test writing checksums to a YAML state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        state_file = tmp_path / "test_state.yaml"
        
        checksums = {
            "data/raw/file1.txt": "abc123",
            "data/raw/file2.txt": "def456"
        }
        
        record_checksums_to_state(checksums, state_file)
        
        assert state_file.exists()
        with open(state_file, "r") as f:
            data = yaml.safe_load(f)
        
        assert "projects" in data
        project_id = "PROJ-712-predicting-individual-pain-sensitivity-f"
        assert project_id in data["projects"]
        assert data["projects"][project_id]["data_checksums"] == checksums
        assert data["projects"][project_id]["checksum_algorithm"] == "SHA-256"
