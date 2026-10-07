"""
Unit tests for src/utils/plots.py
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for tests

from src.utils.plots import (
    plot_weekly_counts,
    plot_signal_table,
    plot_ror_distribution,
    plot_sensitivity_comparison,
    create_summary_dashboard
)

class TestPlots:
    @pytest.fixture
    def weekly_data(self):
        """Create sample weekly data."""
        dates = pd.date_range(start='2020-01-01', periods=10, freq='W')
        data = {
            'REPT_DATE': dates,
            'count': [10, 15, 12, 20, 18, 25, 30, 22, 19, 28]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def signals_data(self):
        """Create sample signals data."""
        data = {
            'soc': ['SOC A', 'SOC B', 'SOC C', 'SOC D', 'SOC E'],
            'ror': [2.5, 1.8, 3.2, 1.2, 2.1],
            'prr': [1.9, 1.6, 2.8, 1.1, 1.7],
            'ic': [0.5, 0.2, 0.8, -0.1, 0.4],
            'ror_ci_lower': [1.5, 1.2, 2.1, 0.8, 1.4],
            'signal_flag': [True, False, True, False, True]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sensitivity_data(self):
        """Create sample sensitivity data."""
        data = {
            'soc': ['SOC A', 'SOC A', 'SOC B'],
            'baseline_type': ['Flu-only', 'Non-COVID', 'Flu-only'],
            'ror_delta': [0.2, 0.1, -0.05],
            'prr_delta': [0.1, 0.05, -0.02],
            'ic_delta': [0.05, 0.02, -0.01]
        }
        return pd.DataFrame(data)

    def test_plot_weekly_counts(self, weekly_data, tmp_path):
        """Test weekly counts plot generation."""
        output_file = tmp_path / "test_weekly.png"
        result_path = plot_weekly_counts(
            weekly_data, 
            soc_name="Test SOC", 
            output_path=output_file
        )
        
        assert result_path.exists()
        assert result_path == output_file
        # Check file size is non-zero
        assert result_path.stat().st_size > 0

    def test_plot_weekly_counts_empty_df(self, tmp_path):
        """Test that empty dataframe raises error."""
        empty_df = pd.DataFrame(columns=['REPT_DATE', 'count'])
        with pytest.raises(ValueError):
            plot_weekly_counts(empty_df, soc_name="Empty", output_path=tmp_path / "test.png")

    def test_plot_signal_table(self, signals_data, tmp_path):
        """Test signal table plot generation."""
        output_file = tmp_path / "test_table.png"
        result_path = plot_signal_table(
            signals_data, 
            output_path=output_file,
            top_n=3
        )
        
        assert result_path.exists()
        assert result_path == output_file
        assert result_path.stat().st_size > 0

    def test_plot_ror_distribution(self, signals_data, tmp_path):
        """Test ROR distribution plot generation."""
        output_file = tmp_path / "test_ror_dist.png"
        result_path = plot_ror_distribution(
            signals_data, 
            output_path=output_file,
            metric='ror'
        )
        
        assert result_path.exists()
        assert result_path == output_file
        assert result_path.stat().st_size > 0

    def test_plot_ror_distribution_missing_metric(self, signals_data, tmp_path):
        """Test error when metric column is missing."""
        with pytest.raises(ValueError):
            plot_ror_distribution(signals_data, metric='non_existent_metric')

    def test_plot_sensitivity_comparison(self, sensitivity_data, tmp_path):
        """Test sensitivity comparison plot generation."""
        output_file = tmp_path / "test_sens.png"
        result_path = plot_sensitivity_comparison(
            sensitivity_data, 
            soc="SOC A", 
            output_path=output_file
        )
        
        assert result_path.exists()
        assert result_path == output_file
        assert result_path.stat().st_size > 0

    def test_plot_sensitivity_comparison_missing_soc(self, sensitivity_data, tmp_path):
        """Test error when SOC is not found."""
        with pytest.raises(ValueError):
            plot_sensitivity_comparison(sensitivity_data, soc="Non Existent SOC")

    def test_create_summary_dashboard(self, signals_data, weekly_data, tmp_path):
        """Test summary dashboard generation."""
        top_socs = ['SOC A', 'SOC B']
        temporal_data = {
            'SOC A': weekly_data,
            'SOC B': weekly_data
        }
        output_file = tmp_path / "test_dashboard.png"
        
        result_path = create_summary_dashboard(
            signals_data, 
            top_socs, 
            temporal_data, 
            output_path=output_file
        )
        
        assert result_path.exists()
        assert result_path == output_file
        assert result_path.stat().st_size > 0

    def test_create_summary_dashboard_no_socs(self, signals_data, tmp_path):
        """Test dashboard with no top SOCs."""
        output_file = tmp_path / "test_empty_dash.png"
        result_path = create_summary_dashboard(
            signals_data, 
            [], 
            {}, 
            output_path=output_file
        )
        
        assert result_path.exists()
        assert result_path.stat().st_size > 0