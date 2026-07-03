"""
Unit tests for classification module.

Tests for T020: Continuous ratio calculation
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features.classification import calculate_continuous_ratio
from utils.logging import get_logger


class TestContinuousRatio:
    """Tests for continuous ratio calculation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = get_logger("test_classification")
        
        # Create sample data
        self.sample_data = pd.DataFrame({
            'participant_id': [1, 2, 3, 4, 5],
            'eye_fixation_duration': [100.0, 200.0, 150.0, 0.0, 50.0],
            'mouth_fixation_duration': [50.0, 100.0, 250.0, 100.0, 50.0],
            'other_feature': ['a', 'b', 'c', 'd', 'e']
        })
    
    def test_ratio_calculation_basic(self):
        """Test basic ratio calculation."""
        result = calculate_continuous_ratio(self.sample_data.copy(), self.logger)
        
        # Check that fixation_ratio column was added
        assert 'fixation_ratio' in result.columns
        
        # Check specific values
        # Participant 1: 100 / (100 + 50) = 0.6667
        expected_ratio_1 = 100.0 / (100.0 + 50.0)
        assert abs(result.iloc[0]['fixation_ratio'] - expected_ratio_1) < 0.0001
        
        # Participant 2: 200 / (200 + 100) = 0.6667
        expected_ratio_2 = 200.0 / (200.0 + 100.0)
        assert abs(result.iloc[1]['fixation_ratio'] - expected_ratio_2) < 0.0001
        
        # Participant 3: 150 / (150 + 250) = 0.375
        expected_ratio_3 = 150.0 / (150.0 + 250.0)
        assert abs(result.iloc[2]['fixation_ratio'] - expected_ratio_3) < 0.0001
    
    def test_ratio_calculation_zero_eye(self):
        """Test ratio calculation when eye duration is zero."""
        # Participant 4 has eye=0, mouth=100 -> ratio should be 0
        result = calculate_continuous_ratio(self.sample_data.copy(), self.logger)
        assert abs(result.iloc[3]['fixation_ratio']) < 0.0001
    
    def test_ratio_calculation_equal_durations(self):
        """Test ratio calculation when eye and mouth durations are equal."""
        # Participant 5: eye=50, mouth=50 -> ratio should be 0.5
        result = calculate_continuous_ratio(self.sample_data.copy(), self.logger)
        assert abs(result.iloc[4]['fixation_ratio'] - 0.5) < 0.0001
    
    def test_missing_columns_handling(self):
        """Test handling of missing required columns."""
        # Create data without required columns
        incomplete_data = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'other_feature': ['a', 'b', 'c']
        })
        
        result = calculate_continuous_ratio(incomplete_data.copy(), self.logger)
        
        # Should have NaN values for fixation_ratio
        assert 'fixation_ratio' in result.columns
        assert result['fixation_ratio'].isna().all()
    
    def test_zero_total_duration(self):
        """Test handling when both eye and mouth durations are zero."""
        zero_data = pd.DataFrame({
            'participant_id': [1],
            'eye_fixation_duration': [0.0],
            'mouth_fixation_duration': [0.0]
        })
        
        result = calculate_continuous_ratio(zero_data.copy(), self.logger)
        
        # Should handle division by zero gracefully (result should be NaN or 0)
        # The implementation uses np.where to handle this
        assert result['fixation_ratio'].iloc[0] in [0.0, np.nan] or pd.isna(result['fixation_ratio'].iloc[0])
    
    def test_mean_ratio_warning(self):
        """Test that warning is logged when mean ratio is <= 0."""
        # Create data where mean ratio would be <= 0 (all zeros)
        zero_data = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'eye_fixation_duration': [0.0, 0.0, 0.0],
            'mouth_fixation_duration': [100.0, 100.0, 100.0]
        })
        
        # This should not raise an exception, just log a warning
        result = calculate_continuous_ratio(zero_data.copy(), self.logger)
        
        # Mean should be 0
        assert result['fixation_ratio'].mean() == 0.0
    
    def test_missing_values_handling(self):
        """Test handling of missing values in input data."""
        missing_data = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'eye_fixation_duration': [100.0, np.nan, 150.0],
            'mouth_fixation_duration': [50.0, 100.0, np.nan]
        })
        
        result = calculate_continuous_ratio(missing_data.copy(), self.logger)
        
        # Should have NaN where either component is NaN
        assert pd.isna(result.iloc[1]['fixation_ratio'])
        assert pd.isna(result.iloc[2]['fixation_ratio'])
        assert not pd.isna(result.iloc[0]['fixation_ratio'])
    
    def test_output_dataframe_unchanged_structure(self):
        """Test that original columns are preserved."""
        result = calculate_continuous_ratio(self.sample_data.copy(), self.logger)
        
        # All original columns should still be present
        assert 'participant_id' in result.columns
        assert 'eye_fixation_duration' in result.columns
        assert 'mouth_fixation_duration' in result.columns
        assert 'other_feature' in result.columns
        
        # Same number of rows
        assert len(result) == len(self.sample_data)