"""
Unit tests for unit conversion logic in preprocessing.
Specifically tests weight% to atomic% conversion edge cases.
"""
import pytest
import math
from code.src.utils import constants

# Helper function to perform the conversion (mirroring logic expected in preprocessing)
def weight_pct_to_atomic_pct(weight_pct_list, element_symbols):
    """
    Convert a list of weight percentages to atomic percentages.
    
    Args:
        weight_pct_list: List of weight percentages for impurities
        element_symbols: List of corresponding element symbols (e.g., ['C', 'Al'])
    
    Returns:
        List of atomic percentages
    """
    if not weight_pct_list or not element_symbols:
        return []
    
    if len(weight_pct_list) != len(element_symbols):
        raise ValueError("Weight percentage list and element symbols list must be the same length")
    
    # Calculate moles for each impurity
    moles = []
    for wt, symbol in zip(weight_pct_list, element_symbols):
        atomic_weight = constants.get_atomic_weight(symbol)
        if atomic_weight is None:
            raise ValueError(f"Unknown element symbol: {symbol}")
        moles.append(wt / atomic_weight)
    
    # Calculate total moles of impurities
    total_moles = sum(moles)
    
    if total_moles == 0:
        return [0.0] * len(weight_pct_list)
    
    # Calculate atomic percentages
    atomic_pct = [(m / total_moles) * 100.0 for m in moles]
    
    return atomic_pct


class TestWeightToAtomicConversion:
    """Test suite for weight% to atomic% conversion logic."""

    def test_basic_conversion_single_element(self):
        """Test conversion with a single impurity (should be 100% atomic if only one)."""
        weights = [10.0]
        symbols = ['C']
        result = weight_pct_to_atomic_pct(weights, symbols)
        assert len(result) == 1
        assert math.isclose(result[0], 100.0, rel_tol=1e-5)

    def test_basic_conversion_two_elements(self):
        """Test conversion with two impurities with known weights."""
        # Example: 50% C (12.01 g/mol) and 50% Al (26.98 g/mol)
        # Moles C = 50/12.01 = 4.163
        # Moles Al = 50/26.98 = 1.853
        # Total Moles = 6.016
        # At% C = 4.163/6.016 = 69.2%
        # At% Al = 1.853/6.016 = 30.8%
        weights = [50.0, 50.0]
        symbols = ['C', 'Al']
        result = weight_pct_to_atomic_pct(weights, symbols)
        
        expected_c = (50.0 / 12.011) / ((50.0 / 12.011) + (50.0 / 26.982)) * 100
        expected_al = (50.0 / 26.982) / ((50.0 / 12.011) + (50.0 / 26.982)) * 100
        
        assert len(result) == 2
        assert math.isclose(result[0], expected_c, rel_tol=1e-3)
        assert math.isclose(result[1], expected_al, rel_tol=1e-3)
        assert math.isclose(result[0] + result[1], 100.0, rel_tol=1e-5)

    def test_edge_case_empty_lists(self):
        """Test conversion with empty lists."""
        result = weight_pct_to_atomic_pct([], [])
        assert result == []

    def test_edge_case_single_element_zero_weight(self):
        """Test conversion where weight is zero."""
        weights = [0.0]
        symbols = ['C']
        result = weight_pct_to_atomic_pct(weights, symbols)
        # 0 weight means 0 moles, total moles = 0 -> handled by division check
        # In our logic: total_moles is 0, so we return 0.0
        assert math.isclose(result[0], 0.0, rel_tol=1e-5)

    def test_edge_case_multiple_zeros(self):
        """Test conversion where all weights are zero."""
        weights = [0.0, 0.0]
        symbols = ['C', 'Al']
        result = weight_pct_to_atomic_pct(weights, symbols)
        # Total moles is 0, should return zeros
        assert len(result) == 2
        assert all(math.isclose(x, 0.0, rel_tol=1e-5) for x in result)

    def test_invalid_element_symbol(self):
        """Test conversion with an unknown element symbol."""
        weights = [10.0]
        symbols = ['X']  # Unknown element
        with pytest.raises(ValueError, match="Unknown element symbol"):
            weight_pct_to_atomic_pct(weights, symbols)

    def test_mismatched_list_lengths(self):
        """Test conversion with mismatched list lengths."""
        weights = [10.0, 20.0]
        symbols = ['C']
        with pytest.raises(ValueError, match="same length"):
            weight_pct_to_atomic_pct(weights, symbols)

    def test_very_small_weights(self):
        """Test conversion with very small weight percentages (precision edge case)."""
        weights = [1e-6, 1e-6]
        symbols = ['C', 'Al']
        result = weight_pct_to_atomic_pct(weights, symbols)
        # Should still sum to 100%
        assert math.isclose(sum(result), 100.0, rel_tol=1e-3)

    def test_very_large_weights(self):
        """Test conversion with large weight percentages."""
        weights = [99.9, 0.1]
        symbols = ['C', 'Al']
        result = weight_pct_to_atomic_pct(weights, symbols)
        # C is lighter, so its atomic % should be higher than 99.9
        # Moles C = 99.9/12.01 ~ 8.31
        # Moles Al = 0.1/26.98 ~ 0.0037
        # Total ~ 8.3137
        # At% C ~ 99.95%
        assert result[0] > 99.9
        assert result[1] < 0.1

    def test_consistency_with_constants_module(self):
        """Verify the conversion uses the correct atomic weights from constants module."""
        # Use Carbon and Magnesium
        # C: ~12.011, Mg: ~24.305
        # If we have 50% C and 50% Mg
        weights = [50.0, 50.0]
        symbols = ['C', 'Mg']
        result = weight_pct_to_atomic_pct(weights, symbols)
        
        atomic_wt_c = constants.get_atomic_weight('C')
        atomic_wt_mg = constants.get_atomic_weight('Mg')
        
        expected_c = (50.0 / atomic_wt_c) / ((50.0 / atomic_wt_c) + (50.0 / atomic_wt_mg)) * 100
        
        assert math.isclose(result[0], expected_c, rel_tol=1e-5)
    
    def test_real_world_scenario_mgb2_impurities(self):
        """Test a realistic scenario with MgB2 impurities (C and Al)."""
        # Typical doping levels: 1 wt% C, 2 wt% Al
        weights = [1.0, 2.0]
        symbols = ['C', 'Al']
        result = weight_pct_to_atomic_pct(weights, symbols)
        
        # Verify sum is 100
        assert math.isclose(sum(result), 100.0, rel_tol=1e-5)
        
        # C is lighter (12.01) than Al (26.98), so 1% C should have more moles 
        # than 2% Al?
        # Moles C = 1/12.01 = 0.083
        # Moles Al = 2/26.98 = 0.074
        # So C should have slightly higher atomic % despite lower weight %
        assert result[0] > result[1]