"""
Unit tests for T015: Project-level aggregation of pair-level variances.

Tests the weighted mean aggregation logic to ensure statistical instability
is addressed correctly as per FR-010.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function to test
from aggregation import aggregate_pair_metrics_to_project_level


class TestAggregationWeightedMean:
    """Tests for the weighted mean aggregation logic."""

    def test_basic_weighted_mean_calculation(self):
        """Test that weighted mean is calculated correctly with simple data."""
        # Create test data: 2 pairs, 1 project
        # Pair 1: variance=10, events=5
        # Pair 2: variance=20, events=15
        # Expected weighted mean = (10*5 + 20*15) / (5+15) = 350/20 = 17.5
        data = {
            'project_id': ['P1', 'P1'],
            'pair_id': ['pair1', 'pair2'],
            'response_time_variance': [10.0, 20.0],
            'mean_delay': [100.0, 200.0],
            'event_count': [5, 15]
        }
        df = pd.DataFrame(data)

        result_df, stats = aggregate_pair_metrics_to_project_level(df)

        assert len(result_df) == 1
        assert result_df.iloc[0]['project_id'] == 'P1'
        assert result_df.iloc[0]['pair_count'] == 2
        assert result_df.iloc[0]['total_events'] == 20

        # Check weighted mean calculation
        expected_variance = (10.0 * 5 + 20.0 * 15) / 20.0
        assert abs(result_df.iloc[0]['project_variance_weighted_mean'] - expected_variance) < 0.001

        # Check weighted mean for delay
        expected_delay = (100.0 * 5 + 200.0 * 15) / 20.0
        assert abs(result_df.iloc[0]['project_mean_delay_weighted_mean'] - expected_delay) < 0.001

    def test_multiple_projects(self):
        """Test aggregation across multiple projects."""
        data = {
            'project_id': ['P1', 'P1', 'P2', 'P2'],
            'pair_id': ['p1_1', 'p1_2', 'p2_1', 'p2_2'],
            'response_time_variance': [10.0, 30.0, 5.0, 15.0],
            'mean_delay': [100.0, 300.0, 50.0, 150.0],
            'event_count': [10, 10, 20, 20]
        }
        df = pd.DataFrame(data)

        result_df, stats = aggregate_pair_metrics_to_project_level(df)

        assert len(result_df) == 2

        # P1: (10*10 + 30*10) / 20 = 20
        p1_row = result_df[result_df['project_id'] == 'P1'].iloc[0]
        assert abs(p1_row['project_variance_weighted_mean'] - 20.0) < 0.001

        # P2: (5*20 + 15*20) / 40 = 10
        p2_row = result_df[result_df['project_id'] == 'P2'].iloc[0]
        assert abs(p2_row['project_variance_weighted_mean'] - 10.0) < 0.001

    def test_handles_nan_values(self):
        """Test that NaN values in variance are handled correctly."""
        data = {
            'project_id': ['P1', 'P1', 'P1'],
            'pair_id': ['p1', 'p2', 'p3'],
            'response_time_variance': [10.0, np.nan, 20.0],
            'mean_delay': [100.0, 150.0, 200.0],
            'event_count': [5, 10, 15]
        }
        df = pd.DataFrame(data)

        result_df, stats = aggregate_pair_metrics_to_project_level(df)

        # Should only use valid values: (10*5 + 20*15) / (5+15) = 350/20 = 17.5
        assert len(result_df) == 1
        assert abs(result_df.iloc[0]['project_variance_weighted_mean'] - 17.5) < 0.001

    def test_empty_dataframe(self):
        """Test handling of empty input dataframe."""
        df = pd.DataFrame(columns=['project_id', 'pair_id', 'response_time_variance', 'event_count'])
        result_df, stats = aggregate_pair_metrics_to_project_level(df)

        assert result_df.empty
        assert stats['projects_processed'] == 0

    def test_below_threshold_filtering(self):
        """Test that projects below min_events threshold are excluded."""
        data = {
            'project_id': ['P1', 'P1', 'P2', 'P2'],
            'pair_id': ['p1_1', 'p1_2', 'p2_1', 'p2_2'],
            'response_time_variance': [10.0, 20.0, 15.0, 25.0],
            'mean_delay': [100.0, 200.0, 150.0, 250.0],
            'event_count': [2, 2, 10, 10]  # P1 total=4, P2 total=20
        }
        df = pd.DataFrame(data)

        # Temporarily override config to set threshold
        import config
        original_get_config = config.get_config
        config.get_config = lambda: {'sample_size': 10}

        try:
            result_df, stats = aggregate_pair_metrics_to_project_level(df)
            assert len(result_df) == 1
            assert result_df.iloc[0]['project_id'] == 'P2'
            assert stats['projects_below_threshold'] == 1
        finally:
            config.get_config = original_get_config

    def test_output_file_creation(self):
        """Test that output file is created correctly."""
        data = {
            'project_id': ['P1'],
            'pair_id': ['p1'],
            'response_time_variance': [15.0],
            'mean_delay': [120.0],
            'event_count': [10]
        }
        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.csv"
            result_df, stats = aggregate_pair_metrics_to_project_level(df, output_path=str(output_path))

            assert output_path.exists()
            saved_df = pd.read_csv(output_path)
            assert len(saved_df) == 1
            assert saved_df.iloc[0]['project_id'] == 'P1'

    def test_missing_required_columns(self):
        """Test that missing required columns raise an error."""
        data = {
            'project_id': ['P1'],
            'pair_id': ['p1'],
            'response_time_variance': [15.0]
            # Missing 'event_count'
        }
        df = pd.DataFrame(data)

        with pytest.raises(ValueError, match="Missing required columns"):
            aggregate_pair_metrics_to_project_level(df)

    def test_inf_values_handling(self):
        """Test that infinite values are handled correctly."""
        data = {
            'project_id': ['P1', 'P1'],
            'pair_id': ['p1', 'p2'],
            'response_time_variance': [10.0, float('inf')],
            'mean_delay': [100.0, 200.0],
            'event_count': [5, 15]
        }
        df = pd.DataFrame(data)

        result_df, stats = aggregate_pair_metrics_to_project_level(df)

        # Should only use the valid value
        assert len(result_df) == 1
        assert abs(result_df.iloc[0]['project_variance_weighted_mean'] - 10.0) < 0.001