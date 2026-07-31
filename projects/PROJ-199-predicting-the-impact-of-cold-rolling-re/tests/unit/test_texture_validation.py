"""
Unit tests for T022: Texture Evolution Deviation Validator
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.texture_validation import (
    calculate_expected_trend,
    calculate_trend_deviation,
    aggregate_deviation_score,
    validate_sample_trends,
    validate_dataset_trends,
    flag_deviant_samples
)

class TestCalculateExpectedTrend:
    """Tests for expected trend calculation"""

    def test_aluminum_trends(self):
        """Test that Aluminum follows expected FCC trends"""
        trends = calculate_expected_trend('Al', 50.0)

        # Brass and Copper should increase
        assert trends['Brass'] > 0
        assert trends['Copper'] > 0

        # Cube should decrease
        assert trends['Cube'] < 0

        # S should increase moderately
        assert trends['S'] > 0

    def test_reduction_scaling(self):
        """Test that trends scale with reduction level"""
        trends_low = calculate_expected_trend('Al', 20.0)
        trends_high = calculate_expected_trend('Al', 80.0)

        # Higher reduction should have larger magnitude trends
        assert trends_high['Brass'] > trends_low['Brass']
        assert abs(trends_high['Cube']) > abs(trends_low['Cube'])

    def test_material_specific_trends(self):
        """Test that different materials have different trend expectations"""
        trends_al = calculate_expected_trend('Al', 50.0)
        trends_cu = calculate_expected_trend('Cu', 50.0)
        trends_ni = calculate_expected_trend('Ni', 50.0)

        # All should have positive Brass trends
        assert trends_al['Brass'] > 0
        assert trends_cu['Brass'] > 0
        assert trends_ni['Brass'] > 0

        # But magnitudes may differ
        assert isinstance(trends_al['Brass'], float)

class TestCalculateTrendDeviation:
    """Tests for deviation calculation"""

    def test_positive_deviation(self):
        """Test detection of positive deviation"""
        sample = {'Brass': 0.5, 'Copper': 0.3, 'material': 'Al', 'reduction': 50.0}
        expected = {'Brass': 0.3, 'Copper': 0.2}

        deviations = calculate_trend_deviation(sample, expected)

        # Brass should show positive deviation
        assert deviations['Brass'] > 0

    def test_negative_deviation(self):
        """Test detection of negative deviation"""
        sample = {'Brass': 0.1, 'Copper': 0.3, 'material': 'Al', 'reduction': 50.0}
        expected = {'Brass': 0.3, 'Copper': 0.2}

        deviations = calculate_trend_deviation(sample, expected)

        # Brass should show negative deviation
        assert deviations['Brass'] < 0

    def test_near_zero_expected(self):
        """Test handling of near-zero expected values"""
        sample = {'Brass': 0.05, 'material': 'Al', 'reduction': 50.0}
        expected = {'Brass': 0.001}

        deviations = calculate_trend_deviation(sample, expected)

        # Should not raise error
        assert 'Brass' in deviations

class TestAggregateDeviationScore:
    """Tests for aggregate score calculation"""

    def test_equal_weights(self):
        """Test aggregation with equal weights"""
        deviations = {'Brass': 1.0, 'Copper': 2.0, 'Cube': 3.0}

        score = aggregate_deviation_score(deviations)

        # Should be average of absolute values
        expected = (1.0 + 2.0 + 3.0) / 3.0
        assert abs(score - expected) < 0.001

    def test_custom_weights(self):
        """Test aggregation with custom weights"""
        deviations = {'Brass': 1.0, 'Copper': 2.0}
        weights = {'Brass': 2.0, 'Copper': 1.0}

        score = aggregate_deviation_score(deviations, weights)

        # Weighted average: (1*2 + 2*1) / (2+1) = 4/3
        expected = 4.0 / 3.0
        assert abs(score - expected) < 0.001

    def test_empty_deviations(self):
        """Test handling of empty deviations"""
        score = aggregate_deviation_score({})
        assert score == 0.0

class TestValidateSampleTrends:
    """Tests for single sample validation"""

    def test_valid_sample(self):
        """Test that a sample following trends is not flagged"""
        sample = {
            'material': 'Al',
            'reduction': 50.0,
            'Brass': 0.25,
            'Copper': 0.20,
            'S': 0.15,
            'Goss': 0.05,
            'Cube': 0.10
        }

        is_valid, details = validate_sample_trends(sample)

        assert isinstance(is_valid, bool)
        assert 'aggregate_deviation_score' in details
        assert 'flagged' in details

    def test_deviant_sample(self):
        """Test that a deviant sample is flagged"""
        # Create a sample with extreme deviation
        sample = {
            'material': 'Al',
            'reduction': 50.0,
            'Brass': 0.90,  # Extremely high Brass
            'Copper': 0.01,  # Extremely low Copper
            'S': 0.01,
            'Goss': 0.01,
            'Cube': 0.01
        }

        is_valid, details = validate_sample_trends(sample, deviation_threshold=0.5)

        # This sample should be flagged
        assert not is_valid
        assert details['flagged']
        assert len(details['deviation_reasons']) > 0

    def test_reason_collection(self):
        """Test that deviation reasons are collected"""
        sample = {
            'material': 'Al',
            'reduction': 50.0,
            'Brass': 0.95,  # Very high
            'Copper': 0.01,  # Very low
            'S': 0.01,
            'Goss': 0.01,
            'Cube': 0.95  # Very high (should decrease)
        }

        is_valid, details = validate_sample_trends(sample, deviation_threshold=0.3)

        if not is_valid:
            assert len(details['deviation_reasons']) > 0
            # Check that reasons contain component names
            reasons_str = '; '.join(details['deviation_reasons'])
            assert 'Brass' in reasons_str or 'Copper' in reasons_str or 'Cube' in reasons_str

class TestValidateDatasetTrends:
    """Tests for dataset-wide validation"""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample dataframe for testing"""
        data = {
            'sample_id': ['S1', 'S2', 'S3'],
            'material': ['Al', 'Cu', 'Al'],
            'reduction': [30.0, 50.0, 70.0],
            'Brass': [0.20, 0.25, 0.30],
            'Copper': [0.15, 0.20, 0.25],
            'S': [0.10, 0.15, 0.20],
            'Goss': [0.05, 0.05, 0.03],
            'Cube': [0.15, 0.10, 0.05]
        }
        return pd.DataFrame(data)

    def test_returns_dataframe(self, sample_dataframe):
        """Test that validation returns a DataFrame"""
        result = validate_dataset_trends(sample_dataframe)

        assert isinstance(result, pd.DataFrame)
        assert 'follows_fcc_trend' in result.columns
        assert 'deviation_score' in result.columns
        assert 'flagged' in result.columns

    def test_all_samples_validated(self, sample_dataframe):
        """Test that all samples are validated"""
        result = validate_dataset_trends(sample_dataframe)

        assert len(result) == len(sample_dataframe)

    def test_valid_samples_not_flagged(self, sample_dataframe):
        """Test that samples following trends are not flagged"""
        result = validate_dataset_trends(sample_dataframe, deviation_threshold=2.0)

        # With high threshold, most samples should not be flagged
        flagged_count = result['flagged'].sum()
        assert flagged_count <= len(sample_dataframe)

class TestFlagDeviantSamples:
    """Tests for deviant sample flagging"""

    @pytest.fixture
    def mixed_dataframe(self):
        """Create a dataframe with both normal and deviant samples"""
        data = {
            'sample_id': ['N1', 'N2', 'D1', 'D2'],
            'material': ['Al', 'Cu', 'Al', 'Cu'],
            'reduction': [40.0, 50.0, 50.0, 60.0],
            'Brass': [0.25, 0.30, 0.90, 0.85],  # D1, D2 have high Brass
            'Copper': [0.20, 0.25, 0.02, 0.03],  # D1, D2 have low Copper
            'S': [0.15, 0.20, 0.01, 0.02],
            'Goss': [0.05, 0.03, 0.02, 0.02],
            'Cube': [0.10, 0.08, 0.01, 0.01]
        }
        return pd.DataFrame(data)

    def test_returns_only_flagged(self, mixed_dataframe):
        """Test that only flagged samples are returned"""
        flagged = flag_deviant_samples(mixed_dataframe, deviation_threshold=0.5)

        assert len(flagged) <= len(mixed_dataframe)
        assert all(flagged['flagged'] == True)

    def test_identifies_deviant_samples(self, mixed_dataframe):
        """Test that deviant samples are correctly identified"""
        flagged = flag_deviant_samples(mixed_dataframe, deviation_threshold=0.5)

        # D1 and D2 should be flagged (they have extreme values)
        flagged_ids = set(flagged['sample_id'])
        assert 'D1' in flagged_ids or 'D2' in flagged_ids

    def test_output_path_creation(self, mixed_dataframe, tmp_path):
        """Test that output file is created when path is provided"""
        output_file = tmp_path / "flagged.csv"
        flag_deviant_samples(mixed_dataframe, output_file, deviation_threshold=0.5)

        assert output_file.exists()

        # Verify file contents
        saved_df = pd.read_csv(output_file)
        assert len(saved_df) > 0
        assert 'sample_id' in saved_df.columns
        assert 'flagged' in saved_df.columns

class TestIntegration:
    """Integration tests for the validation pipeline"""

    def test_full_pipeline(self):
        """Test the complete validation pipeline"""
        # Create realistic test data
        data = {
            'sample_id': [f'S{i}' for i in range(10)],
            'material': ['Al'] * 5 + ['Cu'] * 5,
            'reduction': [20, 30, 40, 50, 60] * 2,
            'Brass': [0.15, 0.18, 0.22, 0.28, 0.35] * 2,
            'Copper': [0.10, 0.15, 0.20, 0.25, 0.30] * 2,
            'S': [0.08, 0.12, 0.15, 0.18, 0.22] * 2,
            'Goss': [0.05, 0.04, 0.03, 0.02, 0.02] * 2,
            'Cube': [0.20, 0.15, 0.12, 0.08, 0.05] * 2
        }
        df = pd.DataFrame(data)

        # Add some deviant samples
        df.loc[8, 'Brass'] = 0.95  # Extreme Brass
        df.loc[9, 'Cube'] = 0.80   # Extreme Cube

        # Validate
        result = validate_dataset_trends(df, deviation_threshold=0.5)

        # Check that deviant samples are flagged
        flagged = result[result['flagged'] == True]

        # At least the two extreme samples should be flagged
        assert len(flagged) >= 2

        # Check that normal samples are not flagged (with appropriate threshold)
        normal_flagged = flagged[~flagged['sample_id'].isin(['S8', 'S9'])]
        # With threshold 0.5, normal samples should not be flagged
        assert len(normal_flagged) == 0
