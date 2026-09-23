import os
import json
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

RESULTS_DIR = Path("data/results")
STATISTICAL_REPORT_PATH = RESULTS_DIR / "statistical_report.json"

def test_statistical_report_schema_exists():
    """Test that the statistical report file exists after analysis."""
    # This test checks if the file exists. If analysis hasn't run, it might not.
    # In a CI/CD pipeline, this would run after the analysis step.
    if not STATISTICAL_REPORT_PATH.exists():
        pytest.skip("Statistical report not generated yet. Run analysis first.")
    
    with open(STATISTICAL_REPORT_PATH, 'r') as f:
        report = json.load(f)
    
    # Check for expected top-level keys
    expected_keys = ['p_values', 'corrected_p_values', 'effect_sizes', 'power', 'MDES']
    for key in expected_keys:
        assert key in report, f"Missing key '{key}' in statistical report"

def test_statistical_report_contains_welch_results():
    """Test that the report contains Welch's t-test results."""
    if not STATISTICAL_REPORT_PATH.exists():
        pytest.skip("Statistical report not generated yet.")
    
    with open(STATISTICAL_REPORT_PATH, 'r') as f:
        report = json.load(f)
    
    # Check that p-values are present for both metrics
    p_values = report.get('p_values', {})
    assert 'perseverative_errors' in p_values, "Missing p-value for perseverative_errors"
    assert 'categories_completed' in p_values, "Missing p-value for categories_completed"
    
    # Ensure p-values are numbers
    for metric, p_val in p_values.items():
        assert isinstance(p_val, (int, float)), f"p-value for {metric} is not a number"
        assert 0 <= p_val <= 1, f"p-value for {metric} is out of range [0, 1]"

def test_effect_size_structure():
    """Test that effect sizes are reported with confidence intervals."""
    if not STATISTICAL_REPORT_PATH.exists():
        pytest.skip("Statistical report not generated yet.")
    
    with open(STATISTICAL_REPORT_PATH, 'r') as f:
        report = json.load(f)
    
    effect_sizes = report.get('effect_sizes', {})
    # Check structure for at least one metric
    if 'perseverative_errors' in effect_sizes:
        es = effect_sizes['perseverative_errors']
        assert 'cohen_d' in es, "Missing Cohen's d in effect sizes"
        assert 'ci_95_lower' in es, "Missing 95% CI lower bound"
        assert 'ci_95_upper' in es, "Missing 95% CI upper bound"

def test_power_analysis_present():
    """Test that power and MDES are included in the report."""
    if not STATISTICAL_REPORT_PATH.exists():
        pytest.skip("Statistical report not generated yet.")
    
    with open(STATISTICAL_REPORT_PATH, 'r') as f:
        report = json.load(f)
    
    assert 'power' in report, "Missing 'power' in report"
    assert 'MDES' in report, "Missing 'MDES' in report"
    
    # Validate types
    assert isinstance(report['power'], (int, float)), "Power should be a number"
    assert isinstance(report['MDES'], (int, float)), "MDES should be a number"
