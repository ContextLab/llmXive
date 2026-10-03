import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for tests
import matplotlib.pyplot as plt

from src.utils.plots import (
    plot_weekly_counts,
    plot_signal_table,
    plot_ror_distribution,
    plot_sensitivity_comparison,
    create_summary_dashboard
)

class TestPlots:
    @pytest.fixture
    def sample_weekly_data(self):
        """Generate sample weekly data for testing."""
        dates = pd.date_range(start='2020-01-01', periods=52, freq='W')
        data = {
            'REPT_DATE': dates.tolist() * 2,
            'VAX_TYPE': ['COVID-19'] * 52 + ['Non-COVID'] * 52,
            'SOC': ['SOC_A'] * 52 + ['SOC_A'] * 52
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_signals(self):
        """Generate sample signals data."""
        return pd.DataFrame({
            'soc': ['SOC_A', 'SOC_B', 'SOC_C'],
            'ror': [3.5, 1.2, 2.1],
            'ror_ci_lower': [2.0, 0.8, 1.5],
            'ror_ci_upper': [5.0, 1.8, 3.0],
            'prr': [3.0, 1.1, 2.0],
            'prr_ci_lower': [1.8, 0.7, 1.4],
            'prr_ci_upper': [4.5, 1.9, 2.8],
            'ic': [0.8, -0.2, 0.3],
            'ic_ci_lower': [0.1, -0.8, -0.1],
            'ic_ci_upper': [1.5, 0.4, 0.9],
            'p_adj': [0.01, 0.45, 0.08],
            'signal_flag': [True, False, True]
        })

    def test_plot_weekly_counts(self, sample_weekly_data, tmp_path):
        """Test weekly count plot generation."""
        output_path = tmp_path / "weekly_counts.png"
        plot_weekly_counts(sample_weekly_data, output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_weekly_counts_with_soc_filter(self, sample_weekly_data, tmp_path):
        """Test weekly count plot with SOC filter."""
        output_path = tmp_path / "weekly_counts_soc.png"
        plot_weekly_counts(sample_weekly_data, output_path, soc_filter='SOC_A')
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_weekly_counts_empty(self, tmp_path):
        """Test weekly count plot with empty data."""
        empty_data = pd.DataFrame(columns=['REPT_DATE', 'VAX_TYPE'])
        output_path = tmp_path / "weekly_counts_empty.png"
        # Should not raise, but produce a warning/placeholder
        with pytest.warns(UserWarning):
            plot_weekly_counts(empty_data, output_path)
        assert output_path.exists()

    def test_plot_signal_table(self, sample_signals, tmp_path):
        """Test signal table plot generation."""
        output_path = tmp_path / "signal_table.png"
        plot_signal_table(sample_signals, output_path, top_n=3)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_signal_table_empty(self, tmp_path):
        """Test signal table plot with empty data."""
        empty_df = pd.DataFrame(columns=['soc', 'ror'])
        output_path = tmp_path / "signal_table_empty.png"
        with pytest.warns(UserWarning):
            plot_signal_table(empty_df, output_path)
        assert output_path.exists()

    def test_plot_ror_distribution(self, sample_signals, tmp_path):
        """Test ROR distribution plot generation."""
        output_path = tmp_path / "ror_dist.png"
        plot_ror_distribution(sample_signals, output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_plot_ror_distribution_empty(self, tmp_path):
        """Test ROR distribution plot with empty data."""
        empty_df = pd.DataFrame(columns=['ror'])
        output_path = tmp_path / "ror_dist_empty.png"
        with pytest.warns(UserWarning):
            plot_ror_distribution(empty_df, output_path)
        assert output_path.exists()

    def test_plot_sensitivity_comparison(self, tmp_path):
        """Test sensitivity comparison plot generation."""
        data = pd.DataFrame({
            'soc': ['SOC_A', 'SOC_A', 'SOC_B', 'SOC_B'],
            'baseline_type': ['Primary', 'Flu', 'Primary', 'Flu'],
            'ror_delta': [0.5, 0.2, -0.1, -0.3]
        })
        output_path = tmp_path / "sens_comp.png"
        plot_sensitivity_comparison(data, output_path, soc_list=['SOC_A', 'SOC_B'])
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_create_summary_dashboard(self, sample_signals, tmp_path):
        """Test summary dashboard generation."""
        output_dir = tmp_path / "dashboard"
        create_summary_dashboard(sample_signals, sample_signals.head(3), output_dir)
        dashboard_path = output_dir / "summary_dashboard.png"
        assert dashboard_path.exists()
        assert dashboard_path.stat().st_size > 0