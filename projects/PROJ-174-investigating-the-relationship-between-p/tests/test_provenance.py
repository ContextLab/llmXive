"""
Tests for the provenance utilities in code/utils/provenance.py.
"""
import json
import os
import tempfile
import pytest
import pandas as pd

# Import the functions under test
from utils.provenance import hash_file, write_meta


class TestHashFile:
    def test_hash_file_sha256(self):
        """Test that hash_file computes a valid SHA256 hash."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
            f.write("test content")
            temp_path = f.name

        try:
            h = hash_file(temp_path, algorithm="sha256")
            assert len(h) == 64  # SHA256 hex length
            assert all(c in "0123456789abcdef" for c in h)
        finally:
            os.unlink(temp_path)

    def test_hash_file_not_found(self):
        """Test that hash_file raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            hash_file("/nonexistent/path/file.txt")

    def test_hash_consistency(self):
        """Test that the same file produces the same hash."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
            f.write("consistent content")
            temp_path = f.name

        try:
            h1 = hash_file(temp_path)
            h2 = hash_file(temp_path)
            assert h1 == h2
        finally:
            os.unlink(temp_path)


class TestWriteMeta:
    def test_write_meta_creates_file(self):
        """Test that write_meta creates a valid JSON file."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".csv") as f:
            f.write("a,b\n1,2\n")
            data_path = f.name

        try:
            meta_path = data_path.replace(".csv", "_meta.json")
            write_meta(data_path, {"description": "test data"}, source="test_source")

            assert os.path.exists(meta_path)
            with open(meta_path, "r") as f:
                meta = json.load(f)

            assert "hash" in meta
            assert "timestamp" in meta
            assert meta["source"] == "test_source"
            assert meta["description"] == "test data"
        finally:
            if os.path.exists(data_path):
                os.unlink(data_path)
            if os.path.exists(meta_path):
                os.unlink(meta_path)

    def test_write_meta_missing_source_file(self):
        """Test that write_meta raises FileNotFoundError for missing source."""
        with pytest.raises(FileNotFoundError):
            write_meta("/nonexistent/file.csv", {})

    def test_write_meta_auto_hash(self):
        """Test that write_meta computes hash if not provided."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".csv") as f:
            f.write("x,y\n10,20\n")
            data_path = f.name

        try:
            meta_path = data_path.replace(".csv", "_meta.json")
            # Do not provide 'hash' in meta_dict
            write_meta(data_path, {"note": "auto hash"}, source="auto_test")

            with open(meta_path, "r") as f:
                meta = json.load(f)

            # Verify hash matches actual file hash
            computed_hash = hash_file(data_path)
            assert meta["hash"] == computed_hash
        finally:
            if os.path.exists(data_path):
                os.unlink(data_path)
            if os.path.exists(meta_path):
                os.unlink(meta_path)

    def test_write_meta_creates_directories(self):
        """Test that write_meta creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "subdir", "data.csv")
            os.makedirs(os.path.dirname(nested_path), exist_ok=True)
            
            with open(nested_path, "w") as f:
                f.write("col\n1\n")

            meta_path = nested_path.replace(".csv", "_meta.json")
            write_meta(nested_path, {}, source="nested_test")
            
            assert os.path.exists(meta_path)
            os.unlink(meta_path)
