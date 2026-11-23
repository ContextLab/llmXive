"""
Unit tests for feature engineering logic in code/data/features.py
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data.features import (
    parse_composition_string,
    compute_weighted_mean,
    compute_size_mismatch,
    compute_pairwise_size_mismatch,
    get_element_properties
)


class TestParseComposition:
    """Tests for parse_composition_string function"""

    def test_simple_ternary(self):
        """Test parsing a simple ternary composition"""
        comp = "Fe40.5Ni40.5B19"
        result = parse_composition_string(comp)

        assert len(result) == 3
        assert ("Fe", 40.5) in result
        assert ("Ni", 40.5) in result
        assert ("B", 19) in result

    def test_normalized_composition(self):
        """Test parsing composition that sums to 1"""
        comp = "Fe0.4Ni0.4B0.2"
        result = parse_composition_string(comp)

        assert len(result) == 3
        total = sum(frac for _, frac in result)
        assert abs(total - 1.0) < 0.01

    def test_empty_string(self):
        """Test handling of empty string"""
        comp = ""
        result = parse_composition_string(comp)
        assert result == []

    def test_invalid_format(self):
        """Test handling of invalid format"""
        comp = "invalid"
        result = parse_composition_string(comp)
        assert result == []


class TestElementProperties:
    """Tests for get_element_properties function"""

    def test_common_element(self):
        """Test fetching properties for a common element"""
        props = get_element_properties("Fe")
        assert props is not None
        assert 'atomic_radius' in props
        assert 'electronegativity' in props
        assert 'valence' in props
        # Check that at least some properties are not None
        assert props['atomic_radius'] is not None or props['electronegativity'] is not None

    def test_invalid_element(self):
        """Test handling of invalid element symbol"""
        props = get_element_properties("XX")
        # Should return None values or handle gracefully
        assert props is not None


class TestWeightedMean:
    """Tests for compute_weighted_mean function"""

    def test_binary_composition(self):
        """Test weighted mean for binary composition"""
        # Fe (radius ~1.26) and Ni (radius ~1.24) at 50/50
        elements = [("Fe", 0.5), ("Ni", 0.5)]
        mean_radius = compute_weighted_mean(elements, get_element_properties, 'atomic_radius')

        assert mean_radius is not None
        assert not np.isnan(mean_radius)
        # Should be between the two radii
        assert 1.0 < mean_radius < 1.5

    def test_missing_element(self):
        """Test handling of missing element properties"""
        elements = [("Fe", 0.5), ("XX", 0.5)]
        mean_radius = compute_weighted_mean(elements, get_element_properties, 'atomic_radius')

        # Should return nan or handle gracefully
        assert mean_radius is not None


class TestSizeMismatch:
    """Tests for size mismatch calculations"""

    def test_single_element(self):
        """Test size mismatch for single element (should be 0 or nan)"""
        elements = [("Fe", 1.0)]
        mismatch = compute_size_mismatch(elements)
        # Single element should have zero mismatch
        assert mismatch == 0.0 or np.isnan(mismatch)

    def test_binary_composition(self):
        """Test size mismatch for binary composition"""
        elements = [("Fe", 0.5), ("Ni", 0.5)]
        mismatch = compute_size_mismatch(elements)

        assert mismatch is not None
        assert not np.isnan(mismatch)
        assert mismatch >= 0

    def test_pairwise_mismatch_count(self):
        """Test that pairwise mismatch count matches expected pairs"""
        # Ternary should have 3 pairs
        elements = [("Fe", 0.33), ("Ni", 0.33), ("B", 0.34)]
        pairwise = compute_pairwise_size_mismatch(elements)
        assert len(pairwise) == 3

        # Binary should have 1 pair
        elements = [("Fe", 0.5), ("Ni", 0.5)]
        pairwise = compute_pairwise_size_mismatch(elements)
        assert len(pairwise) == 1

        # Single element should have 0 pairs
        elements = [("Fe", 1.0)]
        pairwise = compute_pairwise_size_mismatch(elements)
        assert len(pairwise) == 0


class TestIntegration:
    """Integration tests for feature computation"""

    def test_full_pipeline_mock(self):
        """Test that all functions can be called together without error"""
        comp_str = "Fe40.5Ni40.5B19"
        elements = parse_composition_string(comp_str)

        assert len(elements) > 0

        atomic_radius = compute_weighted_mean(elements, get_element_properties, 'atomic_radius')
        electronegativity = compute_weighted_mean(elements, get_element_properties, 'electronegativity')
        size_mismatch = compute_size_mismatch(elements)
        pairwise = compute_pairwise_size_mismatch(elements)

        assert atomic_radius is not None
        assert electronegativity is not None
        assert size_mismatch is not None
        assert pairwise is not None
        assert len(pairwise) == 3  # Ternary has 3 pairs