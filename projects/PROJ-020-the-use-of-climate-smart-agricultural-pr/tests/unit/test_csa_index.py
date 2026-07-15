"""
Unit tests for CSA Index construction in code/data/features.py

These tests verify:
1. Correct construction of the weighted composite score
2. Proper exclusion of digital/finance variables
3. Normalization to [0, 1] range
4. Error handling for missing columns
5. Statistical validity of the index
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.features import (
    construct_csa_index,
    calculate_component_statistics,
    validate_csa_components,
    CSA_COMPONENTS,
    EXCLUDED_VARIABLES
)


class TestCSAIndexConstruction:
    """Test suite for CSA Index construction functions."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data with all required CSA components."""
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'household_id': range(n),
            'country': np.random.choice(['KEN', 'IND', 'VNM'], n),
            'conservation_tillage_score': np.random.beta(2, 2, n),
            'crop_diversity_index': np.random.beta(3, 2, n),
            'irrigation_efficiency_score': np.random.beta(2, 3, n),
            # Excluded variables
            'digital_technology_access': np.random.beta(2, 2, n),
            'finance_access_score': np.random.beta(3, 2, n)
        })
    
    def test_construct_index_returns_dataframe(self, sample_data):
        """Test that construct_csa_index returns a DataFrame."""
        result = construct_csa_index(sample_data)
        assert isinstance(result, pd.DataFrame)
        assert 'csa_index' in result.columns
    
    def test_construct_index_normalization(self, sample_data):
        """Test that the index is normalized to [0, 1]."""
        result = construct_csa_index(sample_data, normalize=True)
        csa_min = result['csa_index'].min()
        csa_max = result['csa_index'].max()
        
        assert csa_min >= 0.0, f"Min value {csa_min} is below 0"
        assert csa_max <= 1.0, f"Max value {csa_max} is above 1"
    
    def test_construct_index_missing_column(self, sample_data):
        """Test error handling when a required column is missing."""
        df_missing = sample_data.drop(columns=['conservation_tillage_score'])
        
        with pytest.raises(ValueError) as exc_info:
            construct_csa_index(df_missing)
        
        assert 'conservation_tillage_score' in str(exc_info.value)
    
    def test_construct_index_excludes_variables(self, sample_data):
        """Test that excluded variables are not used in index construction."""
        # Try to include an excluded variable in components
        bad_components = {
            'conservation_tillage_score': 0.5,
            'digital_technology_access': 0.5  # This should fail
        }
        
        with pytest.raises(ValueError) as exc_info:
            construct_csa_index(sample_data, components=bad_components)
        
        assert 'digital_technology_access' in str(exc_info.value)
    
    def test_construct_index_weighted_sum(self, sample_data):
        """Test that the index is a proper weighted sum."""
        # Use known weights for testing
        test_components = {
            'conservation_tillage_score': 0.5,
            'crop_diversity_index': 0.3,
            'irrigation_efficiency_score': 0.2
        }
        
        result = construct_csa_index(sample_data, components=test_components, normalize=False)
        
        # Calculate expected weighted sum manually
        expected = (
            sample_data['conservation_tillage_score'] * 0.5 +
            sample_data['crop_diversity_index'] * 0.3 +
            sample_data['irrigation_efficiency_score'] * 0.2
        )
        
        # Check if they match (before normalization)
        np.testing.assert_array_almost_equal(
            result['csa_index'].values,
            expected.values,
            decimal=10
        )
    
    def test_construct_index_constant_values(self, sample_data):
        """Test handling when all component values are constant."""
        df_constant = sample_data.copy()
        df_constant['conservation_tillage_score'] = 0.5
        df_constant['crop_diversity_index'] = 0.5
        df_constant['irrigation_efficiency_score'] = 0.5
        
        result = construct_csa_index(df_constant, normalize=True)
        
        # All values should be 0.5 (middle of range)
        assert all(result['csa_index'] == 0.5), "Constant inputs should produce constant output"
    
    def test_calculate_component_statistics(self, sample_data):
        """Test component statistics calculation."""
        stats = calculate_component_statistics(sample_data)
        
        # Check that all components have statistics
        for col in CSA_COMPONENTS.keys():
            assert col in stats, f"Missing statistics for {col}"
            assert 'mean' in stats[col], f"Missing 'mean' for {col}"
            assert 'std' in stats[col], f"Missing 'std' for {col}"
    
    def test_validate_csa_components_valid(self, sample_data):
        """Test validation with valid data."""
        is_valid, errors = validate_csa_components(sample_data)
        
        assert is_valid, f"Validation failed with errors: {errors}"
        assert len(errors) == 0
    
    def test_validate_csa_components_missing(self, sample_data):
        """Test validation with missing columns."""
        df_missing = sample_data.drop(columns=['conservation_tillage_score'])
        is_valid, errors = validate_csa_components(df_missing)
        
        assert not is_valid
        assert any('conservation_tillage_score' in error for error in errors)
    
    def test_index_distribution(self, sample_data):
        """Test that the index has a reasonable distribution."""
        result = construct_csa_index(sample_data)
        
        # Check that the index is not all zeros or ones
        assert result['csa_index'].std() > 0.01, "Index should have variance"
        
        # Check that the mean is reasonable (not too close to boundaries)
        mean_val = result['csa_index'].mean()
        assert 0.1 < mean_val < 0.9, f"Mean {mean_val} is too close to boundaries"
    
    def test_different_countries(self, sample_data):
        """Test that index construction works across different countries."""
        for country in ['KEN', 'IND', 'VNM']:
            country_data = sample_data[sample_data['country'] == country].copy()
            
            if len(country_data) > 0:
                result = construct_csa_index(country_data)
                assert 'csa_index' in result.columns
                assert not result['csa_index'].isna().any()
    
    def test_missing_values_handling(self):
        """Test handling of missing values in components."""
        df_with_missing = pd.DataFrame({
            'conservation_tillage_score': [0.5, np.nan, 0.7],
            'crop_diversity_index': [0.6, 0.4, np.nan],
            'irrigation_efficiency_score': [0.3, 0.5, 0.6]
        })
        
        # Should not raise an error, but fill NaN with 0
        result = construct_csa_index(df_with_missing)
        
        # Check that no NaN values in the result
        assert not result['csa_index'].isna().any(), "Result should not have NaN values"
    
    def test_weight_normalization(self):
        """Test that weights are properly normalized even if they don't sum to 1."""
        df = pd.DataFrame({
            'conservation_tillage_score': [0.5],
            'crop_diversity_index': [0.6],
            'irrigation_efficiency_score': [0.7]
        })
        
        # Weights that don't sum to 1
        bad_weights = {
            'conservation_tillage_score': 2,
            'crop_diversity_index': 3,
            'irrigation_efficiency_score': 5
        }  # Sum = 10
        
        result = construct_csa_index(df, components=bad_weights, normalize=False)
        
        # Manual calculation: (0.5*2 + 0.6*3 + 0.7*5) / 10 = (1 + 1.8 + 3.5) / 10 = 0.63
        expected = (0.5*2 + 0.6*3 + 0.7*5) / 10
        
        assert abs(result['csa_index'].iloc[0] - expected) < 1e-10


class TestExcludedVariables:
    """Test that excluded variables are properly handled."""
    
    def test_excluded_variables_list(self):
        """Test that the excluded variables list is defined."""
        assert len(EXCLUDED_VARIABLES) > 0
        assert 'digital_technology_access' in EXCLUDED_VARIABLES
        assert 'finance_access_score' in EXCLUDED_VARIABLES
    
    def test_no_excluded_in_default_components(self):
        """Test that default components don't include excluded variables."""
        overlap = set(CSA_COMPONENTS.keys()) & set(EXCLUDED_VARIABLES)
        assert len(overlap) == 0, f"Default components should not include: {overlap}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])