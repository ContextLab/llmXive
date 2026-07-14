"""
tests/unit/test_metrics_aggregation.py

Unit tests for the T022 aggregation logic in code/data/metrics.py.
"""
import numpy as np
import pytest
from code.data.metrics import aggregate_node_metrics

class TestAggregateNodeMetrics:
    """Tests for the aggregate_node_metrics function."""

    def test_aggregates_participation_coef_mean(self):
        """Verify that Participation Coefficient is averaged correctly."""
        input_metrics = {
            "participation_coef": np.array([0.1, 0.2, 0.3, 0.4]),
            "within_module_degree": np.array([1, 2, 3, 4])
        }
        result = aggregate_node_metrics(input_metrics)
        
        expected_mean_pc = 0.25  # (0.1+0.2+0.3+0.4)/4
        assert abs(result["mean_participation_coef"] - expected_mean_pc) < 1e-6

    def test_aggregates_within_module_degree_mean(self):
        """Verify that Within-Module Degree is averaged correctly."""
        input_metrics = {
            "participation_coef": np.array([0.1, 0.2, 0.3, 0.4]),
            "within_module_degree": np.array([10, 20, 30, 40])
        }
        result = aggregate_node_metrics(input_metrics)
        
        expected_mean_wmd = 25.0  # (10+20+30+40)/4
        assert abs(result["mean_within_module_degree"] - expected_mean_wmd) < 1e-6

    def test_handles_empty_arrays(self):
        """Verify behavior when node metrics are empty."""
        input_metrics = {
            "participation_coef": np.array([]),
            "within_module_degree": np.array([])
        }
        result = aggregate_node_metrics(input_metrics)
        
        assert result["mean_participation_coef"] == 0.0
        assert result["mean_within_module_degree"] == 0.0

    def test_handles_missing_keys(self):
        """Verify behavior when keys are missing from input dict."""
        input_metrics = {}
        result = aggregate_node_metrics(input_metrics)
        
        assert result["mean_participation_coef"] == 0.0
        assert result["mean_within_module_degree"] == 0.0

    def test_aggregates_single_node(self):
        """Verify aggregation works for a single node (edge case)."""
        input_metrics = {
            "participation_coef": np.array([0.5]),
            "within_module_degree": np.array([10.0])
        }
        result = aggregate_node_metrics(input_metrics)
        
        assert abs(result["mean_participation_coef"] - 0.5) < 1e-6
        assert abs(result["mean_within_module_degree"] - 10.0) < 1e-6