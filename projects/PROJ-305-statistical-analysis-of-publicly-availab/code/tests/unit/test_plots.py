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
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt

from src.utils.plots import (
    plot_weekly_counts,
    plot_signal_table,
    plot_ror_distribution,
    plot_sensitivity_comparison,
    create_summary_dashboard
)


class TestPlots:
    """Test suite for plotting functions."""

    @pytest.fixture
    def sample_cleaned_data(self):
        """Generate sample cleaned data for testing."""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        data = {
            'SOC_CODE': ['SOC_1'] * 50 + ['SOC_2'] * 50,
            'VAX_TYPE': ['COVID-19'] * 25 + ['Non-COVID'] * 25 + ['COVID-19'] * 25 + ['Non-COVID'] * 25,
            'REPT_DATE': list(dates) * 2
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_signal_data(self):
        """Generate sample signal data."""
        data = {
            'SOC_CODE': ['SOC_1', 'SOC_2', 'SOC_3'],
            'ROR': [2.5, 1.8, 3.0],
            'PRR': [2.1, 1.5, 2.8],
            'IC': [0.5, -0.1, 1.2],
            'Signal_Flag': [True, False, True]
        }
        return pd.DataFrame(data)

    def test_plot_weekly_counts(self, sample_cleaned_data, tmp_path):
        """Test weekly count plot generation."""
        output_file = tmp_path / "test_weekly.png"
        result = plot_weekly_counts(sample_cleaned_data, 'SOC_1', output_path=output_file)
        
        assert result.exists()
        assert result.stat().st_size > 0
        
        # Verify no plot remains open
        assert len(plt.get_fignums()) == 0

    def test_plot_weekly_counts_empty(self, tmp_path):
        """Test weekly count plot with no data."""
        empty_df = pd.DataFrame(columns=['SOC_CODE', 'REPT_DATE', 'VAX_TYPE'])
        output_file = tmp_path / "test_empty_weekly.png"
        
        with pytest.warns(UserWarning):
            result = plot_weekly_counts(empty_df, 'SOC_1', output_path=output_file)
        
        assert result.exists()

    def test_plot_signal_table(self, sample_signal_data, tmp_path):
        """Test signal table plot generation."""
        output_file = tmp_path / "test_signal_table.png"
        result = plot_signal_table(sample_signal_data, output_path=output_file)
        
        assert result.exists()
        assert result.stat().st_size > 0

    def test_plot_signal_table_empty(self, tmp_path):
        """Test signal table with empty dataframe."""
        empty_df = pd.DataFrame()
        output_file = tmp_path / "test_empty_table.png"
        result = plot_signal_table(empty_df, output_path=output_file)
        
        assert result.exists()

    def test_plot_ror_distribution(self, sample_signal_data, tmp_path):
        """Test ROR distribution plot generation."""
        output_file = tmp_path / "test_ror_dist.png"
        result = plot_ror_distribution(sample_signal_data, 'ROR', output_path=output_file)
        
        assert result.exists()
        assert result.stat().st_size > 0

    def test_plot_ror_distribution_missing_metric(self, sample_signal_data, tmp_path):
        """Test ROR distribution with missing metric column."""
        output_file = tmp_path / "test_missing_metric.png"
        with pytest.warns(UserWarning):
            result = plot_ror_distribution(sample_signal_data, 'NON_EXISTENT', output_path=output_file)
        
        assert result.exists()

    def test_plot_sensitivity_comparison(self, sample_signal_data, tmp_path):
        """Test sensitivity comparison plot."""
        output_file = tmp_path / "test_sens_comp.png"
        # Use same data for both for simplicity
        result = plot_sensitivity_comparison(
            sample_signal_data, 
            sample_signal_data, 
            output_path=output_file
        )
        
        assert result.exists()
        assert result.stat().st_size > 0

    def test_create_summary_dashboard(self, sample_signal_data, tmp_path):
        """Test summary dashboard generation."""
        output_file = tmp_path / "test_dashboard.png"
        result = create_summary_dashboard(sample_signal_data, output_path=output_file)
        
        assert result.exists()
        assert result.stat().st_size > 0

    def test_create_summary_dashboard_empty(self, tmp_path):
        """Test dashboard with empty dataframe."""
        empty_df = pd.DataFrame()
        output_file = tmp_path / "test_empty_dashboard.png"
        result = create_summary_dashboard(empty_df, output_path=output_file)
        
        assert result.exists()