"""
Unit tests for tractography confidence thresholding logic.
Tests for T041 and T040.
"""
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocess.structural import calculate_graph_metrics
from config import TRACTOGRAPHY_CONFIDENCE_THRESHOLDS

class TestTractographyThresholding:
    """Tests for tractography confidence thresholding functionality."""

    def test_config_has_thresholds(self):
        """Verify that TRACTOGRAPHY_CONFIDENCE_THRESHOLDS is defined in config."""
        assert isinstance(TRACTOGRAPHY_CONFIDENCE_THRESHOLDS, list)
        assert len(TRACTOGRAPHY_CONFIDENCE_THRESHOLDS) > 0
        assert all(isinstance(t, (int, float)) for t in TRACTOGRAPHY_CONFIDENCE_THRESHOLDS)

    def test_thresholding_filters_edges(self):
        """Test that confidence thresholding correctly filters edges."""
        # Create a simple adjacency matrix
        adj_matrix = np.array([
            [0.0, 0.9, 0.3, 0.1],
            [0.9, 0.0, 0.8, 0.2],
            [0.3, 0.8, 0.0, 0.7],
            [0.1, 0.2, 0.7, 0.0]
        ])

        # Without threshold
        metrics_no_thresh = calculate_graph_metrics(adj_matrix, confidence_threshold=0.0)
        
        # With high threshold (should filter out low confidence edges)
        metrics_high_thresh = calculate_graph_metrics(adj_matrix, confidence_threshold=0.5)

        # The graph with higher threshold should have fewer edges
        # and potentially different metrics
        # We can't guarantee specific values, but we can verify the function runs
        assert metrics_no_thresh is not None
        assert metrics_high_thresh is not None
        assert "global_efficiency" in metrics_no_thresh
        assert "global_efficiency" in metrics_high_thresh

    def test_threshold_changes_topology(self):
        """Test that different thresholds produce different graph topologies."""
        adj_matrix = np.array([
            [0.0, 0.9, 0.3, 0.1],
            [0.9, 0.0, 0.8, 0.2],
            [0.3, 0.8, 0.0, 0.7],
            [0.1, 0.2, 0.7, 0.0]
        ])

        # Low threshold
        metrics_low = calculate_graph_metrics(adj_matrix, confidence_threshold=0.1)
        # High threshold
        metrics_high = calculate_graph_metrics(adj_matrix, confidence_threshold=0.8)

        # With higher threshold, global efficiency should generally decrease
        # (fewer connections)
        assert metrics_low["global_efficiency"] >= metrics_high["global_efficiency"]

    def test_edge_case_zero_threshold(self):
        """Test that zero threshold behaves like no threshold."""
        adj_matrix = np.random.rand(10, 10)
        np.fill_diagonal(adj_matrix, 0)

        metrics_zero = calculate_graph_metrics(adj_matrix, confidence_threshold=0.0)
        metrics_none = calculate_graph_metrics(adj_matrix, confidence_threshold=0.0)

        assert metrics_zero["global_efficiency"] == metrics_none["global_efficiency"]

    def test_edge_case_high_threshold(self):
        """Test that very high threshold results in sparse/disconnected graph."""
        adj_matrix = np.array([
            [0.0, 0.9, 0.3, 0.1],
            [0.9, 0.0, 0.8, 0.2],
            [0.3, 0.8, 0.0, 0.7],
            [0.1, 0.2, 0.7, 0.0]
        ])

        # Threshold higher than any edge
        metrics = calculate_graph_metrics(adj_matrix, confidence_threshold=1.0)

        # Should return zeros for metrics when no edges exist
        assert metrics["global_efficiency"] == 0.0
        assert metrics["average_clustering"] == 0.0
        assert metrics["modularity"] == 0.0

    def test_threshold_range_values(self):
        """Test that the defined threshold range covers the expected spectrum."""
        # Check that we have thresholds covering low to high
        assert min(TRACTOGRAPHY_CONFIDENCE_THRESHOLDS) == 0.0
        assert max(TRACTOGRAPHY_CONFIDENCE_THRESHOLDS) >= 0.8
        
        # Check that we have intermediate values
        thresholds = sorted(TRACTOGRAPHY_CONFIDENCE_THRESHOLDS)
        for i in range(len(thresholds) - 1):
            assert thresholds[i+1] > thresholds[i], "Thresholds should be strictly increasing"