import json
import os
import tempfile
import numpy as np
import pytest

from generate_data import generate_correlated_data, write_dataset_metadata

class TestDatasetGeneration:
    """Unit tests for dataset generation and metadata writing."""

    def test_generate_correlated_data_shapes(self):
        """Test that generated data has correct dimensions."""
        n, p, rho, seed = 100, 50, 0.3, 42
        data, metadata = generate_correlated_data(n, p, rho, seed)

        assert data.shape == (n, p), f"Expected shape ({n}, {p}), got {data.shape}"
        assert metadata["n"] == n
        assert metadata["p"] == p
        assert metadata["rho"] == rho
        assert metadata["seed"] == seed

    def test_generate_correlated_data_distribution(self):
        """Test that generated data follows expected distribution properties."""
        n, p, rho, seed = 1000, 100, 0.0, 123
        data, _ = generate_correlated_data(n, p, rho, seed)

        # For rho=0, columns should be approximately uncorrelated
        corr_matrix = np.corrcoef(data.T)
        off_diag = corr_matrix[np.triu_indices(p, k=1)]
        assert np.abs(np.mean(off_diag)) < 0.1, "Columns should be approximately uncorrelated"

    def test_write_dataset_metadata_creates_file(self):
        """Test that metadata file is created with correct structure."""
        n, p, rho, seed = 50, 20, 0.1, 99
        data, metadata = generate_correlated_data(n, p, rho, seed)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_metadata.json")
            write_dataset_metadata(data, metadata, output_path)

            assert os.path.exists(output_path), "Output file should exist"

            with open(output_path, 'r') as f:
                loaded = json.load(f)

            assert "sha256" in loaded
            assert loaded["rho"] == rho
            assert loaded["n"] == n
            assert loaded["p"] == p
            assert loaded["seed"] == seed

    def test_write_dataset_metadata_hash_verification(self):
        """Test that SHA256 hash in metadata matches actual data hash."""
        n, p, rho, seed = 30, 10, 0.5, 777
        data, metadata = generate_correlated_data(n, p, rho, seed)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "hash_test.json")
            write_dataset_metadata(data, metadata, output_path)

            with open(output_path, 'r') as f:
                loaded = json.load(f)

            # Recompute hash
            computed_hash = np.sha256(data.tobytes()) if hasattr(np, 'sha256') else None
            import hashlib
            expected_hash = hashlib.sha256(data.tobytes()).hexdigest()

            assert loaded["sha256"] == expected_hash, "Hash mismatch"

    def test_write_dataset_metadata_directory_creation(self):
        """Test that nested directories are created automatically."""
        n, p, rho, seed = 20, 10, 0.0, 555
        data, metadata = generate_correlated_data(n, p, rho, seed)

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "synthetic", "deep", "nested", "test.json")
            write_dataset_metadata(data, metadata, nested_path)

            assert os.path.exists(nested_path), "Nested file should be created"
