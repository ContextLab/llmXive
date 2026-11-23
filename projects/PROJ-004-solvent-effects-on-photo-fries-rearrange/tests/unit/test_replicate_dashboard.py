"""
Unit tests for replicate dashboard functionality.

Tests verify:
    - Statistics calculation correctness
    - Outlier flag handling
    - Dashboard generation without errors
    - Output file creation
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

import pytest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.replicate_dashboard import (
    calculate_replicate_statistics,
    generate_dashboard_table,
    load_kinetic_metrics_for_dashboard
)
from config import get_processed_data_path, get_figures_path

class TestReplicateStatistics:
    """Tests for replicate statistics calculation."""

    def test_calculate_statistics_basic(self):
        """Test basic statistics calculation with known values."""
        # Create test data
        data = {
            'solvent': ['A', 'A', 'A', 'B', 'B'],
            'lifetime': [1.0, 1.1, 0.9, 2.0, 2.2],
            'ci_lower': [0.8, 0.85, 0.8, 1.5, 1.6],
            'ci_upper': [1.2, 1.15, 1.2, 2.5, 2.8],
            'is_outlier': [False, False, False, False, False]
        }
        df = pd.DataFrame(data)
        
        stats = calculate_replicate_statistics(df)
        
        # Verify solvent A stats
        a_row = stats[stats['solvent'] == 'A'].iloc[0]
        assert a_row['n_runs'] == 3
        assert np.isclose(a_row['mean_lifetime'], 1.0, atol=0.01)
        assert np.isclose(a_row['std_lifetime'], 0.1, atol=0.01)
        
        # Verify CV calculation
        expected_cv = 0.1 / 1.0
        assert np.isclose(a_row['cv'], expected_cv, atol=0.01)

    def test_calculate_statistics_single_run(self):
        """Test statistics with only one run (std should be NaN)."""
        data = {
            'solvent': ['A'],
            'lifetime': [1.5],
            'ci_lower': [1.3],
            'ci_upper': [1.7],
            'is_outlier': [False]
        }
        df = pd.DataFrame(data)
        
        stats = calculate_replicate_statistics(df)
        
        assert stats['n_runs'].iloc[0] == 1
        assert pd.isna(stats['std_lifetime'].iloc[0])
        assert stats['cv'].iloc[0] == 0.0  # Should be 0, not NaN

    def test_outlier_counting(self):
        """Test that outliers are correctly counted."""
        data = {
            'solvent': ['A', 'A', 'A', 'A', 'B', 'B'],
            'lifetime': [1.0, 1.1, 0.9, 5.0, 2.0, 2.2],
            'ci_lower': [0.8, 0.85, 0.8, 1.0, 1.5, 1.6],
            'ci_upper': [1.2, 1.15, 1.2, 6.0, 2.5, 2.8],
            'is_outlier': [False, False, False, True, False, False]
        }
        df = pd.DataFrame(data)
        
        stats = calculate_replicate_statistics(df)
        
        a_row = stats[stats['solvent'] == 'A'].iloc[0]
        b_row = stats[stats['solvent'] == 'B'].iloc[0]
        
        assert a_row['outlier_count'] == 1
        assert b_row['outlier_count'] == 0

    def test_cv_calculation_edge_cases(self):
        """Test CV calculation with zero mean (should handle gracefully)."""
        data = {
            'solvent': ['A', 'A'],
            'lifetime': [0.0, 0.1],
            'ci_lower': [0.0, 0.0],
            'ci_upper': [0.1, 0.2],
            'is_outlier': [False, False]
        }
        df = pd.DataFrame(data)
        
        # This should not crash, even with zero mean
        stats = calculate_replicate_statistics(df)
        
        # CV should be calculated (may be large or inf if mean is 0)
        assert 'cv' in stats.columns
        assert len(stats) == 1

class TestDashboardTableGeneration:
    """Tests for dashboard table generation."""

    def test_generate_table_structure(self):
        """Test that generated table has required structure."""
        data = {
            'solvent': ['A', 'B'],
            'n_runs': [3, 2],
            'mean_lifetime': [1.0, 2.0],
            'std_lifetime': [0.1, 0.2],
            'min_lifetime': [0.9, 1.8],
            'max_lifetime': [1.1, 2.2],
            'ci_lower_min': [0.8, 1.5],
            'ci_upper_max': [1.2, 2.5],
            'outlier_count': [0, 1],
            'cv': [0.1, 0.1]
        }
        stats_df = pd.DataFrame(data)
        
        report = generate_dashboard_table(stats_df)
        
        # Check top-level keys
        assert 'generated_at' in report
        assert 'total_solvents' in report
        assert 'total_runs' in report
        assert 'statistics' in report
        assert 'summary' in report
        
        # Check summary structure
        summary = report['summary']
        assert 'min_runs_per_solvent' in summary
        assert 'max_runs_per_solvent' in summary
        assert 'mean_cv' in summary
        assert 'total_outliers' in summary
        
        # Check statistics are list of dicts
        assert isinstance(report['statistics'], list)
        assert len(report['statistics']) == 2

    def test_total_runs_calculation(self):
        """Test that total runs are correctly summed."""
        data = {
            'solvent': ['A', 'B', 'C'],
            'n_runs': [3, 5, 2],
            'mean_lifetime': [1.0, 2.0, 3.0],
            'std_lifetime': [0.1, 0.2, 0.3],
            'min_lifetime': [0.9, 1.8, 2.8],
            'max_lifetime': [1.1, 2.2, 3.2],
            'ci_lower_min': [0.8, 1.5, 2.5],
            'ci_upper_max': [1.2, 2.5, 3.5],
            'outlier_count': [0, 1, 0],
            'cv': [0.1, 0.1, 0.1]
        }
        stats_df = pd.DataFrame(data)
        
        report = generate_dashboard_table(stats_df)
        
        assert report['total_runs'] == 10  # 3 + 5 + 2
        assert report['total_solvents'] == 3

class TestIntegration:
    """Integration tests with real file paths (using synthetic data)."""

    def test_load_metrics_with_missing_file(self):
        """Test that missing file raises appropriate error."""
        # Temporarily rename file if it exists
        metrics_path = get_processed_data_path() / "kinetic_metrics.csv"
        backup_path = get_processed_data_path() / "kinetic_metrics.csv.bak"
        
        if metrics_path.exists():
            metrics_path.rename(backup_path)
        
        try:
            with pytest.raises(FileNotFoundError):
                load_kinetic_metrics_for_dashboard()
        finally:
            # Restore file if it was renamed
            if backup_path.exists():
                backup_path.rename(metrics_path)

    def test_statistics_rounding(self):
        """Test that statistics are properly rounded."""
        data = {
            'solvent': ['A', 'A', 'A'],
            'lifetime': [1.123456789, 1.234567890, 1.345678901],
            'ci_lower': [1.0, 1.1, 1.2],
            'ci_upper': [1.3, 1.4, 1.5],
            'is_outlier': [False, False, False]
        }
        df = pd.DataFrame(data)
        
        stats = calculate_replicate_statistics(df)
        
        # All numeric columns should be rounded to 4 decimal places
        for col in ['mean_lifetime', 'std_lifetime', 'cv']:
            val = stats[col].iloc[0]
            assert isinstance(val, float)
            # Check that it's not excessively long (rounded)
            assert len(str(val).split('.')[-1]) <= 6  # Allow some float representation variance

if __name__ == '__main__':
    pytest.main([__file__, '-v'])