import json
import math
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import the module under test
# Assuming the tests are run from the project root or code/ directory
# Adjust import path if necessary
sys_path = str(Path(__file__).parent.parent / "code")
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

from analysis.bias import (
    load_study_count_from_json,
    load_effect_sizes_and_se,
    run_eggerr_regression,
    run_bias_assessment
)

def test_load_study_count_from_json_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"N": 15}, f)
        f.flush()
        path = Path(f.name)
    
    try:
        count = load_study_count_from_json(path)
        assert count == 15
    finally:
        os.unlink(path)

def test_load_study_count_from_json_missing_file():
    count = load_study_count_from_json(Path("/nonexistent/path.json"))
    assert count == 0

def test_load_study_count_from_json_invalid_json():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("not valid json")
        f.flush()
        path = Path(f.name)
    
    try:
        count = load_study_count_from_json(path)
        assert count == 0
    finally:
        os.unlink(path)

def test_load_effect_sizes_and_se_valid():
    data = [
        {"r": 0.5, "n": 30},
        {"r": 0.3, "n": 50},
        {"r": -0.2, "n": 20}
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        path = Path(f.name)
    
    try:
        effects, ses = load_effect_sizes_and_se(path)
        assert len(effects) == 3
        assert len(ses) == 3
        
        # Verify Fisher's Z calculation for first item: r=0.5
        # z = 0.5 * ln((1+0.5)/(1-0.5)) = 0.5 * ln(3)
        expected_z = 0.5 * math.log(3)
        assert math.isclose(effects[0], expected_z, rel_tol=1e-4)
        
        # Verify SE calculation: 1/sqrt(n-3)
        expected_se = 1 / math.sqrt(27)
        assert math.isclose(ses[0], expected_se, rel_tol=1e-4)
    finally:
        os.unlink(path)

def test_load_effect_sizes_and_se_invalid_n():
    data = [
        {"r": 0.5, "n": 2},  # Invalid: n must be > 3 for SE calc (n-3 > 0)
        {"r": 0.5, "n": 10}  # Valid
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        f.flush()
        path = Path(f.name)
    
    try:
        effects, ses = load_effect_sizes_and_se(path)
        assert len(effects) == 1
        assert len(ses) == 1
    finally:
        os.unlink(path)

def test_run_eggerr_regression_skip_insufficient_data():
    result = run_eggerr_regression([0.1], [0.5])
    assert "egger_skipped_reason" in result
    assert "Insufficient data points" in result["egger_skipped_reason"]

def test_run_eggerr_regression_skip_zero_variance():
    # All SEs are the same -> zero variance in x
    effects = [0.1, 0.2, 0.3]
    ses = [0.5, 0.5, 0.5]
    result = run_eggerr_regression(effects, ses)
    assert "egger_skipped_reason" in result
    assert "Variance in standard errors" in result["egger_skipped_reason"]

def test_run_eggerr_regression_success():
    # Generate some data that should produce a regression
    # Using known values to verify logic
    effects = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    ses = [0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19]
    
    result = run_eggerr_regression(effects, ses)
    
    assert "egger_intercept" in result
    assert "egger_p_value" in result
    assert "egger_result" in result
    assert result["n_studies"] == 10
    assert "egger_skipped_reason" not in result

def test_run_bias_assessment_skip_n_less_than_10():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create input file (dummy)
        input_file = tmpdir / "input.json"
        input_file.write_text("[]")
        
        # Create results file with N=5
        results_file = tmpdir / "results.json"
        results_file.write_text(json.dumps({"N": 5}))
        
        output_file = tmpdir / "output.json"
        
        result = run_bias_assessment(input_file, output_file, results_file)
        
        assert "egger_skipped_reason" in result
        assert result["egger_skipped_reason"] == "Skipped: Insufficient studies (N < 10) for Egger's regression"
        
        # Verify file was written
        assert output_file.exists()
        with open(output_file) as f:
            saved_data = json.load(f)
        assert saved_data["egger_skipped_reason"] == result["egger_skipped_reason"]

def test_run_bias_assessment_run_regression():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create input file with valid data
        input_data = [
            {"r": 0.1, "n": 50},
            {"r": 0.2, "n": 50},
            {"r": 0.3, "n": 50},
            {"r": 0.4, "n": 50},
            {"r": 0.5, "n": 50},
            {"r": 0.6, "n": 50},
            {"r": 0.7, "n": 50},
            {"r": 0.8, "n": 50},
            {"r": 0.9, "n": 50},
            {"r": 1.0, "n": 50}
        ]
        input_file = tmpdir / "input.json"
        input_file.write_text(json.dumps(input_data))
        
        # Create results file with N=15
        results_file = tmpdir / "results.json"
        results_file.write_text(json.dumps({"N": 15}))
        
        output_file = tmpdir / "output.json"
        
        result = run_bias_assessment(input_file, output_file, results_file)
        
        assert "egger_skipped_reason" not in result
        assert "egger_intercept" in result
        assert result["n_studies"] == 15
        
        # Verify file content
        assert output_file.exists()
        with open(output_file) as f:
            saved_data = json.load(f)
        assert saved_data["egger_intercept"] == result["egger_intercept"]