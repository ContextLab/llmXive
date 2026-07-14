"""
Contract tests verifying the interface between Simulation and Analysis.
"""
import numpy as np
import pandas as pd
import pytest

from code.analyzer import aggregate_results, compute_bootstrap_ci


class TestSimAnalyzeContract:
    """Tests ensuring simulation output matches analyzer input expectations."""

    def test_aggregate_accepts_dataframe(self):
        """Verify analyzer accepts standard simulation result DataFrame."""
        # Create mock simulation results matching expected schema
        mock_data = pd.DataFrame({
            'sample_size': [10, 10, 20, 20],
            'distribution': ['normal', 'normal', 'uniform', 'uniform'],
            'test_type': ['t-test', 't-test', 't-test', 't-test'],
            'effect_size': [0.0, 0.0, 0.0, 0.0],
            'reject_null': [False, True, False, True],
            'p_value': [0.1, 0.01, 0.2, 0.02]
        })
        
        result = aggregate_results(mock_data)
        
        assert isinstance(result, pd.DataFrame)
        assert 'reject_rate' in result.columns
        assert 'n' in result.columns

    def test_bootstrap_ci_computation(self):
        """Verify bootstrap CI calculation works on aggregated rates."""
        rates = [0.04, 0.05, 0.06, 0.05, 0.04]
        ci_low, ci_high = compute_bootstrap_ci(rates, n_boot=100)
        
        assert ci_low <= ci_high
        assert 0.0 <= ci_low <= 1.0
        assert 0.0 <= ci_high <= 1.0