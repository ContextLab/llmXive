"""Unit tests for composition standardization (wt% to at%) in code/data/clean.py."""

import pytest
import numpy as np
from code.data.clean import standardize_composition_to_atm_percent

# Mock data structure expected by the function
# A list of dictionaries, each representing a composition with 'elements' and 'wt_percent'
MOCK_COMPOSITIONS = [
    {
        "elements": ["Zr", "Ti", "Cu", "Ni", "Be"],
        "wt_percent": [41.0, 13.0, 13.0, 10.0, 23.0]
    },
    {
        "elements": ["Pd", "Cu", "Si"],
        "wt_percent": [77.5, 15.6, 6.9]
    }
]

# Reference atomic weights (approximate from periodic table)
REF_ATOMIC_WEIGHTS = {
    "Zr": 91.224,
    "Ti": 47.867,
    "Cu": 63.546,
    "Ni": 58.693,
    "Be": 9.012,
    "Pd": 106.42,
    "Si": 28.085
}


def test_standardize_composition_to_atm_percent_structure():
    """Test that the output structure is correct."""
    result = standardize_composition_to_atm_percent(MOCK_COMPOSITIONS)
    
    assert isinstance(result, list), "Output should be a list"
    assert len(result) == len(MOCK_COMPOSITIONS), "Output length should match input"
    
    for item in result:
        assert "elements" in item, "Output item must contain 'elements'"
        assert "atm_percent" in item, "Output item must contain 'atm_percent'"
        assert isinstance(item["elements"], list), "'elements' must be a list"
        assert isinstance(item["atm_percent"], list), "'atm_percent' must be a list"


def test_standardize_composition_sum_to_one():
    """Test that the resulting atomic percentages sum to approximately 1.0."""
    result = standardize_composition_to_atm_percent(MOCK_COMPOSITIONS)
    
    for item in result:
        total = sum(item["atm_percent"])
        # Allow small floating point error
        assert np.isclose(total, 1.0, atol=1e-6), f"Atomic percentages should sum to 1.0, got {total}"


def test_standardize_composition_values_positive():
    """Test that all atomic percentages are positive."""
    result = standardize_composition_to_atm_percent(MOCK_COMPOSITIONS)
    
    for item in result:
        for val in item["atm_percent"]:
            assert val > 0, "Atomic percentages must be positive"


def test_standardize_composition_specific_case():
    """Test a specific known case manually calculated."""
    # Input: Zr41Ti13Cu13Ni10Be23 (wt%)
    # Moles (approx): 
    # Zr: 41/91.224 = 0.4494
    # Ti: 13/47.867 = 0.2716
    # Cu: 13/63.546 = 0.2046
    # Ni: 10/58.693 = 0.1704
    # Be: 23/9.012 = 2.5521
    # Total moles = 3.6481
    # Zr at% = 0.4494 / 3.6481 = 0.1232
    
    input_data = [
        {
            "elements": ["Zr", "Ti", "Cu", "Ni", "Be"],
            "wt_percent": [41.0, 13.0, 13.0, 10.0, 23.0]
        }
    ]
    
    result = standardize_composition_to_atm_percent(input_data)
    zr_idx = result[0]["elements"].index("Zr")
    zr_atm = result[0]["atm_percent"][zr_idx]
    
    # Allow for slight variations in atomic weight sources
    assert 0.12 < zr_atm < 0.13, f"Expected Zr at% around 0.123, got {zr_atm}"


def test_standardize_composition_empty_input():
    """Test handling of empty input list."""
    result = standardize_composition_to_atm_percent([])
    assert result == [], "Empty input should return empty list"


def test_standardize_composition_single_element():
    """Test a single element composition."""
    input_data = [
        {
            "elements": ["Cu"],
            "wt_percent": [100.0]
        }
    ]
    result = standardize_composition_to_atm_percent(input_data)
    assert len(result[0]["atm_percent"]) == 1
    assert np.isclose(result[0]["atm_percent"][0], 1.0)