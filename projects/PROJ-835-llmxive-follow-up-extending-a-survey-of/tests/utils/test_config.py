"""
Tests for configuration utilities.
"""
import os
import tempfile
import shutil
import pytest
from pathlib import Path
import yaml
import sys

# Add project root to path if not already there
_current_dir = Path(__file__).resolve().parent
_project_root = _current_dir.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.utils.config import (
    set_seed, 
    get_project_root, 
    get_data_path, 
    get_results_path, 
    get_state_path,
    load_state_file,
    save_state_file,
    compute_file_hash,
    update_artifact_hash,
    ensure_cpu_only,
    DATA_DIR,
    RESULTS_DIR,
    STATE_DIR
)


class TestSeedManagement:
    def test_set_seed_determinism(self):
        """Test that setting seed produces reproducible results."""
        import random
        import numpy as np
        import torch

        set_seed(42)
        val1 = random.random()
        set_seed(42)
        val2 = random.random()
        
        assert val1 == val2

        set_seed(42)
        arr1 = np.random.rand(5)
        set_seed(42)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2)


class TestPathManagement:
    def test_get_project_root_exists(self):
        """Test that project root is a valid directory."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_data_path(self):
        """Test data path generation."""
        path = get_data_path("test.csv")
        assert str(path).startswith(str(DATA_DIR))
        assert path.name == "test.csv"

    def test_get_results_path(self):
        """Test results path generation."""
        path = get_results_path("report.md")
        assert str(path).startswith(str(RESULTS_DIR))
        assert path.name == "report.md"

    def test_get_state_path(self):
        """Test state path generation."""
        path = get_state_path("state.yaml")
        assert str(path).startswith(str(STATE_DIR))
        assert path.name == "state.yaml"


class TestStateFileIO:
    def setup_method(self):
        """Create temporary state directory for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_state_dir = STATE_DIR
        
        # Temporarily override state dir
        import src.utils.config as config_module
        config_module.STATE_DIR = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary state directory."""
        import src.utils.config as config_module
        config_module.STATE_DIR = self.original_state_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_nonexistent_state(self):
        """Test loading a non-existent state file returns default."""
        state = load_state_file("nonexistent_project")
        assert "artifact_hashes" in state
        assert state["artifact_hashes"] == {}

    def test_save_and_load_state(self):
        """Test saving and loading state data."""
        test_data = {
            "artifact_hashes": {
                "file1.csv": "abc123",
                "file2.csv": "def456"
            },
            "metadata": "test"
        }
        
        save_state_file("test_project", test_data)
        loaded = load_state_file("test_project")
        
        assert loaded == test_data

    def test_update_artifact_hash(self):
        """Test updating artifact hash in state file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name

        try:
            update_artifact_hash("hash_test", tmp_path, "test_file")
            state = load_state_file("hash_test")
            
            assert "test_file" in state["artifact_hashes"]
            assert len(state["artifact_hashes"]["test_file"]) == 64  # SHA-256 length
        finally:
            os.unlink(tmp_path)


class TestFileHash:
    def test_compute_file_hash(self):
        """Test SHA-256 hash computation."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            content = b"test content for hashing"
            tmp.write(content)
            tmp_path = tmp.name

        try:
            hash_val = compute_file_hash(tmp_path)
            assert len(hash_val) == 64
            assert all(c in '0123456789abcdef' for c in hash_val)
        finally:
            os.unlink(tmp_path)

    def test_hash_determinism(self):
        """Test that same content produces same hash."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"same content")
            tmp_path1 = tmp.name

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"same content")
            tmp_path2 = tmp.name

        try:
            hash1 = compute_file_hash(tmp_path1)
            hash2 = compute_file_hash(tmp_path2)
            assert hash1 == hash2
        finally:
            os.unlink(tmp_path1)
            os.unlink(tmp_path2)


class TestCPUOnly:
    def test_ensure_cpu_only_sets_env(self):
        """Test that ensure_cpu_only sets CUDA_VISIBLE_DEVICES."""
        ensure_cpu_only()
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
