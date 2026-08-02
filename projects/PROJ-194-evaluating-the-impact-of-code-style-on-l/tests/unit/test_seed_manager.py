"""
Unit tests for code/transform/seed_manager.py (T006).
Verifies Constitution Principle VI: Reproducibility.
"""
import os
import json
import hashlib
import tempfile
import shutil
import pytest
from unittest.mock import patch

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from transform.seed_manager import (
    compute_mapping_hash,
    log_transform_seed,
    get_seed_entry,
    verify_reproducibility,
    _ensure_data_dir,
    SEED_LOG_PATH
)


class TestComputeMappingHash:
    """Tests for compute_mapping_hash function."""

    def test_hash_deterministic(self):
        """Hash should be the same for the same dictionary."""
        mapping = {"a": "1", "b": "2"}
        hash1 = compute_mapping_hash(mapping)
        hash2 = compute_mapping_hash(mapping)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_hash_order_independent(self):
        """Hash should be the same regardless of dict insertion order."""
        mapping1 = {"a": "1", "b": "2"}
        mapping2 = {"b": "2", "a": "1"}
        assert compute_mapping_hash(mapping1) == compute_mapping_hash(mapping2)

    def test_hash_different_content(self):
        """Hash should differ for different content."""
        mapping1 = {"a": "1"}
        mapping2 = {"a": "2"}
        assert compute_mapping_hash(mapping1) != compute_mapping_hash(mapping2)

    def test_empty_mapping(self):
        """Hash for empty dict should be valid."""
        h = compute_mapping_hash({})
        assert len(h) == 64


class TestLogTransformSeed:
    """Tests for log_transform_seed function."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_data_dir = "data"
        
        # Mock the DATA_DIR and SEED_LOG_PATH
        with patch('transform.seed_manager.DATA_DIR', self.temp_dir):
            with patch('transform.seed_manager.SEED_LOG_PATH', os.path.join(self.temp_dir, "transform_seeds.jsonl")):
                yield
        
        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_creates_file(self):
        """Logging should create the JSONL file."""
        log_transform_seed(42, "test_type", {})
        log_path = os.path.join(self.temp_dir, "transform_seeds.jsonl")
        assert os.path.exists(log_path)

    def test_log_contains_seed(self):
        """Log entry should contain the correct seed."""
        seed_val = 12345
        log_transform_seed(seed_val, "test_type", {})
        
        log_path = os.path.join(self.temp_dir, "transform_seeds.jsonl")
        with open(log_path, 'r') as f:
            entry = json.loads(f.readline())
        
        assert entry["transform_seed"] == seed_val

    def test_log_contains_hash(self):
        """Log entry should contain the mapping hash."""
        mapping = {"x": "y"}
        expected_hash = compute_mapping_hash(mapping)
        
        log_transform_seed(42, "test_type", mapping)
        
        log_path = os.path.join(self.temp_dir, "transform_seeds.jsonl")
        with open(log_path, 'r') as f:
            entry = json.loads(f.readline())
        
        assert entry["identifier_mapping_hash"] == expected_hash

    def test_log_no_hash_when_none(self):
        """Log entry should have null hash when mapping is None."""
        log_transform_seed(42, "test_type", None)
        
        log_path = os.path.join(self.temp_dir, "transform_seeds.jsonl")
        with open(log_path, 'r') as f:
            entry = json.loads(f.readline())
        
        assert entry["identifier_mapping_hash"] is None

    def test_log_invalid_seed_raises(self):
        """Logging with non-integer seed should raise ValueError."""
        with pytest.raises(ValueError):
            log_transform_seed("not_an_int", "test_type", {})

    def test_log_appends(self):
        """Multiple logs should append to the file."""
        log_transform_seed(1, "type1", {})
        log_transform_seed(2, "type2", {})
        
        log_path = os.path.join(self.temp_dir, "transform_seeds.jsonl")
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 2


class TestGetSeedEntry:
    """Tests for get_seed_entry function."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        self.temp_dir = tempfile.mkdtemp()
        
        with patch('transform.seed_manager.DATA_DIR', self.temp_dir):
            with patch('transform.seed_manager.SEED_LOG_PATH', os.path.join(self.temp_dir, "transform_seeds.jsonl")):
                # Pre-populate log
                log_transform_seed(100, "type_a", {"a": "b"})
                log_transform_seed(200, "type_b", {"c": "d"})
                yield
        
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_by_seed(self):
        """Should retrieve entry by seed."""
        entry = get_seed_entry(100)
        assert entry is not None
        assert entry["transform_seed"] == 100

    def test_get_by_seed_and_type(self):
        """Should retrieve entry by seed and type."""
        entry = get_seed_entry(100, "type_a")
        assert entry is not None
        assert entry["variant_type"] == "type_a"

    def test_get_wrong_type_returns_none(self):
        """Should return None if type doesn't match."""
        entry = get_seed_entry(100, "wrong_type")
        assert entry is None

    def test_get_nonexistent_seed_returns_none(self):
        """Should return None for nonexistent seed."""
        entry = get_seed_entry(999)
        assert entry is None

    def test_get_nonexistent_file_returns_none(self):
        """Should return None if log file doesn't exist."""
        with patch('transform.seed_manager.SEED_LOG_PATH', "/nonexistent/path.jsonl"):
            entry = get_seed_entry(1)
            assert entry is None


class TestVerifyReproducibility:
    """Tests for verify_reproducibility function."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        self.temp_dir = tempfile.mkdtemp()
        
        with patch('transform.seed_manager.DATA_DIR', self.temp_dir):
            with patch('transform.seed_manager.SEED_LOG_PATH', os.path.join(self.temp_dir, "transform_seeds.jsonl")):
                # Pre-populate log
                log_transform_seed(555, "verify_test", {"key1": "val1", "key2": "val2"})
                yield
        
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_verify_success(self):
        """Should return True for correct seed and mapping."""
        mapping = {"key1": "val1", "key2": "val2"}
        result = verify_reproducibility(555, mapping, "verify_test")
        assert result is True

    def test_verify_wrong_mapping(self):
        """Should return False for different mapping."""
        mapping = {"key1": "different_val"}
        result = verify_reproducibility(555, mapping, "verify_test")
        assert result is False

    def test_verify_wrong_seed(self):
        """Should return False for different seed."""
        mapping = {"key1": "val1", "key2": "val2"}
        result = verify_reproducibility(999, mapping, "verify_test")
        assert result is False

    def test_verify_wrong_type(self):
        """Should return False for different type."""
        mapping = {"key1": "val1", "key2": "val2"}
        result = verify_reproducibility(555, mapping, "wrong_type")
        assert result is False