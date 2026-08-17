"""
Unit tests for code/analysis/network.py to ensure modularity Q is non-negative
and efficiency values are finite.

This test verifies the mathematical bounds of network metrics as required by
SC-003 (Modularity Q >= 0, Efficiency >= 0) and ensures no NaN/Inf values leak
into the results.
"""
import pytest
import math
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.network import (
    calculate_network_metrics,
    calculate_connectivity_matrix,
    extract_roi_timeseries,
    load_preprocessed_data
)
from code.config import Config


class TestNetworkMetricsBounds:
    """Test that network metrics respect mathematical bounds."""
    
    def test_modularity_non_negative(self):
        """Ensure modularity Q is always non-negative (SC-003)."""
        # Create a valid connectivity matrix
        matrix = [
            [1.0, 0.8, 0.1],
            [0.8, 1.0, 0.2],
            [0.1, 0.2, 1.0]
        ]
        
        metrics = calculate_network_metrics(matrix)
        
        assert "modularity" in metrics
        assert metrics["modularity"] >= 0.0, f"Modularity {metrics['modularity']} is negative"
    
    def test_global_efficiency_finite(self):
        """Ensure global efficiency is finite (not NaN or Inf)."""
        matrix = [
            [1.0, 0.5, 0.3],
            [0.5, 1.0, 0.4],
            [0.3, 0.4, 1.0]
        ]
        
        metrics = calculate_network_metrics(matrix)
        
        assert "global_efficiency" in metrics
        value = metrics["global_efficiency"]
        assert math.isfinite(value), f"Global efficiency {value} is not finite"
    
    def test_local_efficiency_finite(self):
        """Ensure local efficiency is finite (not NaN or Inf)."""
        matrix = [
            [1.0, 0.6, 0.2],
            [0.6, 1.0, 0.5],
            [0.2, 0.5, 1.0]
        ]
        
        metrics = calculate_network_metrics(matrix)
        
        assert "local_efficiency" in metrics
        value = metrics["local_efficiency"]
        assert math.isfinite(value), f"Local efficiency {value} is not finite"
    
    def test_empty_matrix_returns_defaults(self):
        """Ensure empty matrix returns valid default metrics."""
        metrics = calculate_network_metrics([])
        
        assert metrics["modularity"] == 0.0
        assert metrics["global_efficiency"] == 0.0
        assert metrics["local_efficiency"] == 0.0
    
    def test_single_node_matrix(self):
        """Test behavior with a single node (edge case)."""
        matrix = [[1.0]]
        
        metrics = calculate_network_metrics(matrix)
        
        # Should handle gracefully without crashing
        assert math.isfinite(metrics["modularity"])
        assert math.isfinite(metrics["global_efficiency"])
        assert math.isfinite(metrics["local_efficiency"])
    
    def test_invalid_values_filtered(self):
        """Ensure NaN/Inf in input matrix doesn't propagate to output."""
        # Matrix with NaN values
        matrix = [
            [1.0, float('nan'), 0.1],
            [float('nan'), 1.0, 0.2],
            [0.1, 0.2, 1.0]
        ]
        
        # Should not crash and should return finite values
        metrics = calculate_network_metrics(matrix)
        
        assert math.isfinite(metrics["modularity"])
        assert math.isfinite(metrics["global_efficiency"])
        assert math.isfinite(metrics["local_efficiency"])
    
    def test_efficiency_non_negative(self):
        """Ensure efficiency values are non-negative (SC-003)."""
        matrix = [
            [1.0, 0.9, 0.8],
            [0.9, 1.0, 0.7],
            [0.8, 0.7, 1.0]
        ]
        
        metrics = calculate_network_metrics(matrix)
        
        assert metrics["global_efficiency"] >= 0.0
        assert metrics["local_efficiency"] >= 0.0
    
    def test_connectivity_matrix_bounds(self):
        """Ensure correlation matrix values are in [-1, 1]."""
        timeseries = [[1.0, 2.0, 3.0], [2.0, 3.0, 4.0]]
        matrix = calculate_connectivity_matrix(timeseries)
        
        for row in matrix:
            for val in row:
                assert -1.0 <= val <= 1.0, f"Correlation value {val} out of bounds"
    
    def test_roi_timeseries_extraction(self):
        """Test ROI timeseries extraction from subject data."""
        subject_data = {
            "subject_id": "sub-001",
            "timeseries": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        }
        
        timeseries = extract_roi_timeseries(subject_data, atlas="aal")
        
        assert len(timeseries) == 2
        assert len(timeseries[0]) == 3
        assert timeseries[0] == [0.1, 0.2, 0.3]
    
    def test_missing_timeseries_handling(self):
        """Test behavior when timeseries is missing."""
        subject_data = {"subject_id": "sub-002"}
        
        timeseries = extract_roi_timeseries(subject_data)
        
        assert timeseries == []
    
    def test_load_preprocessed_data_structure(self):
        """Test that load_preprocessed_data returns correct structure."""
        config = Config()
        
        subjects = load_preprocessed_data(config)
        
        assert isinstance(subjects, list)
        if len(subjects) > 0:
            assert "subject_id" in subjects[0]
            assert "timeseries" in subjects[0]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])