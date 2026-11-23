"""
Unit tests for T037: Bonferroni Correction implementation.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from bonferroni_correction import apply_bonferroni_correction

def test_bonferroni_correction_calculation():
    """Test that the correction formula is applied correctly."""
    input_data = {
        "tobit_p_value": 0.03,
        "cox_p_value": 0.04
    }
    
    result = apply_bonferroni_correction(input_data)
    
    # n_tests = 2
    # p_tobit_corr = 0.03 * 2 = 0.06
    # p_cox_corr = 0.04 * 2 = 0.08
    # min_corr = 0.06
    # is_significant = 0.06 < 0.05 -> False
    
    assert result["p_tobit_corr"] == 0.06
    assert result["p_cox_corr"] == 0.08
    assert result["min_corrected_p"] == 0.06
    assert result["is_significant"] is False
    assert result["n_tests"] == 2

def test_bonferroni_significant():
    """Test case where the result is significant after correction."""
    input_data = {
        "tobit_p_value": 0.01,
        "cox_p_value": 0.02
    }
    
    result = apply_bonferroni_correction(input_data)
    
    # p_tobit_corr = 0.02
    # p_cox_corr = 0.04
    # min = 0.02 < 0.05 -> True
    
    assert result["is_significant"] is True
    assert result["min_corrected_p"] == 0.02

def test_bonferroni_cap_at_one():
    """Test that p-values are capped at 1.0."""
    input_data = {
        "tobit_p_value": 0.9,
        "cox_p_value": 0.6
    }
    
    result = apply_bonferroni_correction(input_data)
    
    # 0.9 * 2 = 1.8 -> capped at 1.0
    # 0.6 * 2 = 1.2 -> capped at 1.0
    assert result["p_tobit_corr"] == 1.0
    assert result["p_cox_corr"] == 1.0
    assert result["is_significant"] is False

def test_missing_p_values():
    """Test that missing p-values raise an error."""
    input_data = {
        "tobit_p_value": 0.05
        # cox_p_value missing
    }
    
    try:
        apply_bonferroni_correction(input_data)
        assert False, "Expected ValueError to be raised"
    except ValueError:
        pass # Expected

if __name__ == "__main__":
    test_bonferroni_correction_calculation()
    test_bonferroni_significant()
    test_bonferroni_cap_at_one()
    test_missing_p_values()
    print("All tests passed.")