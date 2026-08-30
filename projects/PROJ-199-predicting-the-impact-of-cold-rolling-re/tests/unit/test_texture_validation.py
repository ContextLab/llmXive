import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.texture_validation import (
    calculate_expected_trend,
    calculate_trend_deviation,
    validate_sample_trends,
    flag_deviant_samples,
    STANDARD_FCC_TRENDS
)

class TestTextureValidation:
    
    def test_calculate_expected_trend_known_material(self):
        """Test that known materials return correct trends."""
        trends = calculate_expected_trend('Al')
        assert trends['brass'] == 'increase'
        assert trends['random'] == 'decrease'

    def test_calculate_expected_trend_unknown_material(self):
        """Test fallback for unknown materials."""
        trends = calculate_expected_trend('UnknownMetal')
        assert 'brass' in trends
        assert trends['brass'] == 'increase'

    def test_calculate_trend_deviation_high_reduction_random(self):
        """Test detection of high reduction sample with high random fraction."""
        sample = pd.Series({
            'reduction': 70,
            'random_fraction': 0.4,
            'brass_fraction': 0.1,
            'copper_fraction': 0.1,
            's_fraction': 0.1,
            'goss_fraction': 0.1
        })
        expected = calculate_expected_trend('Al')
        is_deviant, details = calculate_trend_deviation(sample, expected)
        
        assert is_deviant is True
        assert 'high_reduction_random' in details
        assert details['high_reduction_random']['status'] == 'FAIL'

    def test_calculate_trend_deviation_low_reduction_textured(self):
        """Test detection of low reduction sample with high texture intensity."""
        sample = pd.Series({
            'reduction': 10,
            'random_fraction': 0.1,
            'brass_fraction': 0.3,
            'copper_fraction': 0.3,
            's_fraction': 0.3,
            'goss_fraction': 0.1
        })
        expected = calculate_expected_trend('Cu')
        is_deviant, details = calculate_trend_deviation(sample, expected)
        
        assert is_deviant is True
        assert 'low_reduction_textured' in details

    def test_calculate_trend_deviation_normal_sample(self):
        """Test that a normal sample is not flagged."""
        # High reduction, low random (normal)
        sample = pd.Series({
            'reduction': 70,
            'random_fraction': 0.1,
            'brass_fraction': 0.3,
            'copper_fraction': 0.3,
            's_fraction': 0.2,
            'goss_fraction': 0.1
        })
        expected = calculate_expected_trend('Al')
        is_deviant, details = calculate_trend_deviation(sample, expected)
        
        assert is_deviant is False

    def test_validate_sample_trends_integration(self):
        """Test the full validation pipeline on a DataFrame."""
        data = {
            'material': ['Al', 'Al', 'Cu'],
            'reduction': [70, 10, 50],
            'random_fraction': [0.4, 0.1, 0.2], # First one is deviant
            'brass_fraction': [0.1, 0.3, 0.2],
            'copper_fraction': [0.1, 0.3, 0.2],
            's_fraction': [0.1, 0.3, 0.2],
            'goss_fraction': [0.1, 0.1, 0.2]
        }
        df = pd.DataFrame(data)
        
        result = validate_sample_trends(df)
        
        assert 'is_trend_deviant' in result.columns
        assert result.iloc[0]['is_trend_deviant'] is True  # High reduction, high random
        assert result.iloc[1]['is_trend_deviant'] is False # Low reduction, low random (normal)
        assert result.iloc[2]['is_trend_deviant'] is False # Mid reduction, normal

    def test_flag_deviant_samples_output(self):
        """Test that flag_deviant_samples returns the correct DataFrame shape."""
        data = {
            'material': ['Al'],
            'reduction': [80],
            'random_fraction': [0.5],
            'brass_fraction': [0.1],
            'copper_fraction': [0.1],
            's_fraction': [0.1],
            'goss_fraction': [0.1]
        }
        df = pd.DataFrame(data)
        
        result = flag_deviant_samples(df)
        
        assert 'is_trend_deviant' in result.columns
        assert result['is_trend_deviant'].sum() == 1