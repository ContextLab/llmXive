"""
Unit tests for Task T019: Bonferroni Correction
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Import the functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from task_t019_bonferroni_correction import (
    load_statistical_results,
    apply_bonferroni_correction,
    save_bonferroni_results,
    main
)

@pytest.fixture
def mock_statistical_report(tmp_path):
    """Creates a mock statistical report file for testing."""
    report_data = {
        "perseverative_errors": {
            "t_statistic": 2.5,
            "p_value": 0.012,
            "df": 98
        },
        "categories_completed": {
            "t_statistic": -1.8,
            "p_value": 0.075,
            "df": 98
        },
        "other_info": "test_data"
    }
    
    report_file = tmp_path / "statistical_report.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f)
    
    return str(report_file), report_data

def test_apply_bonferroni_correction(mock_statistical_report):
    """
    Test that Bonferroni correction is applied correctly.
    
    Given:
    - p1 = 0.012
    - p2 = 0.075
    - n = 2 tests
    
    Expected:
    - p1_corrected = 0.012 * 2 = 0.024
    - p2_corrected = 0.075 * 2 = 0.150 (capped at 1.0 if > 1)
    """
    _, report_data = mock_statistical_report
    
    corrected = apply_bonferroni_correction(report_data)
    
    # Check that status is success
    assert corrected['bonferroni_status'] == 'success'
    
    # Check specific metrics
    assert 'bonferroni_metrics' in corrected
    assert len(corrected['bonferroni_metrics']) == 2
    
    # Find the entries
    pe_entry = next(m for m in corrected['bonferroni_metrics'] if m['metric'] == 'perseverative_errors')
    cc_entry = next(m for m in corrected['bonferroni_metrics'] if m['metric'] == 'categories_completed')
    
    # Verify calculations
    expected_pe_corr = 0.012 * 2
    expected_cc_corr = 0.075 * 2
    
    assert np.isclose(pe_entry['bonferroni_corrected_p_value'], expected_pe_corr)
    assert np.isclose(cc_entry['bonferroni_corrected_p_value'], expected_cc_corr)
    
    # Verify significance flags (alpha = 0.05)
    assert pe_entry['is_significant_at_0.05'] == True  # 0.024 < 0.05
    assert cc_entry['is_significant_at_0.05'] == False # 0.150 > 0.05
    
    # Verify top-level updates
    assert np.isclose(corrected['perseverative_errors']['bonferroni_corrected_p_value'], expected_pe_corr)
    assert corrected['perseverative_errors']['is_significant_after_correction'] == True

def test_apply_bonferroni_no_p_values():
    """Test behavior when no p-values are found."""
    data = {
        "other_field": "value"
    }
    
    corrected = apply_bonferroni_correction(data)
    
    assert corrected['bonferroni_status'] == 'failed_no_p_values'
    assert 'bonferroni_metrics' not in corrected or len(corrected.get('bonferroni_metrics', [])) == 0

def test_save_bonferroni_results(tmp_path):
    """Test that results are saved correctly to a file."""
    results = {
        "test": "data",
        "bonferroni_status": "success"
    }
    
    # Temporarily override the output path for testing
    import task_t019_bonferroni_correction as mod
    original_path = mod.BONFERRONI_OUTPUT_PATH
    mod.BONFERRONI_OUTPUT_PATH = tmp_path / "test_bonferroni.json"
    
    try:
        path = save_bonferroni_results(results)
        
        assert os.path.exists(path)
        with open(path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == results
    finally:
        # Restore original path
        mod.BONFERRONI_OUTPUT_PATH = original_path
