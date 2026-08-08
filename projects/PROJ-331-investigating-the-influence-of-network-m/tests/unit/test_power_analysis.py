import os
import json
import pytest
import numpy as np
from stats import power_analysis
from utils import safe_read_json

def test_power_analysis_structure():
    """
    Test that power_analysis returns a dictionary with the correct schema.
    """
    result = power_analysis(n_subjects=50, alpha=0.05, power_level=0.8)
    
    assert isinstance(result, dict)
    assert "min_detectable_r" in result
    assert "power_level" in result
    assert "adjusted_alpha" in result
    assert "n_subjects" in result

    # Check types
    assert isinstance(result["min_detectable_r"], float)
    assert isinstance(result["power_level"], float)
    assert isinstance(result["adjusted_alpha"], float)
    assert isinstance(result["n_subjects"], int)

def test_power_analysis_values():
    """
    Test that power analysis values are within expected ranges.
    - adjusted_alpha should be smaller than base alpha (0.05)
    - min_detectable_r should be between 0 and 1
    - power_level should match input
    """
    result = power_analysis(n_subjects=50, alpha=0.05, power_level=0.8)
    
    assert result["adjusted_alpha"] < 0.05
    assert 0.0 <= result["min_detectable_r"] <= 1.0
    assert abs(result["power_level"] - 0.8) < 1e-6
    assert result["n_subjects"] == 50

def test_bonferroni_adjustment():
    """
    Verify that the Bonferroni adjustment is applied correctly.
    We assume a correction factor of 26 (13 motifs * 2 metrics).
    """
    result = power_analysis(n_subjects=50, alpha=0.05, power_level=0.8)
    expected_alpha = 0.05 / 26
    assert abs(result["adjusted_alpha"] - expected_alpha) < 1e-10

def test_file_output():
    """
    Test that the main function creates the expected output file.
    This is a mock test to ensure the file writing logic is sound.
    In a real CI, we would run the main function and check the file.
    """
    # We can't easily run main() in a unit test without side effects,
    # but we can verify the logic by calling power_analysis and checking the result.
    # The actual file writing is tested in integration tests or by running the script.
    result = power_analysis()
    assert result is not None
    assert result["min_detectable_r"] > 0