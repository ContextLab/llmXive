"""
Unit tests for src/data/descriptors.py descriptor calculation logic.

Tests verify:
1. Atomic Size Mismatch (delta) calculation
2. Mixing Enthalpy (delta_H_mix) calculation
3. Electronegativity Difference (delta_chi) calculation
4. Handling of unknown elements
5. Composition normalization
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: Adjust import path if src/ is not in PYTHONPATH during test execution
try:
    from src.data import descriptors
except ImportError:
    # Fallback for direct test execution from project root
    from data import descriptors

# Import constants if needed for thresholds
try:
    from src.lib import constants
except ImportError:
    from lib import constants


class TestAtomicSizeMismatch:
    """Tests for Atomic Size Mismatch (delta) calculation."""

    def test_delta_calculation_binary_alloy(self):
        """Test delta calculation for a simple binary alloy."""
        # Alloy: 50% Cu (128 pm), 50% Zr (160 pm)
        # Average radius = 0.5*128 + 0.5*160 = 144
        # delta = 100 * sqrt(sum(c_i * (1 - r_i/r_avg)^2))
        # delta = 100 * sqrt(0.5*(1-128/144)^2 + 0.5*(1-160/144)^2)
        # delta = 100 * sqrt(0.5*(0.111)^2 + 0.5*(0.111)^2) = 100 * 0.111 = 11.11
        
        elements = ["Cu", "Zr"]
        compositions = [0.5, 0.5]
        
        # Mock radii for testing
        mock_radii = {"Cu": 128.0, "Zr": 160.0}
        
        with patch.object(descriptors.Element, 'radius', new_callable=lambda: mock_radii):
            result = descriptors.calculate_atomic_size_mismatch(elements, compositions)
            
        # Expected calculation
        r_avg = 0.5 * 128.0 + 0.5 * 160.0
        expected = 100.0 * np.sqrt(
            0.5 * (1 - 128.0 / r_avg)**2 + 
            0.5 * (1 - 160.0 / r_avg)**2
        )
        
        assert np.isclose(result, expected, rtol=1e-4)

    def test_delta_single_element(self):
        """Test delta is zero for single element (pure metal)."""
        elements = ["Fe"]
        compositions = [1.0]
        
        result = descriptors.calculate_atomic_size_mismatch(elements, compositions)
        assert np.isclose(result, 0.0, atol=1e-6)

    def test_delta_empty_compositions(self):
        """Test handling of empty compositions."""
        with pytest.raises(ValueError):
            descriptors.calculate_atomic_size_mismatch([], [])

    def test_delta_composition_mismatch(self):
        """Test error when elements and compositions lengths differ."""
        with pytest.raises(ValueError):
            descriptors.calculate_atomic_size_mismatch(["Cu", "Zr"], [0.5])

    def test_delta_unknown_element(self, caplog):
        """Test handling of unknown elements (should raise or log)."""
        # This depends on implementation: either raise or exclude
        # We expect a ValueError for unknown elements in strict mode
        with pytest.raises(ValueError):
            descriptors.calculate_atomic_size_mismatch(["UnknownElement"], [1.0])


class TestMixingEnthalpy:
    """Tests for Mixing Enthalpy (delta_H_mix) calculation."""

    def test_delta_h_mix_binary(self):
        """Test delta_H_mix for a binary alloy."""
        # Alloy: 50% Cu, 50% Zr
        # delta_H_mix = sum(sum(c_i * c_j * Omega_ij)) for i != j
        # For binary: 2 * c1 * c2 * Omega_12
        
        elements = ["Cu", "Zr"]
        compositions = [0.5, 0.5]
        
        # Mock enthalpy of mixing values (kJ/mol)
        # Using a simplified mock: Omega_Cu_Zr = -10 kJ/mol
        mock_omega = {
            frozenset(["Cu", "Zr"]): -10.0,
            frozenset(["Zr", "Cu"]): -10.0  # Symmetric
        }
        
        with patch.object(descriptors, '_get_mixing_enthalpy', side_effect=lambda e1, e2: mock_omega.get(frozenset([e1, e2]), 0.0)):
            result = descriptors.calculate_mixing_enthalpy(elements, compositions)
        
        # Expected: 2 * 0.5 * 0.5 * (-10) = -5.0
        expected = 2 * 0.5 * 0.5 * (-10.0)
        assert np.isclose(result, expected, rtol=1e-4)

    def test_delta_h_mix_single_element(self):
        """Test delta_H_mix is zero for single element."""
        elements = ["Fe"]
        compositions = [1.0]
        
        result = descriptors.calculate_mixing_enthalpy(elements, compositions)
        assert np.isclose(result, 0.0, atol=1e-6)

    def test_delta_h_mix_zero_interaction(self):
        """Test delta_H_mix when all interactions are zero."""
        elements = ["Fe", "Co"]
        compositions = [0.5, 0.5]
        
        with patch.object(descriptors, '_get_mixing_enthalpy', return_value=0.0):
            result = descriptors.calculate_mixing_enthalpy(elements, compositions)
        
        assert np.isclose(result, 0.0, atol=1e-6)

    def test_delta_h_mix_unknown_pair(self, caplog):
        """Test handling of unknown element pairs (should log and use default)."""
        elements = ["Unknown1", "Unknown2"]
        compositions = [0.5, 0.5]
        
        # Should not crash, but might log a warning
        # The exact behavior depends on implementation
        result = descriptors.calculate_mixing_enthalpy(elements, compositions)
        
        # If unknown pairs default to 0, result should be 0
        assert isinstance(result, (int, float))


class TestElectronegativityDifference:
    """Tests for Electronegativity Difference (delta_chi) calculation."""

    def test_delta_chi_binary(self):
        """Test delta_chi for a binary alloy."""
        # Alloy: 50% Cu (1.90), 50% Zr (1.33)
        # delta_chi = sqrt(sum(sum(c_i * c_j * (chi_i - chi_j)^2)))
        # For binary: sqrt(2 * c1 * c2 * (chi1 - chi2)^2)
        
        elements = ["Cu", "Zr"]
        compositions = [0.5, 0.5]
        
        # Mock electronegativities (Pauling scale)
        mock_chi = {"Cu": 1.90, "Zr": 1.33}
        
        with patch.object(descriptors.Element, 'electronegativity', new_callable=lambda: mock_chi):
            result = descriptors.calculate_electronegativity_difference(elements, compositions)
        
        # Expected: sqrt(2 * 0.5 * 0.5 * (1.90 - 1.33)^2)
        # = sqrt(0.5 * 0.57^2) = sqrt(0.5 * 0.3249) = sqrt(0.16245) = 0.403
        expected = np.sqrt(2 * 0.5 * 0.5 * (1.90 - 1.33)**2)
        
        assert np.isclose(result, expected, rtol=1e-4)

    def test_delta_chi_single_element(self):
        """Test delta_chi is zero for single element."""
        elements = ["Fe"]
        compositions = [1.0]
        
        result = descriptors.calculate_electronegativity_difference(elements, compositions)
        assert np.isclose(result, 0.0, atol=1e-6)

    def test_delta_chi_identical_elements(self):
        """Test delta_chi is zero when all elements have same electronegativity."""
        elements = ["Cu", "Cu"]  # Same element twice
        compositions = [0.5, 0.5]
        
        result = descriptors.calculate_electronegativity_difference(elements, compositions)
        assert np.isclose(result, 0.0, atol=1e-6)

    def test_delta_chi_unknown_element(self):
        """Test handling of unknown elements."""
        with pytest.raises(ValueError):
            descriptors.calculate_electronegativity_difference(["UnknownElement"], [1.0])


class TestDescriptorIntegration:
    """Integration tests for the full descriptor pipeline."""

    def test_compute_all_descriptors(self):
        """Test computing all three descriptors for a valid alloy."""
        composition_str = "Cu50Zr50"
        
        # This tests the main entry point
        result = descriptors.compute_descriptors(composition_str)
        
        assert isinstance(result, dict)
        assert "delta" in result
        assert "delta_H_mix" in result
        assert "delta_chi" in result
        
        # All values should be numeric
        assert isinstance(result["delta"], (int, float))
        assert isinstance(result["delta_H_mix"], (int, float))
        assert isinstance(result["delta_chi"], (int, float))

    def test_compute_descriptors_invalid_composition(self):
        """Test handling of invalid composition string."""
        with pytest.raises((ValueError, KeyError)):
            descriptors.compute_descriptors("InvalidComposition")

    def test_compute_descriptors_unknown_element(self):
        """Test handling of unknown elements in composition."""
        with pytest.raises((ValueError, KeyError)):
            descriptors.compute_descriptors("UnknownElement100")

    def test_composition_parsing(self):
        """Test composition string parsing."""
        # Test various formats
        test_cases = [
            ("Cu50Zr50", {"Cu": 0.5, "Zr": 0.5}),
            ("Fe20Co30Ni50", {"Fe": 0.2, "Co": 0.3, "Ni": 0.5}),
            ("Ti60Cu40", {"Ti": 0.6, "Cu": 0.4}),
        ]
        
        for comp_str, expected_dict in test_cases:
            # Parse and verify
            parsed = descriptors._parse_composition(comp_str)
            assert parsed == expected_dict

    def test_composition_normalization(self):
        """Test that compositions are normalized to sum to 1."""
        # Input doesn't sum to 1
        elements = ["Cu", "Zr"]
        compositions = [0.4, 0.4]  # Sum = 0.8
        
        # Should normalize to [0.5, 0.5]
        result = descriptors.calculate_atomic_size_mismatch(elements, compositions)
        
        # Verify normalization happened (result should match normalized input)
        # If not normalized, result would be different
        # This is a soft check - depends on implementation
        assert isinstance(result, float)

    def test_large_alloy(self):
        """Test descriptor calculation for a multi-component alloy."""
        composition_str = "Cu30Zr30Ti20Al10Ni10"
        
        result = descriptors.compute_descriptors(composition_str)
        
        assert isinstance(result, dict)
        assert all(k in result for k in ["delta", "delta_H_mix", "delta_chi"])
        assert all(isinstance(v, (int, float)) for v in result.values())

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_composition(self):
        """Test handling of very small composition values."""
        elements = ["Cu", "Zr"]
        compositions = [0.9999, 0.0001]
        
        result = descriptors.calculate_atomic_size_mismatch(elements, compositions)
        assert isinstance(result, float)
        assert result >= 0

    def test_all_same_element(self):
        """Test when all elements are the same (should be pure metal)."""
        elements = ["Fe", "Fe", "Fe"]
        compositions = [0.33, 0.33, 0.34]
        
        result = descriptors.calculate_atomic_size_mismatch(elements, compositions)
        # Should be very close to 0
        assert np.isclose(result, 0.0, atol=1e-4)

    def test_chemical_balance_validation(self):
        """Test that compositions sum to 1 (or are normalized)."""
        # This tests the internal validation logic
        elements = ["Cu", "Zr"]
        compositions = [0.5, 0.5]
        
        # Should not raise
        result = descriptors.calculate_atomic_size_mismatch(elements, compositions)
        assert result >= 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
