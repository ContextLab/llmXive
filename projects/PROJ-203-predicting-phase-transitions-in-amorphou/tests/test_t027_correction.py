"""
Tests for T027: Multiple-Comparison Correction
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
from scipy import stats

from models.corrected_p_values import apply_bonferroni_correction

def test_bonferroni_single_value():
    """Test Bonferroni correction on a single p-value."""
    raw_p = {"feature_A": 0.01}
    corrected = apply_bonferroni_correction(raw_p, alpha=0.05)
    
    assert "feature_A" in corrected
    # n=1, so p_corr = 0.01 * 1 = 0.01
    assert abs(corrected["feature_A"]["p_value_corrected"] - 0.01) < 1e-6
    assert corrected["feature_A"]["significant"] == True
    assert corrected["feature_A"]["alpha_threshold"] == 0.05

def test_bonferroni_multiple_values():
    """Test Bonferroni correction with multiple features."""
    raw_p = {
        "feature_A": 0.01,
        "feature_B": 0.03,
        "feature_C": 0.06
    }
    corrected = apply_bonferroni_correction(raw_p, alpha=0.05)
    
    n = 3
    # feature_A: 0.01 * 3 = 0.03 (< 0.05) -> Significant
    # feature_B: 0.03 * 3 = 0.09 (> 0.05) -> Not Significant
    # feature_C: 0.06 * 3 = 0.18 (> 0.05) -> Not Significant
    
    assert corrected["feature_A"]["significant"] == True
    assert corrected["feature_B"]["significant"] == False
    assert corrected["feature_C"]["significant"] == False
    
    assert abs(corrected["feature_A"]["p_value_corrected"] - 0.03) < 1e-6
    assert abs(corrected["feature_B"]["p_value_corrected"] - 0.09) < 1e-6

def test_bonferroni_cap_at_1():
    """Test that corrected p-values do not exceed 1.0."""
    raw_p = {"feature_X": 0.9}
    corrected = apply_bonferroni_correction(raw_p, alpha=0.05)
    
    # 0.9 * 1 = 0.9 (if n=1) -> OK
    # If n=2, 0.9 * 2 = 1.8 -> capped at 1.0
    raw_p_2 = {"feature_X": 0.9, "feature_Y": 0.5}
    corrected_2 = apply_bonferroni_correction(raw_p_2, alpha=0.05)
    
    assert corrected_2["feature_X"]["p_value_corrected"] == 1.0

def test_bonferroni_empty_input():
    """Test handling of empty input."""
    corrected = apply_bonferroni_correction({}, alpha=0.05)
    assert corrected == {}