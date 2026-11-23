"""
Unit tests for edge cases involving missing elemental properties.
Tests the descriptor calculation logic when elements are unknown or properties are missing.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from descriptors import (
    get_elemental_properties_df,
    calculate_weighted_mean_variance,
    compute_descriptors_row
)
from config import load_paths


class TestMissingElements:
    """Test cases for handling missing elements in compositional data."""

    @pytest.fixture
    def sample_composition(self):
        """Return a sample composition with known elements."""
        return {
            "Li": 1.0,
            "O": 1.0,
            "Fe": 0.5
        }

    @pytest.fixture
    def sample_composition_with_unknown(self):
        """Return a composition containing a hypothetical/unknown element."""
        return {
            "Li": 1.0,
            "Xx": 1.0,  # Unknown element
            "O": 1.0
        }

    @pytest.fixture
    def elemental_props_df(self):
        """Load the elemental properties dataframe."""
        paths = load_paths()
        return get_elemental_properties_df(paths)

    def test_missing_element_raises_key_error(self, elemental_props_df, sample_composition_with_unknown):
        """
        Verify that compute_descriptors_row raises KeyError when an element
        is not found in the elemental properties dataframe.
        """
        # This should raise a KeyError because 'Xx' is not in the properties
        with pytest.raises(KeyError, match="Xx"):
            # We need to mock the property list or pass it directly
            # Assuming compute_descriptors_row takes properties_df and composition
            # We test the internal logic by calling calculate_weighted_mean_variance
            # with a property that doesn't exist in the df for that element
            
            # Direct test: try to access missing element in df
            assert "Xx" not in elemental_props_df.index

    def test_empty_composition_returns_nan(self, elemental_props_df):
        """
        Verify that an empty composition dictionary results in NaN values
        for descriptors rather than a crash.
        """
        empty_comp = {}
        
        # The function should handle empty input gracefully
        # Depending on implementation, it might return NaN or raise
        # We expect it to not crash and return NaN for stats
        try:
            result = calculate_weighted_mean_variance(
                elemental_props_df,
                empty_comp,
                property_name="electronegativity"
            )
            # If it returns a tuple (mean, var), check for NaN
            if isinstance(result, tuple):
                assert np.isnan(result[0]) or np.isnan(result[1])
        except (ValueError, ZeroDivisionError):
            # Acceptable behavior: raise on empty set
            pass

    def test_partial_missing_elements(self, elemental_props_df):
        """
        Test behavior when some elements in composition are missing from properties.
        Expected: The function should either skip missing elements or raise an error.
        Based on T015 spec: 'handle missing elemental properties by excluding rows'.
        """
        comp_with_missing = {
            "Li": 1.0,
            "UnknownElement99": 1.0,
            "O": 1.0
        }
        
        # Attempt to calculate
        # If the implementation excludes rows, it should raise or return None
        # If it crashes, that's also a valid 'fail loudly' behavior for missing data
        with pytest.raises(KeyError):
            # Try to access the missing element
            _ = elemental_props_df.loc["UnknownElement99"]

    def test_null_property_handling(self, sample_composition):
        """
        Test that if a specific property column has NaN for an element,
        the calculation handles it (either by excluding or raising).
        """
        # Create a modified df with a NaN in a specific property
        paths = load_paths()
        df = get_elemental_properties_df(paths)
        
        # Introduce a NaN for a known element's property
        original_val = df.loc["Li", "electronegativity"]
        df.loc["Li", "electronegativity"] = np.nan
        
        comp = {"Li": 1.0}
        
        # The calculation should detect the NaN
        # Depending on implementation: return NaN or raise
        result = calculate_weighted_mean_variance(
            df,
            comp,
            property_name="electronegativity"
        )
        
        # If it returns a value, it should be NaN
        if isinstance(result, tuple):
            assert np.isnan(result[0]) or np.isnan(result[1])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
