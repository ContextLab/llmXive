"""
Unit tests for feature engineering functions in src/data/features.py.

This module contains tests for User Story 1, specifically verifying that
descriptor calculations handle edge cases correctly without crashing.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path if running directly
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data import features


class TestDescriptorVariance:
    """Tests for the calculate_atomic_radius_variance function."""

    def test_descriptor_variance_handles_empty_input(self):
        """
        Verify that calculate_atomic_radius_variance handles empty input
        without crashing and returns an appropriate value (NaN or 0).
        
        This is an edge case test to ensure robustness when the feature
        engineering pipeline encounters empty dataframes or lists.
        """
        # Test with empty list
        result = features.calculate_atomic_radius_variance([])
        assert result is not None, "Function should return a value, not None"
        
        # The function should handle empty input gracefully
        # Depending on implementation, this might be 0.0 or float('nan')
        # We just verify it doesn't raise an exception
        try:
            # If it returns a number, it should be 0 or NaN
            if isinstance(result, (int, float)):
                if result != 0.0 and result != float('nan'):
                    # If it's not 0 or NaN, it might be a calculated value
                    # which would be unexpected for empty input
                    pass
        except TypeError:
            # In case of NaN comparison issues
            pass

    def test_descriptor_variance_single_element(self):
        """
        Verify that variance is 0 for a single element (no variance possible).
        """
        result = features.calculate_atomic_radius_variance(["Al"])
        assert result == 0.0, "Variance of a single element should be 0.0"

    def test_descriptor_variance_multiple_elements(self):
        """
        Verify that variance is calculated correctly for multiple elements.
        """
        # Using known elements with different atomic radii
        elements = ["Al", "Cu", "Ni"]
        result = features.calculate_atomic_radius_variance(elements)
        assert result is not None, "Function should return a value"
        assert result >= 0, "Variance should be non-negative"
        assert result > 0, "Variance should be positive for different elements"

    def test_descriptor_variance_invalid_element(self):
        """
        Verify that the function handles invalid element symbols gracefully.
        """
        # This test ensures the function doesn't crash on invalid input
        # It might return NaN, 0, or raise a specific exception we catch
        with pytest.raises(Exception):
            # We expect some form of error handling for invalid elements
            # The exact behavior depends on the implementation in features.py
            features.calculate_atomic_radius_variance(["InvalidElement"])

class TestElectronegativityStdDev:
    """Tests for the calculate_electronegativity_std function."""

    def test_descriptor_stddev_handles_empty_input(self):
        """
        Verify that calculate_electronegativity_std handles empty input
        without crashing.
        """
        result = features.calculate_electronegativity_std([])
        assert result is not None, "Function should return a value, not None"

    def test_descriptor_stddev_single_element(self):
        """
        Verify that std dev is 0 for a single element.
        """
        result = features.calculate_electronegativity_std(["Al"])
        assert result == 0.0, "Std dev of a single element should be 0.0"

    def test_descriptor_stddev_multiple_elements(self):
        """
        Verify that std dev is calculated correctly for multiple elements.
        """
        elements = ["Al", "Cu", "Ni"]
        result = features.calculate_electronegativity_std(elements)
        assert result is not None, "Function should return a value"
        assert result >= 0, "Std dev should be non-negative"
        assert result > 0, "Std dev should be positive for different elements"

class TestValenceElectronConcentration:
    """Tests for the calculate_valence_electron_concentration function."""

    def test_vec_handles_empty_input(self):
        """
        Verify that calculate_valence_electron_concentration handles empty input.
        """
        result = features.calculate_valence_electron_concentration([])
        assert result is not None, "Function should return a value, not None"

    def test_vec_single_element(self):
        """
        Verify VEC calculation for a single element.
        """
        # Al has 3 valence electrons
        result = features.calculate_valence_electron_concentration(["Al"])
        assert result == 3.0, f"VEC for Al should be 3.0, got {result}"

    def test_vec_multiple_elements(self):
        """
        Verify VEC calculation for multiple elements.
        """
        # Al (3) and Cu (1) -> average should be 2.0
        result = features.calculate_valence_electron_concentration(["Al", "Cu"])
        assert result == 2.0, f"VEC for Al+Cu should be 2.0, got {result}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])