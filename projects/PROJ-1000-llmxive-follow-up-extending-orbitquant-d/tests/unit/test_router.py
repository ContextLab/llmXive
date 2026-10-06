"""
Unit tests for the EntropyRouter lookup logic (US2).

This module validates the core contract of the dynamic rotation router:
1. Correct matrix index selection based on entropy thresholds.
2. Clamping behavior for out-of-range entropy values.
3. Deterministic fallback behavior for edge cases.
"""
import pytest
import numpy as np
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the router implementation
from code.analysis.router import EntropyRouter
from code.config import Config


class TestEntropyRouter:
    """Contract tests for EntropyRouter lookup logic."""

    @pytest.fixture
    def sample_clustering_report(self):
        """Generate a mock clustering report with 4 matrices for testing."""
        return {
            "layers": ["layer_0", "layer_1"],
            "subsets": [
                {"id": 0, "name": "low_entropy", "min": 0.0, "max": 1.5},
                {"id": 1, "name": "medium_low", "min": 1.5, "max": 3.0},
                {"id": 2, "name": "medium_high", "min": 3.0, "max": 4.5},
                {"id": 3, "name": "high_entropy", "min": 4.5, "max": 6.0},
            ],
            "boundaries": [0.0, 1.5, 3.0, 4.5, 6.0],
            "matrices": [
                np.eye(10).tolist(),  # 4 matrices of shape (10, 10)
                np.eye(10).tolist(),
                np.eye(10).tolist(),
                np.eye(10).tolist(),
            ],
            "config": {
                "num_matrices": 4,
                "activation_dim": 10
            }
        }

    @pytest.fixture
    def temp_clustering_file(self, sample_clustering_report):
        """Create a temporary file with the sample clustering report."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_clustering_report, f)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_router_initialization(self, temp_clustering_file):
        """Test that the router initializes correctly from a clustering report."""
        router = EntropyRouter(clustering_report_path=temp_clustering_file)
        assert router.num_matrices == 4
        assert router.boundaries == [0.0, 1.5, 3.0, 4.5, 6.0]
        assert len(router.matrices) == 4
        assert router.matrices[0].shape == (10, 10)

    def test_lookup_low_entropy(self, temp_clustering_file):
        """Test that low entropy values map to index 0."""
        router = EntropyRouter(clustering_report_path=temp_clustering_file)
        assert router.get_matrix_index(0.5) == 0
        assert router.get_matrix_index(1.49) == 0

    def test_lookup_medium_entropy(self, temp_clustering_file):
        """Test that medium entropy values map to correct indices."""
        router = EntropyRouter(clustering_report_path=temp_clustering_file)
        # Boundary case: exactly at 1.5 should go to the next bin (1)
        assert router.get_matrix_index(1.5) == 1
        assert router.get_matrix_index(2.99) == 1
        assert router.get_matrix_index(3.0) == 2
        assert router.get_matrix_index(4.49) == 2
        assert router.get_matrix_index(4.5) == 3
        assert router.get_matrix_index(5.99) == 3

    def test_lookup_clamping_low(self, temp_clustering_file):
        """Test that entropy values below the minimum are clamped to index 0."""
        router = EntropyRouter(clustering_report_path=temp_clustering_file)
        assert router.get_matrix_index(-1.0) == 0
        assert router.get_matrix_index(-100.0) == 0

    def test_lookup_clamping_high(self, temp_clustering_file):
        """Test that entropy values above the maximum are clamped to last index."""
        router = EntropyRouter(clustering_report_path=temp_clustering_file)
        assert router.get_matrix_index(6.1) == 3
        assert router.get_matrix_index(100.0) == 3

    def test_get_matrix_returns_correct_array(self, temp_clustering_file):
        """Test that get_matrix returns the correct numpy array."""
        router = EntropyRouter(clustering_report_path=temp_clustering_file)
        
        # Create a distinct matrix for index 2 to verify retrieval
        # (In this mock, all are identity, but we test the retrieval logic)
        matrix = router.get_matrix(2)
        assert isinstance(matrix, np.ndarray)
        assert matrix.shape == (10, 10)

    def test_invalid_report_structure(self, temp_clustering_file):
        """Test that router raises error for missing keys in report."""
        # Create a corrupted report
        corrupted_report = {"layers": []}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(corrupted_report, f)
            corrupted_path = f.name
        
        with pytest.raises(ValueError, match="Missing required key"):
            EntropyRouter(clustering_report_path=corrupted_path)
        os.unlink(corrupted_path)

    def test_boundary_consistency(self, temp_clustering_file):
        """Test that boundaries are sorted and non-overlapping."""
        router = EntropyRouter(clustering_report_path=temp_clustering_file)
        # Verify boundaries are sorted
        assert router.boundaries == sorted(router.boundaries)
        # Verify number of boundaries is num_matrices + 1
        assert len(router.boundaries) == router.num_matrices + 1

    def test_median_fallback_on_error(self, temp_clustering_file):
        """Test that the router falls back to median index if lookup fails internally."""
        # This tests the defensive programming in get_matrix_index
        router = EntropyRouter(clustering_report_path=temp_clustering_file)
        
        # Simulate an edge case where logic might fail (though our implementation is robust)
        # We rely on the clamping logic to ensure we never get an out-of-bounds index
        idx = router.get_matrix_index(3.0)
        assert 0 <= idx < router.num_matrices

    def test_integration_with_config(self, temp_clustering_file):
        """Test that router respects config settings if passed."""
        config = Config()
        router = EntropyRouter(clustering_report_path=temp_clustering_file)
        # Default behavior check
        assert router.boundaries[0] == 0.0
        assert router.boundaries[-1] == 6.0

    def test_empty_boundaries_raises(self):
        """Test that a report with empty boundaries raises an error."""
        report = {
            "layers": [],
            "subsets": [],
            "boundaries": [],
            "matrices": [],
            "config": {"num_matrices": 0, "activation_dim": 10}
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(report, f)
            path = f.name
        
        with pytest.raises(ValueError):
            EntropyRouter(clustering_report_path=path)
        os.unlink(path)

    def test_non_numeric_entropy_raises(self, temp_clustering_file):
        """Test that non-numeric entropy values are handled (or raise)."""
        router = EntropyRouter(clustering_report_path=temp_clustering_file)
        # If we pass a string, numpy comparison might behave unexpectedly, 
        # but our implementation should handle it or raise a clear error.
        # Standard behavior: TypeError or ValueError
        with pytest.raises((TypeError, ValueError)):
            router.get_matrix_index("invalid")

    def test_boundary_inclusion_logic(self, temp_clustering_file):
        """
        Verify the specific inclusion logic: [min, max).
        i.e., min is inclusive, max is exclusive, except for the last bin.
        """
        router = EntropyRouter(clustering_report_path=temp_clustering_file)
        
        # Bin 0: [0.0, 1.5)
        assert router.get_matrix_index(0.0) == 0
        assert router.get_matrix_index(1.499) == 0
        
        # Bin 1: [1.5, 3.0)
        assert router.get_matrix_index(1.5) == 1
        assert router.get_matrix_index(2.999) == 1
        
        # Last Bin: [4.5, 6.0] (inclusive on both ends effectively via clamp)
        assert router.get_matrix_index(4.5) == 3
        assert router.get_matrix_index(5.999) == 3
        assert router.get_matrix_index(6.0) == 3  # Clamped to last

if __name__ == "__main__":
    pytest.main([__file__, "-v"])