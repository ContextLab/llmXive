"""
Unit tests for stability check functionality.

Tests the logic for flagging results if:
1. Correlation remains significant (p < 0.05) in < 2 of 3 thresholds.
2. |Δrho| > 0.1 across the thresholds.
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.stability_check import (
    check_significance_count,
    calculate_max_rho_diff,
    perform_stability_check,
    load_sensitivity_results,
    save_results
)


@pytest.fixture
def stable_results():
    """Create mock sensitivity results that should pass stability check."""
    return {
        "thresholds": [
            {"threshold": 3, "rho": 0.65, "p_value": 0.01},
            {"threshold": 4, "rho": 0.63, "p_value": 0.02},
            {"threshold": 5, "rho": 0.64, "p_value": 0.015}
        ]
    }


@pytest.fixture
def unstable_significance_results():
    """Create mock results with insufficient significant correlations."""
    return {
        "thresholds": [
            {"threshold": 3, "rho": 0.65, "p_value": 0.01},
            {"threshold": 4, "rho": 0.63, "p_value": 0.08},  # Not significant
            {"threshold": 5, "rho": 0.64, "p_value": 0.12}   # Not significant
        ]
    }


@pytest.fixture
def unstable_rho_results():
    """Create mock results with high rho variation."""
    return {
        "thresholds": [
            {"threshold": 3, "rho": 0.80, "p_value": 0.01},
            {"threshold": 4, "rho": 0.55, "p_value": 0.02},  # |Δrho| = 0.25
            {"threshold": 5, "rho": 0.60, "p_value": 0.015}
        ]
    }


@pytest.fixture
def missing_pvalue_results():
    """Create mock results with missing p-values."""
    return {
        "thresholds": [
            {"threshold": 3, "rho": 0.65},
            {"threshold": 4, "rho": 0.63, "p_value": 0.02},
            {"threshold": 5, "rho": 0.64, "p_value": 0.015}
        ]
    }


def test_check_significance_count_stable(stable_results):
    """Test significance count with stable results."""
    count, flags = check_significance_count(stable_results)
    assert count == 3
    assert flags == [True, True, True]


def test_check_significance_count_unstable(unstable_significance_results):
    """Test significance count with unstable results (only 1 significant)."""
    count, flags = check_significance_count(unstable_significance_results)
    assert count == 1
    assert flags == [True, False, False]


def test_check_significance_count_missing_pvalue(missing_pvalue_results):
    """Test significance count with missing p-values."""
    count, flags = check_significance_count(missing_pvalue_results)
    assert count == 2
    assert flags == [False, True, True]


def test_calculate_max_rho_diff_stable(stable_results):
    """Test max rho difference with stable results."""
    max_diff = calculate_max_rho_diff(stable_results)
    assert abs(max_diff - 0.02) < 0.001  # 0.65 - 0.63


def test_calculate_max_rho_diff_unstable(unstable_rho_results):
    """Test max rho difference with unstable results."""
    max_diff = calculate_max_rho_diff(unstable_rho_results)
    assert abs(max_diff - 0.25) < 0.001  # 0.80 - 0.55


def test_calculate_max_rho_diff_insufficient_data():
    """Test max rho difference with insufficient data."""
    results = {"thresholds": [{"threshold": 3, "rho": 0.65}]}
    max_diff = calculate_max_rho_diff(results)
    assert max_diff == 0.0


def test_perform_stability_check_stable(stable_results):
    """Test full stability check with stable results."""
    result = perform_stability_check(stable_results)
    
    assert result["stability_check"]["is_stable"] is True
    assert result["stability_check"]["status"] == "STABLE"
    assert result["stability_check"]["significant_count"] == 3
    assert result["stability_check"]["significance_stable"] is True
    assert result["stability_check"]["rho_stable"] is True
    assert result["stability_check"]["flags"]["insufficient_significance"] is False
    assert result["stability_check"]["flags"]["high_rho_variation"] is False


def test_perform_stability_check_unstable_significance(unstable_significance_results):
    """Test stability check with insufficient significance."""
    result = perform_stability_check(unstable_significance_results)
    
    assert result["stability_check"]["is_stable"] is False
    assert result["stability_check"]["status"] == "UNSTABLE"
    assert result["stability_check"]["significant_count"] == 1
    assert result["stability_check"]["significance_stable"] is False
    assert result["stability_check"]["rho_stable"] is True
    assert result["stability_check"]["flags"]["insufficient_significance"] is True
    assert result["stability_check"]["flags"]["high_rho_variation"] is False


def test_perform_stability_check_unstable_rho(unstable_rho_results):
    """Test stability check with high rho variation."""
    result = perform_stability_check(unstable_rho_results)
    
    assert result["stability_check"]["is_stable"] is False
    assert result["stability_check"]["status"] == "UNSTABLE"
    assert result["stability_check"]["significant_count"] == 3
    assert result["stability_check"]["significance_stable"] is True
    assert result["stability_check"]["rho_stable"] is False
    assert result["stability_check"]["flags"]["insufficient_significance"] is False
    assert result["stability_check"]["flags"]["high_rho_variation"] is True


def test_save_results(tmp_path):
    """Test saving results to file."""
    results = {
        "stability_check": {
            "is_stable": True,
            "status": "STABLE"
        }
    }
    
    output_path = tmp_path / "test_results.json"
    saved_path = save_results(results, str(output_path))
    
    assert Path(saved_path).exists()
    
    with open(saved_path, 'r') as f:
        loaded = json.load(f)
        
    assert loaded["stability_check"]["is_stable"] is True


def test_load_sensitivity_results(tmp_path):
    """Test loading sensitivity results from file."""
    data = {
        "thresholds": [
            {"threshold": 3, "rho": 0.65, "p_value": 0.01}
        ]
    }
    
    input_path = tmp_path / "sensitivity.json"
    with open(input_path, 'w') as f:
        json.dump(data, f)
        
    loaded = load_sensitivity_results(str(input_path))
    assert loaded["thresholds"][0]["rho"] == 0.65


def test_load_sensitivity_results_not_found():
    """Test loading from non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_sensitivity_results("nonexistent/path.json")