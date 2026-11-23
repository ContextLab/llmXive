"""
Unit tests for the T014b execution script (run_t014b.py).

These tests verify the logic of the script without necessarily running the full pipeline
against large datasets, focusing on the verification and execution flow.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
import numpy as np

# Ensure we can import the script module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.run_t014b import verify_file_integrity

class TestRunT014b:
    """Test cases for T014b execution logic."""

    def test_verify_file_not_exists(self, tmp_path):
        """Test verification fails when file does not exist."""
        fake_path = tmp_path / "nonexistent.npz"
        assert not verify_file_integrity(fake_path)

    def test_verify_file_empty(self, tmp_path):
        """Test verification fails when file is empty."""
        fake_path = tmp_path / "empty.npz"
        fake_path.touch()
        assert not verify_file_integrity(fake_path)

    def test_verify_file_corrupted(self, tmp_path):
        """Test verification fails when file is not a valid npz."""
        fake_path = tmp_path / "corrupted.npz"
        with open(fake_path, 'w') as f:
            f.write("this is not a numpy file")
        assert not verify_file_integrity(fake_path)

    def test_verify_file_valid_minimal(self, tmp_path):
        """Test verification passes for a valid, minimal npz file."""
        fake_path = tmp_path / "valid.npz"
        
        # Create a minimal valid npz with required keys
        data = {
            'vectors': np.array([[1.0, 2.0], [3.0, 4.0]]),
            'metadata': np.array(['task1', 'task2'])
        }
        np.savez(fake_path, **data)
        
        assert verify_file_integrity(fake_path)

    def test_verify_file_missing_vectors_key(self, tmp_path):
        """Test verification fails if 'vectors' key is missing."""
        fake_path = tmp_path / "missing_vectors.npz"
        data = {'metadata': np.array(['task1'])}
        np.savez(fake_path, **data)
        assert not verify_file_integrity(fake_path)

    def test_verify_file_empty_vectors(self, tmp_path):
        """Test verification fails if 'vectors' array is empty."""
        fake_path = tmp_path / "empty_vectors.npz"
        data = {
            'vectors': np.array([]),
            'metadata': np.array([])
        }
        np.savez(fake_path, **data)
        assert not verify_file_integrity(fake_path)