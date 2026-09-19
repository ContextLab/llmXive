"""
Unit tests for unit conversion logic in preprocessing, specifically
weight% to atomic% conversion edge cases.
"""
import pytest
import math
from code.src.utils import constants
from code.src.ingestion.preprocess import weight_pct_to_atomic_pct


class TestWeightToAtomicConversion:
    """Tests for weight_pct_to_atomic_pct function."""

    def test_basic_conversion_boron(self):
        """Test conversion for Boron impurity."""
        # Boron atomic weight ~10.81, Mg ~24.305
        # 10 wt% B -> should be higher atomic % because B is lighter
        weight_pct = 10.0
        impurity = "B"
        
        result = weight_pct_to_atomic_pct(weight_pct, impurity)
        
        # Manual calculation check:
        # Assume 100g total: 10g B, 90g Mg
        # Moles B = 10 / 10.81 ≈ 0.925
        # Moles Mg = 90 / 24.305 ≈ 3.703
        # Atomic % B = 0.925 / (0.925 + 3.703) * 100 ≈ 19.99%
        
        assert result > weight_pct, "Lighter impurity should have higher atomic%"
        assert 19.0 < result < 21.0, f"Expected ~20%, got {result}"

    def test_basic_conversion_aluminum(self):
        """Test conversion for Aluminum impurity (heavier than B)."""
        # Aluminum atomic weight ~26.98
        weight_pct = 10.0
        impurity = "Al"
        
        result = weight_pct_to_atomic_pct(weight_pct, impurity)
        
        # Manual calculation:
        # 100g total: 10g Al, 90g Mg
        # Moles Al = 10 / 26.98 ≈ 0.371
        # Moles Mg = 90 / 24.305 ≈ 3.703
        # Atomic % Al = 0.371 / (0.371 + 3.703) * 100 ≈ 9.11%
        
        assert result < weight_pct, "Heavier impurity should have lower atomic%"
        assert 8.5 < result < 9.5, f"Expected ~9.1%, got {result}"

    def test_zero_weight_percent(self):
        """Edge case: 0% weight should result in 0% atomic."""
        for impurity in ["B", "Al", "C", "Si"]:
            result = weight_pct_to_atomic_pct(0.0, impurity)
            assert result == 0.0, f"0 wt% should give 0 at%, got {result}"

    def test_hundred_weight_percent(self):
        """Edge case: 100% weight should result in 100% atomic."""
        for impurity in ["B", "Al", "C", "Si"]:
            result = weight_pct_to_atomic_pct(100.0, impurity)
            assert result == 100.0, f"100 wt% should give 100 at%, got {result}"

    def test_negative_weight_percent_raises(self):
        """Edge case: negative weight percentage should raise ValueError."""
        with pytest.raises(ValueError):
            weight_pct_to_atomic_pct(-1.0, "B")

    def test_invalid_impurity_raises(self):
        """Edge case: unknown impurity should raise ValueError."""
        with pytest.raises(ValueError):
            weight_pct_to_atomic_pct(5.0, "UnknownElement")

    def test_small_values_precision(self):
        """Test precision with very small weight percentages."""
        weight_pct = 0.001
        result = weight_pct_to_atomic_pct(weight_pct, "B")
        assert result > 0, "Small positive weight should give positive atomic"
        assert result < 0.01, "Small weight should give small atomic%"

    def test_magnesium_as_impurity(self):
        """Edge case: Mg as impurity (same as matrix)."""
        # If impurity is Mg, atomic weight matches, so wt% == at%
        weight_pct = 15.0
        result = weight_pct_to_atomic_pct(weight_pct, "Mg")
        # Due to floating point, allow small tolerance
        assert math.isclose(result, weight_pct, rel_tol=1e-9), \
            f"Mg impurity should have wt% == at%, got {result}"

    def test_multiple_impurities_calculation(self):
        """Test that the function handles the formula correctly for typical values."""
        # Using Carbon (12.01)
        weight_pct = 5.0
        result = weight_pct_to_atomic_pct(weight_pct, "C")
        
        # 100g: 5g C, 95g Mg
        # Moles C = 5/12.01 ≈ 0.416
        # Moles Mg = 95/24.305 ≈ 3.909
        # At% = 0.416 / (0.416 + 3.909) * 100 ≈ 9.62%
        
        assert 9.0 < result < 10.0, f"Expected ~9.6%, got {result}"

    def test_consistency_with_atomic_weights(self):
        """Verify the conversion uses correct atomic weights from constants."""
        # For an impurity with atomic weight equal to Mg (24.305), 
        # wt% should equal at%
        mg_weight = constants.get_atomic_weight("Mg")
        
        # Create a test with a hypothetical element matching Mg weight
        # Since we can't easily mock constants, we verify the logic
        # by checking that the ratio of atomic weights drives the conversion
        
        # Lighter element (B) -> at% > wt%
        b_result = weight_pct_to_atomic_pct(10.0, "B")
        assert b_result > 10.0
        
        # Heavier element (Al) -> at% < wt%
        al_result = weight_pct_to_atomic_pct(10.0, "Al")
        assert al_result < 10.0

    def test_boundary_conditions(self):
        """Test boundary conditions near 0 and 100."""
        test_cases = [
            (0.0001, "B", True),   # Very small positive
            (99.9999, "B", True),  # Very close to 100
            (50.0, "B", True),     # Midpoint
        ]
        
        for wt, imp, should_succeed in test_cases:
            if should_succeed:
                result = weight_pct_to_atomic_pct(wt, imp)
                assert 0 <= result <= 100, f"Result {result} out of bounds for {wt} wt%"
            else:
                with pytest.raises(ValueError):
                    weight_pct_to_atomic_pct(wt, imp)