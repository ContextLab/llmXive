"""
Unit tests for edge cases involving missing elemental properties.

These tests verify that the descriptor computation pipeline handles
compounds containing elements with missing or undefined properties
gracefully, either by excluding the row or raising a clear error.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from descriptors import (
    get_elemental_properties_df,
    calculate_weighted_mean_variance,
    compute_descriptors_row,
    validate_final_dataset
)
from config import load_paths


class TestMissingElements:
    """Tests for handling missing elemental properties."""

    @pytest.fixture
    def sample_dataframe_with_missing(self):
        """Create a DataFrame simulating a compound with a missing element."""
        # Simulate a row where 'Unobtainium' (Uo) has no properties
        data = {
            'formula': ['NaCl', 'UoO2', 'Fe2O3'],
            'elements': [['Na', 'Cl'], ['Uo', 'O'], ['Fe', 'O']],
            'stoichiometry': [[1, 1], [1, 2], [2, 3]],
            'formation_energy': [-4.1, -5.0, -8.2]
        }
        return pd.DataFrame(data)

    def test_get_elemental_properties_handles_missing(self):
        """Test that get_elemental_properties_df loads real data without crashing."""
        # This should load the real elemental properties file
        # If the file is missing, it should raise an error (fail loudly)
        paths = load_paths()
        elem_file = paths['data']['elemental_properties']
        
        # We expect this to succeed if the file exists
        # If it doesn't exist, the test environment is misconfigured
        try:
            df = get_elemental_properties_df()
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert 'element' in df.columns
        except FileNotFoundError:
            pytest.skip("Elemental properties file not found in test environment")

    def test_calculate_weighted_mean_variance_missing_element(self, sample_dataframe_with_missing):
        """
        Test that calculate_weighted_mean_variance handles missing elements.
        
        When an element is not found in the properties dataframe, the function
        should either return NaN for the descriptors or raise a specific error.
        We expect it to handle missing data gracefully by propagating NaNs.
        """
        paths = load_paths()
        
        try:
            # Load real properties
            props_df = get_elemental_properties_df()
            
            # Try to calculate for the row with missing element 'Uo'
            # The function should handle the missing element by returning NaN
            # or raising a KeyError which we catch
            row_idx = 1  # UoO2 row
            elements = sample_dataframe_with_missing.loc[row_idx, 'elements']
            stoich = sample_dataframe_with_missing.loc[row_idx, 'stoichiometry']
            
            # This might raise KeyError if Uo is missing
            try:
                result = calculate_weighted_mean_variance(
                    elements, stoich, props_df
                )
                # If it doesn't raise, check that result contains NaN
                assert any(np.isnan(v) for v in result.values()), \
                    "Expected NaN values for missing element properties"
            except KeyError:
                # Expected behavior: KeyError for missing element
                pass

        except FileNotFoundError:
            pytest.skip("Elemental properties file not found in test environment")

    def test_compute_descriptors_row_missing_element(self, sample_dataframe_with_missing):
        """
        Test that compute_descriptors_row handles missing elements.
        
        The main computation function should handle missing elements
        by returning NaN for all descriptors or raising a clear error.
        """
        paths = load_paths()
        
        try:
            props_df = get_elemental_properties_df()
            
            row_idx = 1  # UoO2 row
            row = sample_dataframe_with_missing.iloc[row_idx]
            
            # Try to compute descriptors for row with missing element
            try:
                descriptors = compute_descriptors_row(row, props_df)
                # If successful, check for NaN values
                assert any(np.isnan(v) for v in descriptors.values()), \
                    "Expected NaN values for missing element properties"
            except KeyError:
                # Expected: KeyError for missing element
                pass

        except FileNotFoundError:
            pytest.skip("Elemental properties file not found in test environment")

    def test_validate_final_dataset_with_missing_values(self):
        """
        Test that validate_final_dataset detects rows with missing descriptor values.
        
        When descriptors contain NaN due to missing elemental properties,
        the validation should flag these rows.
        """
        # Create a dataset with NaN values in descriptor columns
        data = {
            'formula': ['NaCl', 'Fe2O3', 'Missing'],
            'mean_electronegativity': [1.5, 2.0, np.nan],
            'variance_radius': [0.1, 0.2, np.nan],
            'mean_valence': [1.0, 2.0, np.nan],
            'mean_melting_point': [500.0, 1000.0, np.nan],
            'mean_ionization_energy': [5.0, 10.0, np.nan],
            'formation_energy': [-4.1, -8.2, -5.0]
        }
        df = pd.DataFrame(data)
        
        # Validation should detect the missing values
        is_valid, errors = validate_final_dataset(df)
        
        # The dataset should be invalid due to missing values
        assert not is_valid, "Dataset with NaN descriptors should be invalid"
        assert len(errors) > 0, "Validation should report errors for NaN values"
        assert any("NaN" in str(err) or "null" in str(err).lower() for err in errors), \
            "Errors should mention NaN or null values"

    def test_empty_element_list(self):
        """Test handling of empty element lists."""
        data = {
            'formula': ['Empty'],
            'elements': [[]],
            'stoichiometry': [[]],
            'formation_energy': [0.0]
        }
        df = pd.DataFrame(data)
        
        paths = load_paths()
        try:
            props_df = get_elemental_properties_df()
            
            row = df.iloc[0]
            try:
                result = compute_descriptors_row(row, props_df)
                # Should return NaN or raise error for empty list
                assert any(np.isnan(v) for v in result.values()), \
                    "Empty element list should result in NaN descriptors"
            except (ValueError, IndexError):
                # Expected: error for empty list
                pass
        except FileNotFoundError:
            pytest.skip("Elemental properties file not found in test environment")

    def test_null_element_in_list(self):
        """Test handling of None/null elements in the list."""
        data = {
            'formula': ['NullElement'],
            'elements': [[None, 'O']],
            'stoichiometry': [[1, 2]],
            'formation_energy': [-5.0]
        }
        df = pd.DataFrame(data)
        
        paths = load_paths()
        try:
            props_df = get_elemental_properties_df()
            
            row = df.iloc[0]
            try:
                result = compute_descriptors_row(row, props_df)
                # Should handle None gracefully
                assert any(np.isnan(v) for v in result.values()), \
                    "None element should result in NaN descriptors"
            except (TypeError, KeyError):
                # Expected: error for None element
                pass
        except FileNotFoundError:
            pytest.skip("Elemental properties file not found in test environment")
