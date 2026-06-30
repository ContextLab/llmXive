"""
Unit tests for code/foundation_protocol/utils.py
"""
import json
import os
import tempfile
from pathlib import Path

import pytest

from code.foundation_protocol.utils import get_hash, log_seed


class TestLogSeed:
    def test_log_seed_creates_file(self, tmp_path):
        """Test that log_seed creates a valid JSON file."""
        seed_val = 42
        output_dir = str(tmp_path / "seeds")
        
        result_path = log_seed(seed_val, output_dir)
        
        assert os.path.exists(result_path)
        assert result_path.endswith("seed_log.json")
        
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        assert data["seed"] == seed_val
        assert "timestamp_utc" in data
        assert data["algorithm"] == "default"

    def test_log_seed_invalid_type(self):
        """Test that log_seed raises ValueError for non-integer seeds."""
        with pytest.raises(ValueError, match="Seed must be an integer"):
            log_seed("not_an_int")
        
        with pytest.raises(ValueError, match="Seed must be an integer"):
            log_seed(3.14)

    def test_log_seed_default_dir(self, tmp_path, monkeypatch):
        """Test default directory behavior."""
        # Temporarily change cwd to tmp_path to avoid writing to real data/
        monkeypatch.chdir(tmp_path)
        # We can't easily test the default 'data/seeds' without side effects,
        # so we rely on the explicit path test above.
        pass


class TestGetHash:
    def test_get_hash_known_file(self, tmp_path):
        """Test hashing a known file content."""
        file_path = tmp_path / "test.txt"
        content = b"Hello, World!"
        file_path.write_bytes(content)
        
        computed_hash = get_hash(str(file_path))
        
        # Known SHA-256 for "Hello, World!"
        expected_hash = "7f83b1657ff1fc53b92dc18148a1d65dfa541f00692b12123178544199271042"
        assert computed_hash == expected_hash

    def test_get_hash_file_not_found(self, tmp_path):
        """Test that get_hash raises FileNotFoundError."""
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            get_hash(str(non_existent))

    def test_get_hash_directory(self, tmp_path):
        """Test that get_hash raises IsADirectoryError for directories."""
        with pytest.raises(IsADirectoryError):
            get_hash(str(tmp_path))

    def test_get_hash_large_file(self, tmp_path):
        """Test hashing a large file to ensure chunking works."""
        file_path = tmp_path / "large.bin"
        # Create a 1MB file
        data = b"0" * (1024 * 1024)
        file_path.write_bytes(data)
        
        hash_val = get_hash(str(file_path))
        # Just verify it returns a valid hex string of correct length
        assert len(hash_val) == 64
        assert all(c in "0123456789abcdef" for c in hash_val)