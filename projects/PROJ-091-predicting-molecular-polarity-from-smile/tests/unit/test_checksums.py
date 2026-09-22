import os
import json
import tempfile
import pytest
from pathlib import Path
import pandas as pd

# Import the functions to test
from code.utils.checksums import compute_file_checksum, generate_manifest

def test_compute_file_checksum():
    """Test that checksum is computed correctly and is deterministic."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum1 = compute_file_checksum(temp_path)
        checksum2 = compute_file_checksum(temp_path)
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA256 hex length
    finally:
        os.unlink(temp_path)

def test_generate_manifest():
    """Test manifest generation with real files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy files
        file1_path = os.path.join(tmpdir, "file1.csv")
        file2_path = os.path.join(tmpdir, "file2.parquet")
        
        pd.DataFrame({"a": [1, 2]}).to_csv(file1_path, index=False)
        pd.DataFrame({"b": [3, 4]}).to_parquet(file2_path)
        
        manifest_path = os.path.join(tmpdir, "manifest.json")
        files = {
            "csv_file": file1_path,
            "parquet_file": file2_path
        }
        
        generate_manifest(manifest_path, files)
        
        assert os.path.exists(manifest_path)
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert "algorithm" in manifest
        assert manifest["algorithm"] == "sha256"
        assert "files" in manifest
        assert "csv_file" in manifest["files"]
        assert "parquet_file" in manifest["files"]
        assert "checksum" in manifest["files"]["csv_file"]
        assert "path" in manifest["files"]["csv_file"]

def test_generate_manifest_missing_file():
    """Test that manifest generation raises on missing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = os.path.join(tmpdir, "manifest.json")
        files = {
            "missing_file": os.path.join(tmpdir, "nonexistent.csv")
        }
        
        with pytest.raises(FileNotFoundError):
            generate_manifest(manifest_path, files)
