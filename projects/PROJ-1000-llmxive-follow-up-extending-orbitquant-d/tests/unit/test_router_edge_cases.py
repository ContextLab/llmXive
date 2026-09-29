"""
Unit tests for edge cases in the entropy router.
Tests scenarios: entropy out-of-range, proxy failure, missing matrices, and boundary conditions.
"""
import pytest
import numpy as np
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.router import EntropyRouter
from code.config import Config

class TestEntropyRouterEdgeCases:
    """Test EntropyRouter with edge cases and failure scenarios."""

    @pytest.fixture
    def mock_config(self):
        """Provide a mock configuration."""
        config = Mock(spec=Config)
        config.router_entropy_min = -2.0
        config.router_entropy_max = 2.0
        config.router_fallback_index = 7
        config.clustering_report_path = "data/processed/clustering_report.json"
        return config

    @pytest.fixture
    def temp_clustering_report(self):
        """Create a temporary clustering report file for testing."""
        report_data = {
            "layers": ["layer1", "layer2"],
            "subsets": ["subset1", "subset2"],
            "boundaries": [-1.5, -0.5, 0.5, 1.5],
            "matrices": {
                "layer1": [np.eye(8).tolist() for _ in range(5)],
                "layer2": [np.eye(8).tolist() for _ in range(5)]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(report_data, f)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def router(self, mock_config, temp_clustering_report):
        """Create an EntropyRouter instance."""
        mock_config.clustering_report_path = temp_clustering_report
        router = EntropyRouter(mock_config)
        return router

    def test_entropy_below_minimum(self, router):
        """Test routing when entropy is below the minimum boundary."""
        # Entropy well below the minimum boundary
        entropy = -10.0
        matrix_index = router.get_matrix_index(entropy)
        
        # Should clamp to the first index (0)
        assert matrix_index == 0

    def test_entropy_above_maximum(self, router):
        """Test routing when entropy is above the maximum boundary."""
        # Entropy well above the maximum boundary
        entropy = 10.0
        matrix_index = router.get_matrix_index(entropy)
        
        # Should clamp to the last index
        expected_max_index = len(router.boundaries)
        assert matrix_index == expected_max_index

    def test_entropy_at_boundary_exact(self, router):
        """Test routing when entropy is exactly at a boundary."""
        # Test at each boundary
        for i, boundary in enumerate(router.boundaries):
            matrix_index = router.get_matrix_index(boundary)
            # Should map to the correct segment
            assert 0 <= matrix_index <= len(router.boundaries)

    def test_entropy_very_close_to_boundary(self, router):
        """Test routing with entropy very close to boundaries (floating point edge case)."""
        epsilon = 1e-10
        for i, boundary in enumerate(router.boundaries):
            # Just below boundary
            entropy_below = boundary - epsilon
            idx_below = router.get_matrix_index(entropy_below)
            
            # Just above boundary
            entropy_above = boundary + epsilon
            idx_above = router.get_matrix_index(entropy_above)
            
            # Should be in adjacent or same bin depending on implementation
            assert abs(idx_above - idx_below) <= 1

    def test_negative_entropy_values(self, router):
        """Test with negative entropy values (possible with certain entropy definitions)."""
        negative_entropies = [-5.0, -2.5, -0.1]
        for entropy in negative_entropies:
            matrix_index = router.get_matrix_index(entropy)
            assert 0 <= matrix_index <= len(router.boundaries)

    def test_very_large_positive_entropy(self, router):
        """Test with extremely large positive entropy values."""
        large_entropy = 1e6
        matrix_index = router.get_matrix_index(large_entropy)
        # Should clamp to maximum
        expected_max = len(router.boundaries)
        assert matrix_index == expected_max

    def test_nan_entropy_input(self, router):
        """Test behavior when entropy is NaN."""
        entropy = float('nan')
        # Should either raise or return fallback
        try:
            matrix_index = router.get_matrix_index(entropy)
            # If it returns, it should be the fallback index
            assert matrix_index == router.fallback_index
        except (ValueError, TypeError):
            # Raising an error is also acceptable
            pass

    def test_inf_entropy_input(self, router):
        """Test behavior when entropy is infinity."""
        for inf_val in [float('inf'), float('-inf')]:
            try:
                matrix_index = router.get_matrix_index(inf_val)
                # Should clamp to boundaries
                assert 0 <= matrix_index <= len(router.boundaries)
            except (ValueError, TypeError):
                # Raising an error is also acceptable
                pass

    def test_missing_clustering_report(self, mock_config):
        """Test behavior when clustering report file is missing."""
        mock_config.clustering_report_path = "nonexistent/path/report.json"
        
        with pytest.raises(FileNotFoundError):
            EntropyRouter(mock_config)

    def test_invalid_clustering_report_format(self, mock_config):
        """Test behavior when clustering report has invalid format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"invalid": "data"}, f)
            temp_path = f.name
        
        mock_config.clustering_report_path = temp_path
        
        try:
            with pytest.raises((KeyError, ValueError, TypeError)):
                EntropyRouter(mock_config)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_empty_boundaries(self, mock_config):
        """Test behavior when boundaries list is empty."""
        report_data = {
            "layers": ["layer1"],
            "subsets": ["subset1"],
            "boundaries": [],
            "matrices": {"layer1": []}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(report_data, f)
            temp_path = f.name
        
        mock_config.clustering_report_path = temp_path
        
        try:
            router = EntropyRouter(mock_config)
            # With no boundaries, should return fallback or 0
            matrix_index = router.get_matrix_index(0.5)
            assert matrix_index in [0, router.fallback_index]
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_single_boundary(self, mock_config):
        """Test behavior with only one boundary (two bins)."""
        report_data = {
            "layers": ["layer1"],
            "subsets": ["subset1"],
            "boundaries": [0.0],
            "matrices": {"layer1": [np.eye(4).tolist(), np.eye(4).tolist()]}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(report_data, f)
            temp_path = f.name
        
        mock_config.clustering_report_path = temp_path
        
        try:
            router = EntropyRouter(mock_config)
            # Should have 2 bins
            assert len(router.boundaries) == 1
            
            # Below boundary
            idx_below = router.get_matrix_index(-1.0)
            assert idx_below == 0
            
            # Above boundary
            idx_above = router.get_matrix_index(1.0)
            assert idx_above == 1
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_fallback_index_out_of_range(self, mock_config):
        """Test behavior when fallback index is out of valid range."""
        report_data = {
            "layers": ["layer1"],
            "subsets": ["subset1"],
            "boundaries": [0.0, 1.0],
            "matrices": {"layer1": [np.eye(4).tolist()]}  # Only 1 matrix
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(report_data, f)
            temp_path = f.name
        
        mock_config.clustering_report_path = temp_path
        mock_config.router_fallback_index = 99  # Out of range
        
        try:
            router = EntropyRouter(mock_config)
            # Should clamp fallback to valid range
            assert router.fallback_index < len(router.matrices["layer1"])
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_multiple_layers_missing_matrices(self, mock_config, temp_clustering_report):
        """Test behavior when some layers are missing matrices."""
        # Modify the temp file to have missing matrices
        with open(temp_clustering_report, 'r') as f:
            data = json.load(f)
        
        # Remove matrices for one layer
        if "layer2" in data["matrices"]:
            del data["matrices"]["layer2"]
        
        with open(temp_clustering_report, 'w') as f:
            json.dump(data, f)
        
        router = EntropyRouter(mock_config)
        # Should handle missing layers gracefully
        # (either skip or use fallback)
        assert router is not None

    def test_router_with_no_entropy_range(self, mock_config):
        """Test behavior when entropy range is not configured."""
        mock_config.router_entropy_min = None
        mock_config.router_entropy_max = None
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "layers": ["layer1"],
                "subsets": ["subset1"],
                "boundaries": [-1.0, 0.0, 1.0],
                "matrices": {"layer1": [np.eye(4).tolist() for _ in range(4)]}
            }, f)
            temp_path = f.name
        
        mock_config.clustering_report_path = temp_path
        
        try:
            router = EntropyRouter(mock_config)
            # Should still work, using boundaries from report
            idx = router.get_matrix_index(0.5)
            assert 0 <= idx <= 3
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_batch_entropy_values(self, router):
        """Test routing with a batch of entropy values."""
        entropies = [-10.0, -2.0, -0.5, 0.0, 0.5, 2.0, 10.0]
        indices = [router.get_matrix_index(e) for e in entropies]
        
        # Should be monotonically non-decreasing
        for i in range(1, len(indices)):
            assert indices[i] >= indices[i-1]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
