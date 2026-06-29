"""
Unit tests for descriptor computation in code/descriptors/compute.py
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from descriptors.compute import (
    compute_atomic_size_mismatch,
    compute_mixing_enthalpy,
    compute_electronegativity_variance,
    parse_composition
)


class TestParseComposition:
    """Tests for composition string parsing."""

    def test_simple_binary_composition(self):
        """Test parsing Cu40Zr60."""
        result = parse_composition('Cu40Zr60')
        assert abs(result['Cu'] - 0.4) < 0.001
        assert abs(result['Zr'] - 0.6) < 0.001

    def test_decimal_composition(self):
        """Test parsing with decimal values."""
        result = parse_composition('Cu40.5Zr59.5')
        assert abs(result['Cu'] - 0.405) < 0.001
        assert abs(result['Zr'] - 0.595) < 0.001

    def test_three_element_composition(self):
        """Test parsing multi-element composition."""
        result = parse_composition('Cu33Zr33Ti34')
        assert abs(result['Cu'] - 0.33) < 0.001
        assert abs(result['Zr'] - 0.33) < 0.001
        assert abs(result['Ti'] - 0.34) < 0.001


class TestAtomicSizeMismatch:
    """Tests for atomic size mismatch calculation."""

    def test_single_element(self):
        """Single element should have zero mismatch."""
        composition = {'Cu': 1.0}
        result = compute_atomic_size_mismatch(composition)
        assert abs(result) < 0.0001

    def test_binary_system(self):
        """Test Cu-Zr binary system."""
        # Cu radius ~128 pm, Zr radius ~160 pm
        composition = {'Cu': 0.5, 'Zr': 0.5}
        result = compute_atomic_size_mismatch(composition)
        # Should be non-zero due to different radii
        assert result > 0
        assert result < 0.2  # Reasonable upper bound

    def test_empty_composition(self):
        """Empty composition should return NaN."""
        composition = {}
        result = compute_atomic_size_mismatch(composition)
        assert np.isnan(result)


class TestMixingEnthalpy:
    """Tests for mixing enthalpy calculation."""

    def test_single_element(self):
        """Single element should have zero mixing enthalpy."""
        composition = {'Cu': 1.0}
        result = compute_mixing_enthalpy(composition)
        assert abs(result) < 0.001

    def test_binary_system(self):
        """Test Cu-Zr binary system."""
        composition = {'Cu': 0.5, 'Zr': 0.5}
        result = compute_mixing_enthalpy(composition)
        # Should be non-zero for Cu-Zr (negative for glass-forming)
        assert result != 0


class TestElectronegativityVariance:
    """Tests for electronegativity variance calculation."""

    def test_single_element(self):
        """Single element should have zero variance."""
        composition = {'Cu': 1.0}
        result = compute_electronegativity_variance(composition)
        assert abs(result) < 0.0001

    def test_binary_system(self):
        """Test Cu-Zr binary system."""
        # Cu EN ~1.9, Zr EN ~1.33
        composition = {'Cu': 0.5, 'Zr': 0.5}
        result = compute_electronegativity_variance(composition)
        # Should be non-zero due to different electronegativities
        assert result > 0

    def test_empty_composition(self):
        """Empty composition should return NaN."""
        composition = {}
        result = compute_electronegativity_variance(composition)
        assert np.isnan(result)


class TestDescriptorIntegration:
    """Integration tests for full descriptor computation."""

    def test_all_descriptors_for_benchmark(self):
        """Test all three descriptors for Cu-Zr benchmark."""
        composition = {'Cu': 0.64, 'Zr': 0.36}

        delta = compute_atomic_size_mismatch(composition)
        delta_h = compute_mixing_enthalpy(composition)
        chi_var = compute_electronegativity_variance(composition)

        # All should be computed without error
        assert not np.isnan(delta)
        assert not np.isnan(delta_h)
        assert not np.isnan(chi_var)

        # Reasonable ranges
        assert 0 <= delta < 0.2
        assert -100 < delta_h < 100
        assert 0 <= chi_var < 1.0
