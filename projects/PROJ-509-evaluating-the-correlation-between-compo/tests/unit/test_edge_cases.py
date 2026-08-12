"""
Additional unit tests for various edge cases in the descriptor computation pipeline.

This file aggregates tests for edge cases that don't fit neatly into
the missing elements or extreme outliers categories.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from descriptors import (
    calculate_weighted_mean_variance,
    compute_descriptors_row,
    validate_final_dataset
)
from config import load_paths


class TestEdgeCases:
    """Tests for various edge cases."""

    @pytest.fixture
    def minimal_elemental_properties(self):
        """Create a minimal elemental properties DataFrame for testing."""
        data = {
            'element': ['H', 'He', 'Li', 'Be', 'B'],
            'electronegativity': [2.20, 0.0, 0.98, 1.57, 2.04],
            'atomic_radius': [37.0, 31.0, 152.0, 112.0, 85.0],
            'valence': [1, 0, 1, 2, 3],
            'melting_point': [14.0, 0.0, 180.0, 1560.0, 2300.0],
            'ionization_energy': [13.6, 24.6, 5.4, 9.3, 8.3]
        }
        return pd.DataFrame(data)

    def test_zero_stoichiometry(self, minimal_elemental_properties):
        """Test handling of zero stoichiometry values."""
        elements = ['H', 'O']
        stoichiometry = [1, 0]  # O has zero stoichiometry
        
        # This should handle zero stoichiometry gracefully
        # Either return NaN or skip the zero-stoichiometry element
        try:
            result = calculate_weighted_mean_variance(
                elements, stoichiometry, minimal_elemental_properties
            )
            # If it succeeds, check the result
            assert isinstance(result, dict)
        except (ValueError, ZeroDivisionError):
            # Expected: error when dividing by zero total stoichiometry
            pass

    def test_negative_stoichiometry(self, minimal_elemental_properties):
        """Test handling of negative stoichiometry values."""
        elements = ['H', 'O']
        stoichiometry = [1, -1]  # Negative stoichiometry is invalid
        
        try:
            result = calculate_weighted_mean_variance(
                elements, stoichiometry, minimal_elemental_properties
            )
            # If it succeeds, the function handled it gracefully
            assert isinstance(result, dict)
        except ValueError:
            # Expected: negative stoichiometry is invalid
            pass

    def test_empty_dataframe_validation(self):
        """Test validation of an empty DataFrame."""
        df = pd.DataFrame(columns=[
            'formula', 'formation_energy', 'mean_electronegativity',
            'variance_radius', 'mean_valence', 'mean_melting_point',
            'mean_ionization_energy'
        ])
        
        is_valid, errors = validate_final_dataset(df)
        
        # Empty dataset should be invalid
        assert not is_valid, "Empty dataset should be invalid"
        assert len(errors) > 0, "Validation should report errors for empty dataset"

    def test_single_column_dataset(self):
        """Test validation of a dataset with only one column."""
        df = pd.DataFrame({
            'formula': ['NaCl']
        })
        
        is_valid, errors = validate_final_dataset(df)
        
        # Missing required columns should make it invalid
        assert not is_valid, "Dataset with missing columns should be invalid"
        assert len(errors) > 0, "Validation should report missing columns"

    def test_all_nan_column(self):
        """Test validation of a dataset with all NaN in a descriptor column."""
        df = pd.DataFrame({
            'formula': ['A', 'B', 'C'],
            'formation_energy': [-5.0, -6.0, -7.0],
            'mean_electronegativity': [np.nan, np.nan, np.nan],
            'variance_radius': [0.1, 0.2, 0.3],
            'mean_valence': [1.0, 2.0, 3.0],
            'mean_melting_point': [1000.0, 1100.0, 1200.0],
            'mean_ionization_energy': [7.0, 8.0, 9.0]
        })
        
        is_valid, errors = validate_final_dataset(df)
        
        # All NaN in a descriptor column should make it invalid
        assert not is_valid, "Dataset with all-NaN descriptor should be invalid"
        assert any("NaN" in str(err) or "null" in str(err).lower() for err in errors), \
            "Errors should mention NaN values"

    def test_infinite_values(self):
        """Test handling of infinite values in descriptors."""
        df = pd.DataFrame({
            'formula': ['A', 'B', 'C'],
            'formation_energy': [-5.0, -6.0, -7.0],
            'mean_electronegativity': [1.5, np.inf, 2.5],
            'variance_radius': [0.1, 0.2, 0.3],
            'mean_valence': [1.0, 2.0, 3.0],
            'mean_melting_point': [1000.0, 1100.0, 1200.0],
            'mean_ionization_energy': [7.0, 8.0, 9.0]
        })
        
        is_valid, errors = validate_final_dataset(df)
        
        # Infinite values should make it invalid
        assert not is_valid, "Dataset with infinite values should be invalid"
        assert any("inf" in str(err).lower() for err in errors), \
            "Errors should mention infinite values"

    def test_string_values_in_numeric_columns(self):
        """Test validation of string values in numeric columns."""
        df = pd.DataFrame({
            'formula': ['A', 'B', 'C'],
            'formation_energy': [-5.0, -6.0, -7.0],
            'mean_electronegativity': [1.5, 'invalid', 2.5],
            'variance_radius': [0.1, 0.2, 0.3],
            'mean_valence': [1.0, 2.0, 3.0],
            'mean_melting_point': [1000.0, 1100.0, 1200.0],
            'mean_ionization_energy': [7.0, 8.0, 9.0]
        })
        
        is_valid, errors = validate_final_dataset(df)
        
        # String values in numeric columns should make it invalid
        assert not is_valid, "Dataset with string in numeric column should be invalid"

    def test_very_large_values(self):
        """Test handling of very large (but finite) values."""
        df = pd.DataFrame({
            'formula': ['A', 'B', 'C'],
            'formation_energy': [-5.0, -6.0, -7.0],
            'mean_electronegativity': [1.5, 1e100, 2.5],
            'variance_radius': [0.1, 0.2, 0.3],
            'mean_valence': [1.0, 2.0, 3.0],
            'mean_melting_point': [1000.0, 1100.0, 1200.0],
            'mean_ionization_energy': [7.0, 8.0, 9.0]
        })
        
        is_valid, errors = validate_final_dataset(df)
        
        # Very large values might be valid (depending on implementation)
        # but should be handled without crashing
        # The function should not crash even if it considers them valid
        assert isinstance(is_valid, bool), "Validation should return boolean"

    def test_duplicate_formulas(self):
        """Test handling of duplicate formulas in dataset."""
        df = pd.DataFrame({
            'formula': ['NaCl', 'NaCl', 'Fe2O3'],
            'formation_energy': [-5.0, -5.0, -8.2],
            'mean_electronegativity': [1.5, 1.5, 2.0],
            'variance_radius': [0.1, 0.1, 0.2],
            'mean_valence': [1.0, 1.0, 2.0],
            'mean_melting_point': [1000.0, 1000.0, 1100.0],
            'mean_ionization_energy': [7.0, 7.0, 8.0]
        })
        
        # This should not crash
        is_valid, errors = validate_final_dataset(df)
        
        # Duplicate formulas might be valid or invalid depending on requirements
        # The important thing is that it doesn't crash
        assert isinstance(is_valid, bool), "Validation should return boolean"

    def test_special_characters_in_formula(self):
        """Test handling of special characters in chemical formulas."""
        data = {
            'formula': ['NaCl', 'Fe2O3', 'H2SO4', 'Ca(OH)2', 'Na2CO3·10H2O'],
            'formation_energy': [-5.0, -8.2, -9.0, -12.0, -5.5],
            'mean_electronegativity': [1.5, 2.0, 2.5, 1.8, 1.6],
            'variance_radius': [0.1, 0.2, 0.3, 0.25, 0.15],
            'mean_valence': [1.0, 2.0, 3.0, 2.5, 1.5],
            'mean_melting_point': [1000.0, 1100.0, 1200.0, 1300.0, 1050.0],
            'mean_ionization_energy': [7.0, 8.0, 9.0, 8.5, 7.5]
        }
        df = pd.DataFrame(data)
        
        # Should not crash with special characters
        is_valid, errors = validate_final_dataset(df)
        assert isinstance(is_valid, bool), "Validation should handle special characters"

    def test_unicode_characters(self):
        """Test handling of unicode characters in formulas."""
        df = pd.DataFrame({
            'formula': ['NaCl', 'Fe₂O₃', 'H₂SO₄'],  # Unicode subscripts
            'formation_energy': [-5.0, -8.2, -9.0],
            'mean_electronegativity': [1.5, 2.0, 2.5],
            'variance_radius': [0.1, 0.2, 0.3],
            'mean_valence': [1.0, 2.0, 3.0],
            'mean_melting_point': [1000.0, 1100.0, 1200.0],
            'mean_ionization_energy': [7.0, 8.0, 9.0]
        })
        
        # Should not crash with unicode
        is_valid, errors = validate_final_dataset(df)
        assert isinstance(is_valid, bool), "Validation should handle unicode"
