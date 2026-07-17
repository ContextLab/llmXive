"""
Unit tests for validation logic in code/validation.py.
"""
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# We need to mock the imports from config and utils if they are heavy, 
# but for unit testing the logic we can mock the file loading.
# Since we are writing a test file, we assume the environment is set up.
# We will test the logic functions directly by mocking file I/O.

def test_validate_retention_rate_pass():
    from validation import validate_retention_rate
    report = {"retention_rate": 0.96}
    result = validate_retention_rate(report)
    assert result["status"] == "PASS"
    assert "0.9600" in result["details"]

def test_validate_retention_rate_fail():
    from validation import validate_retention_rate
    report = {"retention_rate": 0.94}
    result = validate_retention_rate(report)
    assert result["status"] == "FAIL"
    assert "0.9400" in result["details"]

def test_validate_retention_rate_missing():
    from validation import validate_retention_rate
    report = {}
    result = validate_retention_rate(report)
    assert result["status"] == "FAIL"
    assert "missing" in result["details"]

def test_validate_model_count_pass():
    from validation import validate_model_count
    report = {"models": [{"converged": True}, {"converged": True}, {"converged": True}]}
    result = validate_model_count(report)
    assert result["status"] == "PASS"
    assert "3 models" in result["details"]

def test_validate_model_count_fail():
    from validation import validate_model_count
    report = {"models": [{"converged": True}, {"converged": False}]}
    result = validate_model_count(report)
    assert result["status"] == "FAIL"
    assert "1 models" in result["details"]

def test_validate_hill_index_pass():
    from validation import validate_hill_index
    report = {"tail_index": 0.8}
    result = validate_hill_index(report)
    assert result["status"] == "PASS"

def test_validate_hill_index_fail_bounds():
    from validation import validate_hill_index
    report = {"tail_index": 5.0}
    result = validate_hill_index(report)
    assert result["status"] == "FAIL"

def test_validate_runtime_pass():
    from validation import validate_runtime
    import time
    start = time.time() - 100
    result = validate_runtime(start)
    assert result["status"] == "PASS"

def test_validate_runtime_fail():
    from validation import validate_runtime
    import time
    start = time.time() - 4000
    result = validate_runtime(start)
    assert result["status"] == "FAIL"

def test_validate_vuong_test_pass():
    from validation import validate_vuong_test
    report = {"p_value": 0.03}
    result = validate_vuong_test(report)
    assert result["status"] == "PASS"

def test_validate_vuong_test_missing():
    from validation import validate_vuong_test
    result = validate_vuong_test(None)
    assert result["status"] == "FAIL"

def test_validate_tail_ks_pass():
    from validation import validate_tail_ks
    report = {"p_value": 0.15}
    result = validate_tail_ks(report)
    assert result["status"] == "PASS"

def test_validate_stability_window_pass():
    from validation import validate_stability_window
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        f.write(b"col1,col2\n1,2\n")
        temp_path = Path(f.name)
    
    try:
        result = validate_stability_window(temp_path)
        assert result["status"] == "PASS"
    finally:
        os.unlink(temp_path)

def test_validate_stability_window_fail():
    from validation import validate_stability_window
    result = validate_stability_window(Path("nonexistent.csv"))
    assert result["status"] == "FAIL"

def test_validate_pvalues_pass():
    from validation import validate_pvalues
    bg = {"p_value": 0.2}
    ln = {"p_value": 0.3}
    result = validate_pvalues(bg, ln)
    assert result["status"] == "PASS"

def test_validate_pvalues_fail_missing():
    from validation import validate_pvalues
    result = validate_pvalues(None, {"p_value": 0.3})
    assert result["status"] == "FAIL"
    assert "bootstrap_gof" in result["details"]