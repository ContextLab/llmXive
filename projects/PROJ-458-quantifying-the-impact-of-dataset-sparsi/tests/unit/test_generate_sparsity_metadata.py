"""
Unit tests for generate_sparsity_metadata.py (Task T034)
"""
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from generate_sparsity_metadata import generate_metadata, load_rss_manifest

def test_generate_metadata_creates_file():
    """Test that generate_metadata creates the correct JSON file with required keys."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a dummy CSV file to act as the subset
        csv_path = tmpdir / "subset_test.csv"
        csv_path.write_text("id,val\n1,2\n3,4")
        
        # Define subset
        subset_def = {
            "level": "10",
            "seed": 42,
            "percentage": 10.0,
            "filename": "subset_test.csv"
        }
        
        output_dir = tmpdir / "metadata"
        
        # Run function
        result = generate_metadata(subset_def, tmpdir, output_dir)
        
        # Verify file exists
        expected_meta_path = output_dir / "sparsity_10_42.json"
        assert expected_meta_path.exists(), "Metadata file was not created"
        
        # Verify content
        with open(expected_meta_path, 'r') as f:
            meta = json.load(f)
        
        assert meta["seed"] == 42
        assert meta["percentage"] == 10.0
        assert "criteria" in meta
        assert "checksum" in meta
        assert len(meta["checksum"]) == 64  # SHA-256 hex length

def test_generate_metadata_checksum_matches():
    """Test that the computed checksum matches the actual file checksum."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        content = "test_data_123"
        csv_path = tmpdir / "data.csv"
        csv_path.write_text(content)
        
        # Calculate expected hash
        expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        subset_def = {
            "level": "20",
            "seed": 123,
            "percentage": 20.0,
            "filename": "data.csv"
        }
        
        output_dir = tmpdir / "meta"
        generate_metadata(subset_def, tmpdir, output_dir)
        
        with open(output_dir / "sparsity_20_123.json", 'r') as f:
            meta = json.load(f)
        
        assert meta["checksum"] == expected_hash

def test_load_rss_manifest_invalid():
    """Test that load_rss_manifest raises error on missing file."""
    with pytest.raises(FileNotFoundError):
        load_rss_manifest(Path("non_existent_file.json"))

def test_load_rss_manifest_not_list():
    """Test that load_rss_manifest raises error if root is not a list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "bad.json"
        p.write_text('{"key": "value"}')
        with pytest.raises(ValueError):
            load_rss_manifest(p)
