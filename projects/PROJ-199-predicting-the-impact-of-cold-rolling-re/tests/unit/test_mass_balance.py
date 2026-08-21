import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features.mass_balance import (
    calculate_random_fraction,
    check_mass_balance,
    validate_descriptor_mass_balance,
    validate_dataset_mass_balance
)

class TestCalculateRandomFraction:
    """Tests for calculate_random_fraction function"""
    
    def test_perfect_balance(self):
        """Test when major components sum to 1.0"""
        result = calculate_random_fraction(1.0)
        assert result == 0.0
    
    def test_partial_balance(self):
        """Test when major components sum to 0.7"""
        result = calculate_random_fraction(0.7)
        assert result == 0.3
    
    def test_over_balance(self):
        """Test when major components exceed 1.0"""
        result = calculate_random_fraction(1.2)
        assert result == 0.0  # Should clamp to 0
    
    def test_zero_balance(self):
        """Test when no major components"""
        result = calculate_random_fraction(0.0)
        assert result == 1.0

class TestCheckMassBalance:
    """Tests for check_mass_balance function"""
    
    def test_perfect_balance_with_random(self):
        """Test perfect balance with explicit random fraction"""
        descriptors = {
            'brass': 0.3,
            'copper': 0.2,
            's': 0.1,
            'goss': 0.2,
            'random': 0.2
        }
        is_balanced, total_sum, deviation = check_mass_balance(descriptors)
        assert is_balanced
        assert abs(total_sum - 1.0) < 1e-9
        assert abs(deviation) < 1e-9
    
    def test_perfect_balance_without_random(self):
        """Test perfect balance without explicit random fraction"""
        descriptors = {
            'brass': 0.3,
            'copper': 0.2,
            's': 0.1,
            'goss': 0.2
        }
        is_balanced, total_sum, deviation = check_mass_balance(descriptors)
        assert is_balanced
        assert abs(total_sum - 1.0) < 1e-9
    
    def test_within_tolerance(self):
        """Test balance within tolerance"""
        descriptors = {
            'brass': 0.3,
            'copper': 0.2,
            's': 0.1,
            'goss': 0.2,
            'random': 0.195
        }
        is_balanced, total_sum, deviation = check_mass_balance(descriptors)
        assert is_balanced
        assert abs(deviation) <= 0.01
    
    def test_outside_tolerance(self):
        """Test balance outside tolerance"""
        descriptors = {
            'brass': 0.3,
            'copper': 0.2,
            's': 0.1,
            'goss': 0.2,
            'random': 0.1
        }
        is_balanced, total_sum, deviation = check_mass_balance(descriptors)
        assert not is_balanced
        assert deviation > 0.01
    
    def test_missing_components(self):
        """Test with missing component keys"""
        descriptors = {
            'brass': 0.3,
            'copper': 0.2
        }
        is_balanced, total_sum, deviation = check_mass_balance(descriptors)
        assert is_balanced
        # Should calculate random as 1.0 - 0.5 = 0.5
        assert abs(total_sum - 1.0) < 1e-9

class TestValidateDescriptorMassBalance:
    """Tests for validate_descriptor_mass_balance function"""
    
    def test_valid_dataframe(self):
        """Test with a valid DataFrame"""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2'],
            'brass': [0.3, 0.2],
            'copper': [0.2, 0.3],
            's': [0.1, 0.1],
            'goss': [0.2, 0.2],
            'random': [0.2, 0.2]
        })
        
        result = validate_descriptor_mass_balance(df)
        
        assert 'mass_balance_sum' in result.columns
        assert 'mass_balance_deviation' in result.columns
        assert 'mass_balance_valid' in result.columns
        assert result['mass_balance_valid'].all()
    
    def test_invalid_dataframe(self):
        """Test with an invalid DataFrame"""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2'],
            'brass': [0.3, 0.2],
            'copper': [0.2, 0.3],
            's': [0.1, 0.1],
            'goss': [0.2, 0.2],
            'random': [0.1, 0.1]  # Sum = 0.9, deviation = 0.1
        })
        
        result = validate_descriptor_mass_balance(df)
        
        assert not result['mass_balance_valid'].all()
        assert result['mass_balance_deviation'].iloc[0] == 0.1
        assert result['mass_balance_deviation'].iloc[1] == 0.1
    
    def test_missing_columns(self):
        """Test with missing component columns"""
        df = pd.DataFrame({
            'sample_id': ['s1'],
            'brass': [0.3]
            # Missing copper, s, goss
        })
        
        result = validate_descriptor_mass_balance(df)
        
        # Should handle missing columns gracefully
        assert 'mass_balance_valid' in result.columns

class TestValidateDatasetMassBalance:
    """Tests for validate_dataset_mass_balance function"""
    
    def test_all_valid(self):
        """Test when all samples are valid"""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2', 's3'],
            'brass': [0.3, 0.2, 0.25],
            'copper': [0.2, 0.3, 0.25],
            's': [0.1, 0.1, 0.1],
            'goss': [0.2, 0.2, 0.2],
            'random': [0.2, 0.2, 0.2]
        })
        
        result = validate_dataset_mass_balance(df, strict=False)
        
        assert result['all_valid']
        assert result['valid_samples'] == 3
        assert result['total_samples'] == 3
        assert result['valid_rate'] == 1.0
    
    def test_some_invalid(self):
        """Test when some samples are invalid"""
        df = pd.DataFrame({
            'sample_id': ['s1', 's2', 's3'],
            'brass': [0.3, 0.2, 0.25],
            'copper': [0.2, 0.3, 0.25],
            's': [0.1, 0.1, 0.1],
            'goss': [0.2, 0.2, 0.2],
            'random': [0.2, 0.1, 0.1]  # s2 and s3 have deviation 0.1
        })
        
        result = validate_dataset_mass_balance(df, strict=False)
        
        assert not result['all_valid']
        assert result['valid_samples'] == 1
        assert result['invalid_samples'] == 2
        assert result['valid_rate'] == 1/3
    
    def test_strict_mode_failure(self):
        """Test strict mode raises ValueError on failure"""
        df = pd.DataFrame({
            'sample_id': ['s1'],
            'brass': [0.3],
            'copper': [0.2],
            's': [0.1],
            'goss': [0.2],
            'random': [0.1]  # Deviation = 0.1
        })
        
        with pytest.raises(ValueError, match="Mass balance validation failed"):
            validate_dataset_mass_balance(df, strict=True)
    
    def test_strict_mode_success(self):
        """Test strict mode passes when all valid"""
        df = pd.DataFrame({
            'sample_id': ['s1'],
            'brass': [0.3],
            'copper': [0.2],
            's': [0.1],
            'goss': [0.2],
            'random': [0.2]
        })
        
        # Should not raise
        result = validate_dataset_mass_balance(df, strict=True)
        assert result['all_valid']

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
