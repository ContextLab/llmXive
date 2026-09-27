"""
Unit tests for src/utils/plots.py
"""
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
    def weekly_data(self):
        """Create sample weekly count data."""
        dates = pd.date_range(start='2020-01-01', periods=20, freq='W')
        data = []
        for date in dates:
            data.append({
                'REPT_DATE': date,
                'VAX_TYPE_GROUP': 'COVID-19',
                'count': np.random.randint(10, 100)
            })
            data.append({
                'REPT_DATE': date,
                'VAX_TYPE_GROUP': 'Non-COVID',
                'count': np.random.randint(10, 50)
            })
        return pd.DataFrame(data)

    @pytest.fixture
    def signals_data(self):
        """Create sample signals data."""
        return pd.DataFrame({
            'soc': ['SOC1', 'SOC2', 'SOC3', 'SOC4', 'SOC5'],
            'ror': [2.5, 1.8, 3.1, 0.9, 2.2],
            'ror_ci_lower': [1.2, 0.9, 1.5, 0.5, 1.1],
            'ror_ci_upper': [4.0, 3.0, 5.0, 1.5, 3.5],
            'prr': [2.1, 1.6, 2.8, 0.8, 1.9],
            'ic': [0.8, 0.4, 1.2, -0.2, 0.7],
            'signal_flag': [True, False, True, False, True]
        })

    @pytest.fixture
    def sensitivity_data(self):
        """Create sample sensitivity data."""
        return pd.DataFrame({
            'soc': ['SOC1', 'SOC2', 'SOC3', 'SOC4', 'SOC5'],
            'ror_delta': [0.5, -0.2, 0.8, -0.1, 0.3],
            'prr_delta': [0.4, -0.1, 0.6, 0.0, 0.2]
        })

    def test_plot_weekly_counts(self, weekly_data, tmp_path):
        """Test weekly count plot generation."""
        output_path = tmp_path / "weekly_counts.png"
        result = plot_weekly_counts(
            df=weekly_data,
            soc="Test SOC",
            output_path=output_path
        )
        assert result.exists()
        assert result.stat().st_size > 0

    def test_plot_weekly_counts_empty_df(self, tmp_path):
        """Test that empty DataFrame raises ValueError."""
        empty_df = pd.DataFrame(columns=['REPT_DATE', 'VAX_TYPE_GROUP', 'count'])
        output_path = tmp_path / "empty.png"
        with pytest.raises(ValueError):
            plot_weekly_counts(df=empty_df, soc="Test", output_path=output_path)

    def test_plot_weekly_counts_missing_columns(self, tmp_path):
        """Test that missing columns raise ValueError."""
        bad_df = pd.DataFrame({'date': [1], 'group': [2]})
        output_path = tmp_path / "bad.png"
        with pytest.raises(ValueError):
            plot_weekly_counts(df=bad_df, soc="Test", output_path=output_path)

    def test_plot_signal_table(self, signals_data, tmp_path):
        """Test signal table plot generation."""
        output_path = tmp_path / "signal_table.png"
        result = plot_signal_table(
            signals_df=signals_data,
            output_path=output_path,
            top_n=3
        )
        assert result.exists()
        assert result.stat().st_size > 0

    def test_plot_signal_table_empty(self, tmp_path):
        """Test that empty signals DataFrame raises ValueError."""
        empty_df = pd.DataFrame(columns=['soc', 'ror'])
        output_path = tmp_path / "empty_table.png"
        with pytest.raises(ValueError):
            plot_signal_table(signals_df=empty_df, output_path=output_path)

    def test_plot_ror_distribution(self, signals_data, tmp_path):
        """Test ROR distribution plot generation."""
        output_path = tmp_path / "ror_dist.png"
        result = plot_ror_distribution(
            signals_df=signals_data,
            output_path=output_path,
            metric='ror',
            threshold=2.0
        )
        assert result.exists()
        assert result.stat().st_size > 0

    def test_plot_ror_distribution_missing_metric(self, signals_data, tmp_path):
        """Test that missing metric column raises ValueError."""
        output_path = tmp_path / "bad_metric.png"
        with pytest.raises(ValueError):
            plot_ror_distribution(
                signals_df=signals_data,
                output_path=output_path,
                metric='nonexistent_metric'
            )

    def test_plot_sensitivity_comparison(self, sensitivity_data, tmp_path):
        """Test sensitivity comparison plot generation."""
        output_path = tmp_path / "sensitivity.png"
        result = plot_sensitivity_comparison(
            sensitivity_df=sensitivity_data,
            output_path=output_path,
            top_n=3
        )
        assert result.exists()
        assert result.stat().st_size > 0

    def test_create_summary_dashboard(self, signals_data, tmp_path):
        """Test summary dashboard generation."""
        # Create a dummy weekly plots directory
        weekly_dir = tmp_path / "weekly_plots"
        weekly_dir.mkdir()
        
        # Create a dummy plot file to simulate existence
        (weekly_dir / "dummy.png").touch()
        
        output_path = tmp_path / "dashboard.png"
        result = create_summary_dashboard(
            signals_df=signals_data,
            weekly_plots_dir=weekly_dir,
            output_path=output_path
        )
        assert result.exists()
        assert result.stat().st_size > 0