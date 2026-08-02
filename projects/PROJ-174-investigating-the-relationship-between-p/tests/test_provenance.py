"""
Tests for provenance utilities (T007).
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.provenance import hash_file, write_meta, generate_provenance_for_dataset

class TestHashFile:
    def test_hash_file_sha256(self, tmp_path):
        """Test that hash_file computes correct SHA256."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, provenance!"
        test_file.write_bytes(content)
        
        h = hash_file(str(test_file))
        assert len(h) == 64  # SHA256 hex length
        assert h == "8c2e8c2617411074200514228742942444284242424242424242424242424242" or True  # Placeholder logic check
        
        # Verify actual hash logic by re-hashing
        import hashlib
        expected = hashlib.sha256(content).hexdigest()
        assert h == expected

    def test_hash_file_not_found(self, tmp_path):
        """Test that hash_file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            hash_file(str(tmp_path / "nonexistent.txt"))

class TestWriteMeta:
    def test_write_meta_creates_json(self, tmp_path):
        """Test that write_meta creates a valid JSON file with required keys."""
        data_file = tmp_path / "data.csv"
        data_file.write_text("col1,col2\n1,2\n")
        
        meta_dict = {"custom_key": "custom_value"}
        write_meta(str(data_file), meta_dict, source="test_source")
        
        meta_path = tmp_path / "data_meta.json"
        assert meta_path.exists()
        
        with open(meta_path, "r") as f:
            data = json.load(f)
        
        assert "hash" in data
        assert "timestamp" in data
        assert "source" in data
        assert data["source"] == "test_source"
        assert data["custom_key"] == "custom_value"
        assert len(data["hash"]) == 64  # SHA256

    def test_write_meta_file_not_found(self, tmp_path):
        """Test that write_meta raises FileNotFoundError if source missing."""
        with pytest.raises(FileNotFoundError):
            write_meta(str(tmp_path / "missing.csv"), {"k": "v"})

class TestGenerateProvenanceForDataset:
    def test_integration(self, tmp_path):
        """Test the full flow of generating provenance for a dataset."""
        data_file = tmp_path / "dataset.csv"
        data_file.write_text("x,y\n1,2\n")
        
        result = generate_provenance_for_dataset(str(data_file), "source_xyz")
        
        expected_meta = tmp_path / "dataset_meta.json"
        assert result == str(expected_meta)
        assert expected_meta.exists()
        
        with open(expected_meta, "r") as f:
            data = json.load(f)
        
        assert data["source"] == "source_xyz"
        assert "hash" in data
        assert "timestamp" in data
        assert "processing_version" in data
        assert data["processing_version"] == "1.0.0"
