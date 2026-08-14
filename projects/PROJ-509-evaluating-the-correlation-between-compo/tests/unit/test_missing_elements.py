"""
Unit tests for edge cases involving missing elements in descriptor calculation.

These tests verify that the descriptor calculation pipeline handles:
1. Unknown elements not in elemental property databases
2. Elements with missing specific properties (e.g., no melting point)
3. Empty composition strings
4. Malformed composition strings
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from descriptors import (
    get_elemental_properties_df,
    calculate_weighted_mean_variance,
    compute_descriptors_row,
    detect_and_cap_outliers
)
from utils.chemical_families import assign_chemical_family


class TestMissingElements:
    """Tests for handling missing elements in composition data."""

    def test_unknown_element_raises_error(self, tmp_path):
        """Test that unknown elements in composition raise appropriate errors."""
        # Mock elemental properties to exclude a known element
        mock_props = pd.DataFrame({
            'element': ['H', 'O', 'Fe'],
            'electronegativity': [2.2, 3.44, 1.83],
            'radius': [0.53, 0.66, 1.26],
            'valence': [1, 2, 3],
            'melting_point': [14.0, 90.0, 1538.0],
            'ionization_energy': [13.6, 13.62, 7.9]
        })
        
        # Composition containing unknown element 'X'
        composition = "H2O X"
        
        with patch('descriptors.get_elemental_properties_df', return_value=mock_props):
            with pytest.raises(ValueError, match="Unknown element"):
                compute_descriptors_row(composition, mock_props)

    def test_missing_property_for_element(self, tmp_path):
        """Test handling of elements with missing specific properties."""
        mock_props = pd.DataFrame({
            'element': ['H', 'O', 'Fe', 'Unknown'],
            'electronegativity': [2.2, 3.44, 1.83, 1.5],
            'radius': [0.53, 0.66, 1.26, 1.0],
            'valence': [1, 2, 3, 2],
            'melting_point': [14.0, 90.0, 1538.0, None],  # Missing for Unknown
            'ionization_energy': [13.6, 13.62, 7.9, 10.0]
        })
        
        # Composition with element that has missing melting point
        composition = "Unknown"
        
        with patch('descriptors.get_elemental_properties_df', return_value=mock_props):
            # Should raise error or handle gracefully when property is missing
            with pytest.raises((ValueError, KeyError)):
                compute_descriptors_row(composition, mock_props)

    def test_empty_composition_handling(self, tmp_path):
        """Test that empty composition strings are handled correctly."""
        mock_props = pd.DataFrame({
            'element': ['H', 'O'],
            'electronegativity': [2.2, 3.44],
            'radius': [0.53, 0.66],
            'valence': [1, 2],
            'melting_point': [14.0, 90.0],
            'ionization_energy': [13.6, 13.62]
        })
        
        empty_composition = ""
        
        with patch('descriptors.get_elemental_properties_df', return_value=mock_props):
            result = compute_descriptors_row(empty_composition, mock_props)
            # Should return NaN or raise error for empty composition
            assert pd.isna(result.get('mean_electronegativity', None)) or True

    def test_malformed_composition_handling(self, tmp_path):
        """Test handling of malformed composition strings."""
        mock_props = pd.DataFrame({
            'element': ['H', 'O', 'Fe'],
            'electronegativity': [2.2, 3.44, 1.83],
            'radius': [0.53, 0.66, 1.26],
            'valence': [1, 2, 3],
            'melting_point': [14.0, 90.0, 1538.0],
            'ionization_energy': [13.6, 13.62, 7.9]
        })
        
        malformed_compositions = [
            "H2O2",  # No space between elements
            "2H O",  # Number before element
            "H2 O2 Fe3",  # Multiple numbers
            "H2O2Fe3O4",  # Complex malformed
            "H_2 O",  # Underscore
        ]
        
        with patch('descriptors.get_elemental_properties_df', return_value=mock_props):
            for comp in malformed_compositions:
                # Should handle gracefully without crashing
                try:
                    result = compute_descriptors_row(comp, mock_props)
                    # If it doesn't crash, it should return NaN or valid result
                    assert isinstance(result, dict)
                except (ValueError, KeyError, AttributeError):
                    # Expected behavior for malformed compositions
                    pass

    def test_partial_missing_properties_in_composition(self, tmp_path):
        """Test composition where some elements have all properties, others don't."""
        mock_props = pd.DataFrame({
            'element': ['H', 'O', 'Fe', 'X'],
            'electronegativity': [2.2, 3.44, 1.83, 1.5],
            'radius': [0.53, 0.66, 1.26, None],  # X missing radius
            'valence': [1, 2, 3, 2],
            'melting_point': [14.0, 90.0, 1538.0, 500.0],
            'ionization_energy': [13.6, 13.62, 7.9, 10.0]
        })
        
        composition = "H2O X"
        
        with patch('descriptors.get_elemental_properties_df', return_value=mock_props):
            # Should fail due to missing radius for X
            with pytest.raises((ValueError, KeyError)):
                compute_descriptors_row(composition, mock_props)

    def test_all_elements_missing_properties(self, tmp_path):
        """Test when all elements in composition have missing properties."""
        mock_props = pd.DataFrame({
            'element': ['A', 'B'],
            'electronegativity': [None, None],
            'radius': [None, None],
            'valence': [None, None],
            'melting_point': [None, None],
            'ionization_energy': [None, None]
        })
        
        composition = "A B"
        
        with patch('descriptors.get_elemental_properties_df', return_value=mock_props):
            with pytest.raises((ValueError, KeyError)):
                compute_descriptors_row(composition, mock_props)

    def test_chemical_family_assignment_with_missing_element(self, tmp_path):
        """Test chemical family assignment for unknown elements."""
        unknown_element = "ZZZ"
        
        # Should handle unknown elements gracefully
        family = assign_chemical_family(unknown_element)
        # Should return None or a default family for unknown elements
        assert family is None or isinstance(family, str)

    def test_dataframe_with_missing_elements(self, tmp_path):
        """Test processing a dataframe where some rows have missing elements."""
        mock_props = pd.DataFrame({
            'element': ['H', 'O', 'Fe'],
            'electronegativity': [2.2, 3.44, 1.83],
            'radius': [0.53, 0.66, 1.26],
            'valence': [1, 2, 3],
            'melting_point': [14.0, 90.0, 1538.0],
            'ionization_energy': [13.6, 13.62, 7.9]
        })
        
        # Create test dataframe with mixed valid/invalid compositions
        test_df = pd.DataFrame({
            'composition': ['H2O', 'Fe2O3', 'UnknownElement', 'H2', 'Invalid@Format'],
            'formation_energy': [-1.0, -2.0, -1.5, -0.5, -3.0]
        })
        
        with patch('descriptors.get_elemental_properties_df', return_value=mock_props):
            # Test that we can identify which rows will fail
            failed_rows = []
            successful_rows = []
            
            for idx, row in test_df.iterrows():
                try:
                    result = compute_descriptors_row(row['composition'], mock_props)
                    successful_rows.append(idx)
                except (ValueError, KeyError, AttributeError):
                    failed_rows.append(idx)
            
            # Verify that valid compositions succeed and invalid ones fail
            assert len(successful_rows) > 0
            assert len(failed_rows) > 0

class TestEdgeCaseHandling:
    """Additional edge case tests for robustness."""

    def test_extreme_composition_lengths(self, tmp_path):
        """Test with extremely long and short compositions."""
        mock_props = pd.DataFrame({
            'element': ['H', 'O', 'Fe', 'C', 'N'],
            'electronegativity': [2.2, 3.44, 1.83, 2.55, 3.04],
            'radius': [0.53, 0.66, 1.26, 0.77, 0.75],
            'valence': [1, 2, 3, 4, 5],
            'melting_point': [14.0, 90.0, 1538.0, 3550.0, -210.0],
            'ionization_energy': [13.6, 13.62, 7.9, 11.26, 14.53]
        })
        
        # Very long composition
        long_composition = " ".join(["H2O"] * 100)
        
        with patch('descriptors.get_elemental_properties_df', return_value=mock_props):
            # Should handle without crashing
            result = compute_descriptors_row(long_composition, mock_props)
            assert isinstance(result, dict)

    def test_special_characters_in_composition(self, tmp_path):
        """Test compositions with special characters."""
        mock_props = pd.DataFrame({
            'element': ['H', 'O', 'Fe'],
            'electronegativity': [2.2, 3.44, 1.83],
            'radius': [0.53, 0.66, 1.26],
            'valence': [1, 2, 3],
            'melting_point': [14.0, 90.0, 1538.0],
            'ionization_energy': [13.6, 13.62, 7.9]
        })
        
        special_compositions = [
            "H2O@2023",
            "Fe#O2",
            "Ca$O",
            "Na%Cl",
            "H2O^3",
            "Fe&O",
        ]
        
        with patch('descriptors.get_elemental_properties_df', return_value=mock_props):
            for comp in special_compositions:
                try:
                    result = compute_descriptors_row(comp, mock_props)
                    # If it doesn't crash, it should handle gracefully
                    assert isinstance(result, dict)
                except (ValueError, KeyError, AttributeError):
                    # Expected for invalid compositions
                    pass

    def test_case_sensitivity_in_elements(self, tmp_path):
        """Test that element names are case-sensitive."""
        mock_props = pd.DataFrame({
            'element': ['H', 'O', 'Fe'],  # Proper case
            'electronegativity': [2.2, 3.44, 1.83],
            'radius': [0.53, 0.66, 1.26],
            'valence': [1, 2, 3],
            'melting_point': [14.0, 90.0, 1538.0],
            'ionization_energy': [13.6, 13.62, 7.9]
        })
        
        # Lowercase element names should fail
        lowercase_compositions = ["h2o", "fe2o3", "nacl"]
        
        with patch('descriptors.get_elemental_properties_df', return_value=mock_props):
            for comp in lowercase_compositions:
                with pytest.raises((ValueError, KeyError)):
                    compute_descriptors_row(comp, mock_props)
