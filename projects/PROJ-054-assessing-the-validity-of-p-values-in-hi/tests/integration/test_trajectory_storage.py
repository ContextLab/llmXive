"""
Integration test for p-value trajectory storage (T017).

This test verifies that:
1. The store_trajectories module can write trajectory files
2. The written files contain valid JSON with expected structure
3. The SHA-256 hash in the file matches the computed hash of p-values
4. Metadata is correctly stored when provided
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
import numpy as np

# Import the function under test
from code.store_trajectories import (
    write_trajectory_file,
    compute_trajectory_hash
)


class TestTrajectoryStorage:
    """Integration tests for trajectory file storage."""

    @pytest.fixture
    def temp_trajectory_dir(self):
        """Create a temporary directory for trajectory files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_write_trajectory_basic(self, temp_trajectory_dir):
        """Test basic trajectory file writing."""
        seed = 12345
        pvalues = [0.01, 0.5, 0.9, 0.3, 0.7]

        file_path = write_trajectory_file(
            trajectory_dir=temp_trajectory_dir,
            seed=seed,
            pvalues=pvalues,
            metadata=None
        )

        # Verify file exists
        assert file_path.exists(), "Trajectory file was not created"
        assert file_path.name == f"{seed}.json", "Filename does not match seed"

        # Verify JSON structure
        with open(file_path, 'r') as f:
            data = json.load(f)

        assert "seed" in data, "Missing 'seed' field"
        assert "pvalues" in data, "Missing 'pvalues' field"
        assert "n_pvalues" in data, "Missing 'n_pvalues' field"
        assert "sha256" in data, "Missing 'sha256' field"

        assert data["seed"] == seed
        assert data["pvalues"] == pvalues
        assert data["n_pvalues"] == len(pvalues)

    def test_trajectory_hash_computation(self, temp_trajectory_dir):
        """Test that the SHA-256 hash is correctly computed and stored."""
        seed = 67890
        pvalues = [0.123456789, 0.987654321, 0.555555555]

        file_path = write_trajectory_file(
            trajectory_dir=temp_trajectory_dir,
            seed=seed,
            pvalues=pvalues
        )

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Compute expected hash
        expected_hash = compute_trajectory_hash(pvalues)

        assert data["sha256"] == expected_hash, \
            f"Hash mismatch: stored={data['sha256']}, expected={expected_hash}"

    def test_write_trajectory_with_metadata(self, temp_trajectory_dir):
        """Test trajectory writing with metadata."""
        seed = 11111
        pvalues = [0.2, 0.4, 0.6, 0.8]
        metadata = {
            "n": 100,
            "p": 50,
            "rho": 0.3,
            "distribution_type": "normal",
            "iteration": 5
        }

        file_path = write_trajectory_file(
            trajectory_dir=temp_trajectory_dir,
            seed=seed,
            pvalues=pvalues,
            metadata=metadata
        )

        with open(file_path, 'r') as f:
            data = json.load(f)

        assert "metadata" in data, "Missing 'metadata' field"
        assert data["metadata"]["n"] == 100
        assert data["metadata"]["p"] == 50
        assert data["metadata"]["rho"] == 0.3
        assert data["metadata"]["distribution_type"] == "normal"
        assert data["metadata"]["iteration"] == 5

    def test_large_trajectory_storage(self, temp_trajectory_dir):
        """Test storage of a large number of p-values (simulating high-dimensional data)."""
        seed = 99999
        # Simulate p = 1000 features
        pvalues = np.random.uniform(0, 1, size=1000).tolist()

        file_path = write_trajectory_file(
            trajectory_dir=temp_trajectory_dir,
            seed=seed,
            pvalues=pvalues
        )

        with open(file_path, 'r') as f:
            data = json.load(f)

        assert len(data["pvalues"]) == 1000, "Not all p-values were stored"
        assert data["n_pvalues"] == 1000

    def test_directory_creation(self, temp_trajectory_dir):
        """Test that the function creates the directory if it doesn't exist."""
        # Use a subdirectory that doesn't exist yet
        new_dir = temp_trajectory_dir / "new_subdir" / "nested"

        seed = 54321
        pvalues = [0.5, 0.5, 0.5]

        file_path = write_trajectory_file(
            trajectory_dir=new_dir,
            seed=seed,
            pvalues=pvalues
        )

        assert new_dir.exists(), "Directory was not created"
        assert file_path.exists(), "File was not created in new directory"

    def test_overwrite_existing_file(self, temp_trajectory_dir):
        """Test that writing with the same seed overwrites the existing file."""
        seed = 77777
        pvalues1 = [0.1, 0.2, 0.3]
        pvalues2 = [0.9, 0.8, 0.7]

        # Write first trajectory
        file_path = write_trajectory_file(
            trajectory_dir=temp_trajectory_dir,
            seed=seed,
            pvalues=pvalues1
        )

        # Write second trajectory with same seed
        file_path = write_trajectory_file(
            trajectory_dir=temp_trajectory_dir,
            seed=seed,
            pvalues=pvalues2
        )

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Should have the second set of p-values
        assert data["pvalues"] == pvalues2, "File was not overwritten correctly"

    def test_empty_pvalues_list(self, temp_trajectory_dir):
        """Test behavior with an empty p-values list."""
        seed = 0
        pvalues = []

        file_path = write_trajectory_file(
            trajectory_dir=temp_trajectory_dir,
            seed=seed,
            pvalues=pvalues
        )

        with open(file_path, 'r') as f:
            data = json.load(f)

        assert data["pvalues"] == []
        assert data["n_pvalues"] == 0

    def test_pvalue_precision_preservation(self, temp_trajectory_dir):
        """Test that high-precision p-values are preserved."""
        seed = 24680
        pvalues = [
            0.0000000001,
            0.9999999999,
            0.123456789012345
        ]

        file_path = write_trajectory_file(
            trajectory_dir=temp_trajectory_dir,
            seed=seed,
            pvalues=pvalues
        )

        with open(file_path, 'r') as f:
            data = json.load(f)

        # JSON preserves float precision
        assert data["pvalues"][0] == pvalues[0]
        assert data["pvalues"][1] == pvalues[1]
        assert data["pvalues"][2] == pvalues[2]