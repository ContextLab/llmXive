"""
Unit tests for code/utils.py
"""
import pytest
import tempfile
import os
from pathlib import Path

from code.utils import (
    seed_all,
    hash_artifact,
    SAMPLE_SIZE,
    CONVERGENCE_THRESHOLD,
    MAX_EPOCHS,
)


class TestConstants:
    """Tests for module constants."""

    def test_sample_size_is_110(self):
        """Verify SAMPLE_SIZE matches the specification (N=110)."""
        assert SAMPLE_SIZE == 110, f"Expected SAMPLE_SIZE to be 110, got {SAMPLE_SIZE}"

    def test_convergence_threshold_is_090(self):
        """Verify CONVERGENCE_THRESHOLD matches the specification (0.90)."""
        assert CONVERGENCE_THRESHOLD == 0.90, f"Expected 0.90, got {CONVERGENCE_THRESHOLD}"

    def test_max_epochs_is_1000(self):
        """Verify MAX_EPOCHS matches the specification (1000)."""
        assert MAX_EPOCHS == 1000, f"Expected 1000, got {MAX_EPOCHS}"


class TestSeedAll:
    """Tests for the seed_all function."""

    def test_seed_all_runs_without_error(self):
        """Verify seed_all executes without raising exceptions."""
        # Should not raise even if torch/numpy are missing (handled internally)
        try:
            seed_all(42)
        except Exception as e:
            pytest.fail(f"seed_all raised an unexpected exception: {e}")

    def test_seed_all_sets_random(self):
        """Verify seed_all affects the random module."""
        import random
        seed_all(12345)
        val1 = random.random()
        
        seed_all(12345)
        val2 = random.random()
        
        assert val1 == val2, "Seeding with the same value should produce the same random sequence"


class TestHashArtifact:
    """Tests for the hash_artifact function."""

    def test_hash_artifact_computes_correct_hash(self):
        """Verify hash_artifact computes a valid SHA-256 hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            hash_val = hash_artifact(temp_path)
            assert len(hash_val) == 64, "SHA-256 hash should be 64 hex characters"
            assert all(c in '0123456789abcdef' for c in hash_val), "Hash should be hexadecimal"
        finally:
            os.unlink(temp_path)

    def test_hash_artifact_raises_on_missing_file(self):
        """Verify hash_artifact raises FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            hash_artifact("/nonexistent/path/to/file.txt")

    def test_hash_determinism(self):
        """Verify the same file produces the same hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("deterministic test")
            temp_path = f.name

        try:
            hash1 = hash_artifact(temp_path)
            hash2 = hash_artifact(temp_path)
            assert hash1 == hash2, "Hashing the same file twice should yield identical results"
        finally:
            os.unlink(temp_path)
