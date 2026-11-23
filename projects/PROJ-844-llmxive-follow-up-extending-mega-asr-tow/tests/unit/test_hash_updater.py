"""Unit tests for hash updater functionality."""
import pytest
from pathlib import Path
from code.hash_updater import compute_file_hash, load_state, save_state


class TestHashComputation:
    def test_compute_hash_empty_file(self, tmp_path):
        """Test hash computation on empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("")
        hash_val = compute_file_hash(file_path)
        assert hash_val is not None
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA256 hex length

    def test_compute_hash_content(self, tmp_path):
        """Test hash computation on file with content."""
        file_path = tmp_path / "content.txt"
        file_path.write_text("Hello World")
        hash_val = compute_file_hash(file_path)
        assert hash_val is not None

class TestStateManagement:
    def test_save_load_state(self, tmp_path):
        """Test saving and loading state dictionary."""
        state_path = tmp_path / "state.yaml"
        test_state = {
            "files": {
                "data/test.csv": "abc123"
            },
            "version": 1
        }
        
        save_state(state_path, test_state)
        loaded = load_state(state_path)
        
        assert loaded == test_state
