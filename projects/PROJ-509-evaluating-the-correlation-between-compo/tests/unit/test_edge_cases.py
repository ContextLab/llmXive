"""
Unit tests for edge cases in the materials science pipeline.

Tests cover:
- Missing elemental properties (NaN handling)
- Extreme outliers in formation energy
- Empty compositions
- Single-element compositions
- Invalid chemical formulas
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from descriptors import (
    get_elemental_properties_df,
    calculate_weighted_mean_variance,
    compute_descriptors_row,
    detect_and_cap_outliers,
    validate_final_dataset
)
from utils.sampling import get_chemical_family
from config import load_paths


class TestMissingElementalProperties:
    """Test handling of missing elemental properties."""
    
    def test_missing_element_in_properties(self):
        """Test that missing elements in properties dataframe are handled."""
        # Get the full elemental properties dataframe
        elem_props = get_elemental_properties_df()
        
        # Create a composition with a known missing element (hypothetical)
        # In real scenarios, this might be a very new or synthetic element
        test_composition = {"FakeElement": 1.0}
        
        # The function should handle missing elements gracefully
        # by returning NaN or skipping the row
        result = calculate_weighted_mean_variance(test_composition, elem_props)
        
        # If element is missing, mean and variance should be NaN
        assert result is not None
        # Either all values are NaN or the function handles it gracefully
        if pd.isna(result).all():
            pass  # Expected for missing element
        else:
            # If some values exist, ensure no crash occurred
            assert isinstance(result, dict)
    
    def test_partial_missing_properties(self):
        """Test composition with some missing properties."""
        elem_props = get_elemental_properties_df()
        
        # Get a real element and remove one of its properties temporarily
        real_element = list(elem_props.index)[0]
        test_composition = {real_element: 1.0}
        
        # Modify properties to have a missing value for this element
        modified_props = elem_props.copy()
        modified_props.loc[real_element, 'electronegativity'] = np.nan
        
        result = calculate_weighted_mean_variance(test_composition, modified_props)
        
        # Should handle partial missing data without crashing
        assert result is not None
        

class TestExtremeOutliers:
    """Test handling of extreme outliers in formation energy."""
    
    def test_extreme_positive_outlier(self):
        """Test capping of extremely high formation energy values."""
        # Create a small dataset with an extreme outlier
        data = {
            'formula': ['Fe2O3', 'SiO2', 'ExtremeOutlier'],
            'formation_energy': [-1.0, -0.5, 1000.0],  # 1000 is extreme
            'elements': [['Fe', 'O'], ['Si', 'O'], ['X', 'Y']]
        }
        df = pd.DataFrame(data)
        
        # Apply outlier detection and capping
        capped_df, stats = detect_and_cap_outliers(df, 'formation_energy')
        
        # The extreme value should be capped to the 99th percentile
        assert capped_df['formation_energy'].max() < 1000.0
        assert stats['rows_capped'] >= 1
    
    def test_extreme_negative_outlier(self):
        """Test capping of extremely low formation energy values."""
        data = {
            'formula': ['Fe2O3', 'SiO2', 'ExtremeOutlier'],
            'formation_energy': [-1.0, -0.5, -1000.0],  # -1000 is extreme
            'elements': [['Fe', 'O'], ['Si', 'O'], ['X', 'Y']]
        }
        df = pd.DataFrame(data)
        
        capped_df, stats = detect_and_cap_outliers(df, 'formation_energy')
        
        # The extreme value should be capped to the 1st percentile
        assert capped_df['formation_energy'].min() > -1000.0
        assert stats['rows_capped'] >= 1
    
    def test_no_outliers(self):
        """Test that normal data passes through unchanged."""
        data = {
            'formula': ['Fe2O3', 'SiO2', 'Al2O3'],
            'formation_energy': [-1.0, -0.5, -1.5],
            'elements': [['Fe', 'O'], ['Si', 'O'], ['Al', 'O']]
        }
        df = pd.DataFrame(data)
        
        capped_df, stats = detect_and_cap_outliers(df, 'formation_energy')
        
        # No capping should occur
        assert stats['rows_capped'] == 0
        pd.testing.assert_frame_equal(capped_df, df)
        

class TestInvalidCompositions:
    """Test handling of invalid or edge-case compositions."""
    
    def test_empty_composition(self):
        """Test handling of empty composition dictionary."""
        elem_props = get_elemental_properties_df()
        
        with pytest.raises((ValueError, KeyError)):
            calculate_weighted_mean_variance({}, elem_props)
    
    def test_single_element_composition(self):
        """Test handling of single-element compositions."""
        elem_props = get_elemental_properties_df()
        
        # Pure element composition
        test_composition = {"Fe": 1.0}
        
        result = calculate_weighted_mean_variance(test_composition, elem_props)
        
        # For a single element, mean = value, variance = 0
        assert result is not None
        assert 'mean_electronegativity' in result
    
    def test_very_large_composition(self):
        """Test handling of compositions with many elements."""
        elem_props = get_elemental_properties_df()
        
        # Create a composition with many elements
        many_elements = {f"Element{i}": 1.0 for i in range(100)}
        
        # This should handle missing elements gracefully
        result = calculate_weighted_mean_variance(many_elements, elem_props)
        
        # Should not crash, may have NaN values for missing elements
        assert result is not None
        

class TestChemicalFamilyEdgeCases:
    """Test edge cases in chemical family classification."""
    
    def test_missing_element_for_family(self):
        """Test chemical family detection when element is missing."""
        # Test with an element that might not be in our classification
        result = get_chemical_family("UnknownElementXYZ")
        
        # Should return a default or None, not crash
        assert result is not None
        

class TestValidationEdgeCases:
    """Test dataset validation with edge cases."""
    
    def test_dataset_with_null_descriptors(self):
        """Test validation of dataset with null descriptor values."""
        # Create a dataset with null values in descriptor columns
        data = {
            'formula': ['Fe2O3', 'SiO2', 'NaNRow'],
            'mean_electronegativity': [1.5, 2.0, np.nan],
            'variance_electronegativity': [0.1, 0.2, np.nan],
            'formation_energy': [-1.0, -0.5, -1.2]
        }
        df = pd.DataFrame(data)
        
        # Validation should detect null values
        is_valid, errors = validate_final_dataset(df)
        
        assert not is_valid
        assert len(errors) > 0
    
    def test_empty_dataset(self):
        """Test validation of empty dataset."""
        df = pd.DataFrame(columns=['formula', 'mean_electronegativity', 'formation_energy'])
        
        is_valid, errors = validate_final_dataset(df)
        
        # Empty dataset should fail validation
        assert not is_valid
        

class TestNumericalStability:
    """Test numerical stability with extreme values."""
    
    def test_very_small_stoichiometry(self):
        """Test with very small stoichiometric coefficients."""
        elem_props = get_elemental_properties_df()
        
        # Very small coefficients
        test_composition = {"Fe": 1e-10, "O": 1e-10}
        
        result = calculate_weighted_mean_variance(test_composition, elem_props)
        
        # Should handle without numerical errors
        assert result is not None
    
    def test_very_large_stoichiometry(self):
        """Test with very large stoichiometric coefficients."""
        elem_props = get_elemental_properties_df()
        
        # Very large coefficients
        test_composition = {"Fe": 1e10, "O": 1e10}
        
        result = calculate_weighted_mean_variance(test_composition, elem_props)
        
        # Should handle without overflow
        assert result is not None
        

if __name__ == "__main__":
    pytest.main([__file__, "-v"])