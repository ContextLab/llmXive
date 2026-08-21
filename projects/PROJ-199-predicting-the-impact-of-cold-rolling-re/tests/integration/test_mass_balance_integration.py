import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import tempfile
import shutil

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features.mass_balance import (
    validate_dataset_mass_balance,
    check_mass_balance
)
from features.export_descriptors import load_processed_data

class TestMassBalanceIntegration:
    """Integration tests for mass balance validation with real workflow"""
    
    @pytest.fixture
    def sample_descriptors(self):
        """Create a sample descriptors DataFrame for testing"""
        return pd.DataFrame({
            'sample_id': [f'sample_{i}' for i in range(10)],
            'material': ['Al'] * 5 + ['Cu'] * 5,
            'reduction': [10, 20, 30, 40, 50] * 2,
            'brass': [0.25, 0.30, 0.35, 0.40, 0.45] * 2,
            'copper': [0.20, 0.25, 0.20, 0.15, 0.10] * 2,
            's': [0.15, 0.15, 0.15, 0.15, 0.15] * 2,
            'goss': [0.10, 0.10, 0.10, 0.10, 0.10] * 2,
            'random': [0.30, 0.20, 0.20, 0.30, 0.20] * 2
        })
    
    def test_mass_balance_on_real_workflow(self, sample_descriptors, tmp_path):
        """Test mass balance validation in a realistic workflow"""
        # Save sample data to temporary file
        temp_csv = tmp_path / "test_descriptors.csv"
        sample_descriptors.to_csv(temp_csv, index=False)
        
        # Validate mass balance
        result = validate_dataset_mass_balance(sample_descriptors)
        
        # Check that all required fields are present
        assert 'total_samples' in result
        assert 'valid_samples' in result
        assert 'invalid_samples' in result
        assert 'valid_rate' in result
        assert 'max_deviation' in result
        assert 'mean_deviation' in result
        assert 'all_valid' in result
        assert 'validated_df' in result
        
        # Check that validated_df has required columns
        validated_df = result['validated_df']
        assert 'mass_balance_sum' in validated_df.columns
        assert 'mass_balance_deviation' in validated_df.columns
        assert 'mass_balance_valid' in validated_df.columns
        
        # Check that all samples are valid (sum should be 1.0)
        assert result['all_valid']
        assert result['valid_samples'] == 10
        assert result['total_samples'] == 10
    
    def test_mass_balance_with_tolerance_violations(self, tmp_path):
        """Test mass balance with intentional violations"""
        # Create data with violations
        df = pd.DataFrame({
            'sample_id': ['good', 'bad1', 'bad2'],
            'brass': [0.3, 0.4, 0.5],
            'copper': [0.2, 0.3, 0.2],
            's': [0.1, 0.1, 0.1],
            'goss': [0.2, 0.1, 0.1],
            'random': [0.2, 0.1, 0.0]  # bad1: sum=0.9, bad2: sum=0.9
        })
        
        result = validate_dataset_mass_balance(df, strict=False)
        
        assert result['total_samples'] == 3
        assert result['valid_samples'] == 1
        assert result['invalid_samples'] == 2
        assert result['max_deviation'] == 0.1
        assert not result['all_valid']
    
    def test_mass_balance_strict_mode(self):
        """Test strict mode raises on violations"""
        df = pd.DataFrame({
            'sample_id': ['bad'],
            'brass': [0.5],
            'copper': [0.3],
            's': [0.1],
            'goss': [0.05],
            'random': [0.0]  # Sum = 0.95, deviation = 0.05
        })
        
        with pytest.raises(ValueError):
            validate_dataset_mass_balance(df, strict=True)
    
    def test_mass_balance_edge_cases(self):
        """Test edge cases in mass balance validation"""
        # Empty DataFrame
        df_empty = pd.DataFrame(columns=['sample_id', 'brass', 'copper', 's', 'goss', 'random'])
        result_empty = validate_dataset_mass_balance(df_empty)
        assert result_empty['total_samples'] == 0
        assert result_empty['valid_rate'] == 0.0
        
        # DataFrame with NaN values
        df_nan = pd.DataFrame({
            'sample_id': ['nan_sample'],
            'brass': [np.nan],
            'copper': [0.3],
            's': [0.1],
            'goss': [0.2],
            'random': [0.4]
        })
        # Should handle NaN gracefully (fillna behavior in pandas)
        result_nan = validate_dataset_mass_balance(df_nan)
        # NaN in sum will result in NaN, which is > tolerance, so invalid
        assert 'mass_balance_valid' in result_nan['validated_df'].columns

if __name__ == "__main__":
    pytest.main([__file__, "-v"])