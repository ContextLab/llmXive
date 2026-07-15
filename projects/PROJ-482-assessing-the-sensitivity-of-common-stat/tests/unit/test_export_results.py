"""
Unit tests for the export_results module.
"""
import os
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Mock imports to avoid dependency issues if modules are not fully ready
from code.analyzer import load_simulation_results, aggregate_results, compute_bootstrap_ci
from code.visualizer import generate_all_plots

class TestExportResults:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    def test_aggregate_results_basic(self):
        """Test basic aggregation of simulation results."""
        data = {
            'n': [10, 10, 10, 20, 20],
            'distribution': ['normal', 'normal', 'normal', 'normal', 'normal'],
            'test_type': ['t_test', 't_test', 't_test', 't_test', 't_test'],
            'rejected': [1, 0, 1, 1, 1],
            'p_value': [0.01, 0.5, 0.03, 0.04, 0.02]
        }
        df = pd.DataFrame(data)
        
        agg_df = aggregate_results(df)
        
        assert len(agg_df) == 2  # Two groups: n=10 and n=20
        assert 'error_rate' in agg_df.columns
        assert 'ci_low' in agg_df.columns
        assert 'ci_high' in agg_df.columns
        
        # Check n=10: 2 rejected out of 3 -> 0.666...
        row_n10 = agg_df[agg_df['n'] == 10].iloc[0]
        assert np.isclose(row_n10['error_rate'], 2/3)

    def test_aggregate_results_empty(self):
        """Test aggregation with empty input."""
        df = pd.DataFrame(columns=['n', 'distribution', 'test_type', 'rejected', 'p_value'])
        agg_df = aggregate_results(df)
        assert agg_df.empty

    def test_compute_bootstrap_ci(self):
        """Test bootstrap CI calculation."""
        # All 1s -> CI should be near 1.0
        data_all_ones = np.array([1, 1, 1, 1, 1])
        low, high = compute_bootstrap_ci(data_all_ones, n_boot=500)
        assert low >= 0.8 and high <= 1.0
        
        # All 0s -> CI should be near 0.0
        data_all_zeros = np.array([0, 0, 0, 0, 0])
        low, high = compute_bootstrap_ci(data_all_zeros, n_boot=500)
        assert low >= 0.0 and high <= 0.2

    def test_plot_generation(self, temp_dir):
        """Test that plot generation creates files."""
        data = {
            'n': [10, 20, 30],
            'distribution': ['normal', 'normal', 'normal'],
            'test_type': ['t_test', 't_test', 't_test'],
            'error_rate': [0.05, 0.04, 0.05],
            'ci_low': [0.02, 0.02, 0.03],
            'ci_high': [0.08, 0.06, 0.07],
            'n_replicates': [100, 100, 100],
            'n_rejected': [5, 4, 5]
        }
        df = pd.DataFrame(data)
        
        plots = generate_all_plots(df, temp_dir)
        
        assert len(plots) == 2
        assert os.path.exists(plots[0])
        assert os.path.exists(plots[1])
        assert plots[0].endswith('.png')
        assert plots[1].endswith('.png')