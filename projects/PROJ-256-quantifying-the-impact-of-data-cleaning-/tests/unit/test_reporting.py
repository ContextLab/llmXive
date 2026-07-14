import pytest
import numpy as np
from reporting import (
    calculate_p_value_shift,
    compute_ci_width_change,
    compute_effect_size_delta,
    calculate_inconsistency_rate,
    apply_bonferroni_correction,
    process_single_comparison,
    generate_comparison_report,
    load_json_file,
    save_json_file
)
import json
import os
import tempfile

def test_calculate_p_value_shift():
    """Test absolute difference calculation with >= 3 decimal precision."""
    result = calculate_p_value_shift(0.05, 0.02)
    assert result == 0.03
    
    result = calculate_p_value_shift(0.12345, 0.12346)
    assert result == 0.0001

def test_compute_ci_width_change():
    """Test CI width change calculation with >= 2 decimal precision."""
    baseline = (0.1, 0.5) # width 0.4
    cleaned = (0.2, 0.7) # width 0.5
    result = compute_ci_width_change(baseline, cleaned)
    assert result == 0.1
    
    result = compute_ci_width_change((0, 0), (0.1, 0.2))
    assert result == 0.1

def test_compute_effect_size_delta():
    """Test effect size delta calculation."""
    result = compute_effect_size_delta(0.5, 0.8)
    assert result == 0.3

def test_calculate_inconsistency_rate():
    """Test inconsistency rate calculation (FR-006)."""
    baseline = [
        {"dataset_name": "ds1", "analysis": {"t_test": {"p_value": 0.04}}},
        {"dataset_name": "ds2", "analysis": {"t_test": {"p_value": 0.10}}}
    ]
    cleaned = [
        {"dataset_name": "ds1", "analysis": {"t_test": {"p_value": 0.06}}}, # Changed: sig -> not sig
        {"dataset_name": "ds2", "analysis": {"t_test": {"p_value": 0.12}}}  # No change
    ]
    
    rate = calculate_inconsistency_rate(baseline, cleaned)
    assert rate == 0.5 # 1 out of 2 changed

def test_apply_bonferroni_correction():
    """Test Bonferroni correction."""
    p_values = [0.01, 0.04, 0.06]
    corrected = apply_bonferroni_correction(p_values, alpha=0.05)
    # n=3, so multiply by 3
    assert corrected[0] == 0.03
    assert corrected[1] == 0.12
    assert corrected[2] == 0.18

def test_process_single_comparison():
    """Test single comparison processing."""
    baseline = {"dataset_name": "test_ds", "analysis": {"t_test": {"p_value": 0.05, "ci": [0.1, 0.5], "effect_size": 0.5}}}
    cleaned = {"dataset_name": "test_ds", "analysis": {"t_test": {"p_value": 0.02, "ci": [0.2, 0.6], "effect_size": 0.6}}}
    
    result = process_single_comparison(baseline, cleaned)
    assert result["dataset_name"] == "test_ds"
    assert result["p_value_shift"] == 0.03
    assert result["baseline_sig"] == True
    assert result["cleaned_sig"] == True

def test_generate_comparison_report():
    """Test full report generation."""
    baseline = {
        "datasets": [
            {"dataset_name": "ds1", "analysis": {"t_test": {"p_value": 0.04, "ci": [0.1, 0.5], "effect_size": 0.5}}}
        ]
    }
    cleaned = {
        "datasets": [
            {"dataset_name": "ds1", "analysis": {"t_test": {"p_value": 0.02, "ci": [0.2, 0.6], "effect_size": 0.6}}}
        ]
    }
    
    report = generate_comparison_report(baseline, cleaned)
    assert "comparisons" in report
    assert "aggregate" in report
    assert report["aggregate"]["inconsistency_rate"] == 0.0

def test_save_and_load_json_file(tmp_path):
    """Test JSON save and load."""
    test_file = tmp_path / "test.json"
    data = {"key": "value", "num": 123}
    
    assert save_json_file(data, str(test_file))
    loaded = load_json_file(str(test_file))
    assert loaded == data