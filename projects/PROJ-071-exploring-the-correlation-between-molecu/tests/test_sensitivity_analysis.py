"""
Tests for Sensitivity Analysis (T022a)
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from sensitivity_analysis import bootstrap_correlation, run_sensitivity_analysis

class TestBootstrapCorrelation:
    def test_perfect_correlation(self):
        """Test with perfectly correlated data."""
        df = pd.DataFrame({
            'x': [1, 2, 3, 4, 5],
            'y': [2, 4, 6, 8, 10]
        })
        stats = bootstrap_correlation(df, 'x', 'y', n_bootstraps=100, random_state=42)
        
        assert stats['mean_r'] > 0.99
        assert stats['std_r'] < 0.05
        assert stats['stability_score'] > 0.9

    def test_no_correlation(self):
        """Test with uncorrelated random data."""
        rng = np.random.default_rng(123)
        df = pd.DataFrame({
            'x': rng.normal(0, 1, 100),
            'y': rng.normal(0, 1, 100)
        })
        stats = bootstrap_correlation(df, 'x', 'y', n_bootstraps=100, random_state=42)
        
        # Mean should be close to 0, but not exactly 0 due to sampling
        assert -0.3 < stats['mean_r'] < 0.3
        assert stats['stability_score'] < 0.5  # Low stability for noise

    def test_insufficient_data(self):
        """Test with too few samples."""
        df = pd.DataFrame({
            'x': [1, 2],
            'y': [3, 4]
        })
        # Should not crash, but might return low stats
        stats = bootstrap_correlation(df, 'x', 'y', n_bootstraps=10, random_state=42)
        assert 'mean_r' in stats

    def test_with_nan_values(self):
        """Test that NaN values are handled correctly."""
        df = pd.DataFrame({
            'x': [1, 2, np.nan, 4, 5],
            'y': [2, np.nan, 6, 8, 10]
        })
        stats = bootstrap_correlation(df, 'x', 'y', n_bootstraps=100, random_state=42)
        # Should not crash and should produce valid stats from valid pairs
        assert not np.isnan(stats['mean_r']) or 'note' in stats

class TestSensitivityAnalysisIntegration:
    def test_run_on_mock_data(self, tmp_path):
        """
        Run sensitivity analysis on a small mock dataset.
        Simulates the pipeline flow without needing real ingestion.
        """
        # Create a mock standard_subset.csv
        mock_data = {
            'smiles': ['CCO', 'CCCO', 'CCCCO', 'CCCCCO', 'CCCCCCO'] * 20,
            'mw': [46.07, 60.10, 74.12, 88.15, 102.17] * 20,
            'tpsa': [20.23, 20.23, 20.23, 20.23, 20.23] * 20,
            'rotatable_bonds': [0, 1, 2, 3, 4] * 20,
            'half_life': [10.0, 12.0, 14.0, 16.0, 18.0] * 20
        }
        df = pd.DataFrame(mock_data)
        input_path = tmp_path / "standard_subset.csv"
        df.to_csv(input_path, index=False)

        # Run analysis
        results = run_sensitivity_analysis(data_path=input_path, n_bootstraps=50, random_state=42)

        assert results['status'] == 'completed'
        assert 'mw' in results['results']
        assert 'rotatable_bonds' in results['results']
        
        # MW should be positively correlated with half_life in this mock
        mw_stats = results['results']['mw']
        assert mw_stats['mean_r'] > 0.5
