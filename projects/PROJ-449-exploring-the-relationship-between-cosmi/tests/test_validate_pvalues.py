"""
Tests for p-value validation logic (Task T024).

These tests verify that:
1. The validation correctly identifies missing p-values
2. Non-significant results (p > 0.01) are properly flagged
3. The validation report is generated correctly
"""
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from code.analysis.validate_pvalues import (
    validate_pvalues_exist,
    flag_non_significant_results,
    generate_validation_report
)

@pytest.fixture
def sample_correlation_data():
    """Sample correlation data for testing."""
    return {
        "results": {
            "1.0 GV": {
                "He/p": {
                    "correlations": [
                        {"lag_months": 0, "coefficient": 0.85, "p_value": 0.001},
                        {"lag_months": 1, "coefficient": 0.72, "p_value": 0.05},
                        {"lag_months": -1, "coefficient": 0.68, "p_value": 0.08}
                    ]
                },
                "Fe/p": {
                    "correlations": [
                        {"lag_months": 0, "coefficient": 0.45, "p_value": 0.0001},
                        {"lag_months": 1, "coefficient": 0.32, "p_value": 0.15},
                        {"lag_months": 2, "coefficient": 0.28, "p_value": 0.22}
                    ]
                },
                "He_flux": {
                    "correlations": [
                        {"lag_months": 0, "coefficient": 0.88, "p_value": 0.0005},
                        {"lag_months": 1, "coefficient": 0.75, "p_value": 0.03}
                    ]
                },
                "Fe_flux": {
                    "correlations": [
                        {"lag_months": 0, "coefficient": 0.52, "p_value": 0.0002},
                        {"lag_months": 1, "coefficient": 0.41, "p_value": 0.09}
                    ]
                }
            },
            "2.0 GV": {
                "He/p": {
                    "correlations": [
                        {"lag_months": 0, "coefficient": 0.79, "p_value": 0.002},
                        {"lag_months": 1, "coefficient": 0.65, "p_value": 0.04}
                    ]
                },
                "Fe/p": {
                    "correlations": [
                        {"lag_months": 0, "coefficient": 0.38, "p_value": 0.003},
                        {"lag_months": 1, "coefficient": 0.29, "p_value": 0.18}
                    ]
                },
                "He_flux": {
                    "correlations": [
                        {"lag_months": 0, "coefficient": 0.82, "p_value": 0.001}
                    ]
                },
                "Fe_flux": {
                    "correlations": [
                        {"lag_months": 0, "coefficient": 0.47, "p_value": 0.004}
                    ]
                }
            }
        }
    }

@pytest.fixture
def sample_data_missing_pvalues():
    """Sample data with missing p-values for testing."""
    return {
        "results": {
            "1.0 GV": {
                "He/p": {
                    "correlations": [
                        {"lag_months": 0, "coefficient": 0.85, "p_value": 0.001},
                        {"lag_months": 1, "coefficient": 0.72},  # Missing p_value
                        {"lag_months": -1, "coefficient": 0.68, "p_value": 0.08}
                    ]
                }
            }
        }
    }

def test_validate_pvalues_exist_all_present(sample_correlation_data):
    """Test that validation correctly counts all valid p-values."""
    total, valid, missing = validate_pvalues_exist(sample_correlation_data)
    
    # Count expected: 3+3+2+2 + 2+2+1+1 = 16
    assert total == 16
    assert valid == 16
    assert len(missing) == 0

def test_validate_pvalues_exist_missing_entries(sample_data_missing_pvalues):
    """Test that validation detects missing p-values."""
    total, valid, missing = validate_pvalues_exist(sample_data_missing_pvalues)
    
    assert total == 3
    assert valid == 2
    assert len(missing) == 1
    assert "missing p_value" in missing[0].lower()

def test_flag_non_significant_results(sample_correlation_data):
    """Test that non-significant results (p > 0.01) are flagged."""
    non_sig = flag_non_significant_results(sample_correlation_data)
    
    # He/p at 1.0 GV: lag 1 (p=0.05), lag -1 (p=0.08) -> 2 non-sig
    # Fe/p at 1.0 GV: lag 1 (p=0.15), lag 2 (p=0.22) -> 2 non-sig
    # He_flux at 1.0 GV: lag 1 (p=0.03) -> 1 non-sig
    # Fe_flux at 1.0 GV: lag 1 (p=0.09) -> 1 non-sig
    # He/p at 2.0 GV: lag 1 (p=0.04) -> 1 non-sig
    # Fe/p at 2.0 GV: lag 1 (p=0.18) -> 1 non-sig
    
    assert len(non_sig["He/p"]) == 3
    assert len(non_sig["Fe/p"]) == 3
    assert len(non_sig["He_flux"]) == 1
    assert len(non_sig["Fe_flux"]) == 1

def test_flag_non_significant_all_significant():
    """Test with all significant results."""
    data = {
        "results": {
            "1.0 GV": {
                "He/p": {
                    "correlations": [
                        {"lag_months": 0, "coefficient": 0.85, "p_value": 0.001},
                        {"lag_months": 1, "coefficient": 0.72, "p_value": 0.005}
                    ]
                }
            }
        }
    }
    
    non_sig = flag_non_significant_results(data)
    
    assert len(non_sig["He/p"]) == 0
    assert len(non_sig["Fe/p"]) == 0
    assert len(non_sig["He_flux"]) == 0
    assert len(non_sig["Fe_flux"]) == 0

def test_generate_validation_report_structure(sample_correlation_data):
    """Test that the validation report contains expected sections."""
    total, valid, missing = validate_pvalues_exist(sample_correlation_data)
    non_sig = flag_non_significant_results(sample_correlation_data)
    
    report = generate_validation_report(total, valid, missing, non_sig)
    
    assert "# P-Value Validation Report" in report
    assert "## Summary Statistics" in report
    assert "## Non-Significant Results" in report
    assert "## Overall Statistics" in report
    assert "p > 0.01" in report

def test_generate_validation_report_missing_pvalues(sample_data_missing_pvalues):
    """Test that the report includes missing p-value section."""
    total, valid, missing = validate_pvalues_exist(sample_data_missing_pvalues)
    non_sig = flag_non_significant_results(sample_data_missing_pvalues)
    
    report = generate_validation_report(total, valid, missing, non_sig)
    
    assert "## Missing P-Values" in report
    assert "Missing P-Values" in report

def test_generate_validation_report_empty_data():
    """Test report generation with empty data."""
    data = {"results": {}}
    total, valid, missing = validate_pvalues_exist(data)
    non_sig = flag_non_significant_results(data)
    
    report = generate_validation_report(total, valid, missing, non_sig)
    
    assert "No correlations found to analyze" in report or "Total Correlation Tests: 0" in report

def test_pvalue_threshold_boundary():
    """Test that p=0.01 is treated as significant (not flagged)."""
    data = {
        "results": {
            "1.0 GV": {
                "He/p": {
                    "correlations": [
                        {"lag_months": 0, "coefficient": 0.85, "p_value": 0.01},
                        {"lag_months": 1, "coefficient": 0.72, "p_value": 0.010001}
                    ]
                }
            }
        }
    }
    
    non_sig = flag_non_significant_results(data)
    
    # p=0.01 should be significant (not flagged)
    # p=0.010001 should be non-significant (flagged)
    assert len(non_sig["He/p"]) == 1
    assert non_sig["He/p"][0]["lag_months"] == 1
