import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.utils.plots import (
    plot_weekly_counts,
    plot_signal_table,
    plot_ror_distribution,
    plot_sensitivity_comparison,
    create_summary_dashboard
)


class TestPlots:
    @pytest.fixture
    def weekly_df(self):
        dates = pd.date_range(start='2020-01-01', periods=52, freq='W')
        counts = np.random.randint(100, 500, size=52)
        return pd.DataFrame({'REPT_DATE': dates, 'count': counts})

    @pytest.fixture
    def signals_df(self):
        return pd.DataFrame({
            'SOC_CODE': ['SOC_001', 'SOC_002', 'SOC_003', 'SOC_004', 'SOC_005'],
            'ROR': [2.5, 1.8, 3.1, 1.2, 4.0],
            'PRR': [2.1, 1.6, 2.9, 1.1, 3.8],
            'IC': [0.5, -0.2, 1.1, -0.5, 1.5],
            'is_signal': [True, False, True, False, True]
        })

    @pytest.fixture
    def temp_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_plot_weekly_counts(self, weekly_df, temp_output_dir):
        output_path = os.path.join(temp_output_dir, 'weekly.png')
        result = plot_weekly_counts(weekly_df, output_path)
        assert os.path.exists(result)
        assert result == os.path.abspath(output_path)

    def test_plot_weekly_counts_no_date(self, temp_output_dir):
        df = pd.DataFrame({'count': [10, 20, 30]})
        output_path = os.path.join(temp_output_dir, 'weekly_no_date.png')
        result = plot_weekly_counts(df, output_path, date_col='missing_col')
        assert os.path.exists(result)

    def test_plot_signal_table(self, signals_df, temp_output_dir):
        output_path = os.path.join(temp_output_dir, 'signals.png')
        result = plot_signal_table(signals_df, output_path)
        assert os.path.exists(result)

    def test_plot_ror_distribution(self, signals_df, temp_output_dir):
        output_path = os.path.join(temp_output_dir, 'ror_dist.png')
        result = plot_ror_distribution(signals_df, output_path)
        assert os.path.exists(result)

    def test_plot_ror_distribution_missing_col(self, signals_df, temp_output_dir):
        output_path = os.path.join(temp_output_dir, 'ror_dist_fail.png')
        with pytest.raises(ValueError):
            plot_ror_distribution(signals_df, output_path, metric='NON_EXISTENT')

    def test_plot_sensitivity_comparison(self, signals_df, temp_output_dir):
        # Create a second df with slight variations for comparison
        signals_df_2 = signals_df.copy()
        signals_df_2['ROR'] = signals_df_2['ROR'] * 0.9

        output_path = os.path.join(temp_output_dir, 'sensitivity.png')
        result = plot_sensitivity_comparison(signals_df, signals_df_2, output_path)
        assert os.path.exists(result)

    def test_create_summary_dashboard(self, weekly_df, signals_df, temp_output_dir):
        # Generate intermediate files first
        weekly_path = os.path.join(temp_output_dir, 'weekly.png')
        plot_weekly_counts(weekly_df, weekly_path)

        signals_path = os.path.join(temp_output_dir, 'signals.png')
        plot_signal_table(signals_df, signals_path)

        ror_path = os.path.join(temp_output_dir, 'ror.png')
        plot_ror_distribution(signals_df, ror_path)

        # Create dashboard
        dashboard_path = os.path.join(temp_output_dir, 'dashboard.png')
        result = create_summary_dashboard(weekly_path, signals_path, ror_path, dashboard_path)
        assert os.path.exists(result)