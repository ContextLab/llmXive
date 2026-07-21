"""
Tests for statistical_reference module (Task T010b).
"""
import json
import os
import tempfile
import pytest
import numpy as np

# Add code directory to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from statistical_reference import (
    load_physics_states,
    extract_state_vectors,
    compute_statistics,
    save_reference_stats,
    compute_reference_stats_from_file
)


class TestLoadPhysicsStates:
    def test_load_valid_file(self, tmp_path):
        """Test loading a valid physics states file."""
        test_data = [
            {"state_vector": [1.0, 2.0, 3.0]},
            {"state_vector": [4.0, 5.0, 6.0]}
        ]
        file_path = tmp_path / "test_states.json"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)

        result = load_physics_states(str(file_path))
        assert len(result) == 2
        assert result[0]["state_vector"] == [1.0, 2.0, 3.0]

    def test_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_physics_states("nonexistent.json")

    def test_invalid_format(self, tmp_path):
        """Test error handling for invalid JSON format."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            json.dump({"not": "a list"}, f)

        with pytest.raises(ValueError, match="Expected a list"):
            load_physics_states(str(file_path))


class TestExtractStateVectors:
    def test_extract_valid_vectors(self):
        """Test extraction of state vectors."""
        states = [
            {"state_vector": [1.0, 2.0, 3.0]},
            {"state_vector": [4.0, 5.0, 6.0]},
            {"state_vector": [7.0, 8.0, 9.0]}
        ]

        result = extract_state_vectors(states)
        assert result.shape == (3, 3)
        assert np.allclose(result[0], [1.0, 2.0, 3.0])

    def test_empty_list(self):
        """Test error handling for empty list."""
        with pytest.raises(ValueError, match="empty"):
            extract_state_vectors([])

    def test_missing_state_vector(self):
        """Test error handling for missing state_vector key."""
        states = [{"other_key": [1.0, 2.0, 3.0]}]
        with pytest.raises(ValueError, match="Missing 'state_vector'"):
            extract_state_vectors(states)


class TestComputeStatistics:
    def test_compute_mean_and_covariance(self):
        """Test computation of mean and covariance."""
        # Create data with known statistics
        np.random.seed(42)
        data = np.random.randn(100, 5)

        mean, cov = compute_statistics(data)

        assert mean.shape == (5,)
        assert cov.shape == (5, 5)
        assert np.allclose(mean, np.mean(data, axis=0))
        assert np.allclose(cov, np.cov(data, rowvar=False))

    def test_singular_covariance_regularization(self):
        """Test that singular covariance matrices are regularized."""
        # Create data with rank-deficient covariance
        data = np.ones((10, 3))  # All rows identical

        mean, cov = compute_statistics(data)

        # Covariance should be regularized and invertible
        assert cov.shape == (3, 3)
        # Check that regularization was applied (diagonal should be non-zero)
        assert np.any(np.diag(cov) > 0)

    def test_insufficient_samples(self):
        """Test error handling for insufficient samples."""
        data = np.array([[1.0, 2.0, 3.0]])
        with pytest.raises(ValueError, match="at least 2 samples"):
            compute_statistics(data)

    def test_wrong_dimensions(self):
        """Test error handling for wrong input dimensions."""
        with pytest.raises(ValueError, match="2D array"):
            compute_statistics(np.array([1.0, 2.0, 3.0]))


class TestSaveReferenceStats:
    def test_save_and_load(self, tmp_path):
        """Test saving and loading reference statistics."""
        mean = np.array([1.0, 2.0, 3.0])
        cov = np.array([[1.0, 0.1, 0.2], [0.1, 2.0, 0.3], [0.2, 0.3, 3.0]])

        output_path = tmp_path / "stats.json"
        save_reference_stats(mean, cov, str(output_path))

        assert output_path.exists()

        with open(output_path, 'r') as f:
            loaded = json.load(f)

        assert np.allclose(loaded["mean"], mean.tolist())
        assert np.allclose(loaded["covariance"], cov.tolist())
        assert loaded["n_samples"] == 3
        assert loaded["n_features"] == 3

class TestComputeReferenceStatsFromFile:
    def test_full_pipeline(self, tmp_path):
        """Test the full pipeline from file to statistics."""
        # Create input file
        input_path = tmp_path / "input_states.json"
        test_data = [
            {"state_vector": [1.0, 2.0, 3.0], "metadata": {}},
            {"state_vector": [2.0, 3.0, 4.0], "metadata": {}},
            {"state_vector": [3.0, 4.0, 5.0], "metadata": {}}
        ]
        with open(input_path, 'w') as f:
            json.dump(test_data, f)

        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        output_path = output_dir / "stats.json"

        # Run pipeline
        result = compute_reference_stats_from_file(str(input_path), str(output_path))

        # Verify output file exists
        assert output_path.exists()

        # Verify result
        assert result["n_samples"] == 3
        assert result["n_features"] == 3
        assert result["mean_shape"] == [3]
        assert result["covariance_shape"] == [3, 3]

        # Verify saved file contents
        with open(output_path, 'r') as f:
            saved = json.load(f)

        assert "mean" in saved
        assert "covariance" in saved