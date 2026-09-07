"""
Tests for T034b: Success criteria verification.
"""
import json
import tempfile
from pathlib import Path
import pytest

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from verify_success_criteria import verify_success_criteria, CRITERIA

def test_verify_success_criteria_all_pass():
    """Test verification when all criteria pass."""
    # Create a mock final report with passing values
    mock_report = {
        "primary_model": {
            "p_value": 0.03,
            "pearson_r": 0.45,
            "mae": 0.85,
            "r_squared": 0.20
        },
        "null_model": {
            "mean_mae": 0.08,
            "std_mae": 0.02,
            "max_mae": 0.12
        },
        "robustness": {
            "alpha_sweep": {
                "corr_std": 0.03,
                "mae_range": [0.82, 0.88],
                "optimal_alpha": 1.0
            },
            "variance_metric": {
                "pearson_r": 0.43,
                "p_value": 0.02
            },
            "partial_correlation": {
                "pearson_r": 0.41,
                "p_value": 0.04
            }
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "final_report.json"
        with open(report_path, 'w') as f:
            json.dump(mock_report, f)
        
        results = verify_success_criteria(report_path)
        
        assert results["all_passed"] is True
        assert len(results["failed_criteria"]) == 0
        
        # Check individual criteria
        assert results["criteria_results"]["sc_001"]["passed"] is True
        assert results["criteria_results"]["sc_002"]["passed"] is True
        assert results["criteria_results"]["sc_003"]["passed"] is True
        assert results["criteria_results"]["sc_004"]["passed"] is True
        assert results["criteria_results"]["sc_005"]["passed"] is True

def test_verify_success_criteria_p_value_fail():
    """Test verification when p-value criterion fails."""
    mock_report = {
        "primary_model": {
            "p_value": 0.08,  # > 0.05, should fail
            "pearson_r": 0.45,
            "mae": 0.85,
            "r_squared": 0.20
        },
        "null_model": {
            "mean_mae": 0.08,
            "std_mae": 0.02,
            "max_mae": 0.12
        },
        "robustness": {
            "alpha_sweep": {
                "corr_std": 0.03,
                "mae_range": [0.82, 0.88],
                "optimal_alpha": 1.0
            },
            "variance_metric": {
                "pearson_r": 0.43,
                "p_value": 0.02
            },
            "partial_correlation": {
                "pearson_r": 0.41,
                "p_value": 0.04
            }
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "final_report.json"
        with open(report_path, 'w') as f:
            json.dump(mock_report, f)
        
        results = verify_success_criteria(report_path)
        
        assert results["all_passed"] is False
        assert len(results["failed_criteria"]) == 1
        assert results["failed_criteria"][0]["id"] == "sc_001"
        assert results["criteria_results"]["sc_001"]["passed"] is False

def test_verify_success_criteria_null_model_fail():
    """Test verification when null model criterion fails."""
    mock_report = {
        "primary_model": {
            "p_value": 0.03,
            "pearson_r": 0.45,
            "mae": 0.85,
            "r_squared": 0.20
        },
        "null_model": {
            "mean_mae": 0.15,  # > 0.1, should fail
            "std_mae": 0.02,
            "max_mae": 0.12
        },
        "robustness": {
            "alpha_sweep": {
                "corr_std": 0.03,
                "mae_range": [0.82, 0.88],
                "optimal_alpha": 1.0
            },
            "variance_metric": {
                "pearson_r": 0.43,
                "p_value": 0.02
            },
            "partial_correlation": {
                "pearson_r": 0.41,
                "p_value": 0.04
            }
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "final_report.json"
        with open(report_path, 'w') as f:
            json.dump(mock_report, f)
        
        results = verify_success_criteria(report_path)
        
        assert results["all_passed"] is False
        assert len(results["failed_criteria"]) == 1
        assert results["failed_criteria"][0]["id"] == "sc_002"

def test_verify_success_criteria_missing_key():
    """Test verification when required key is missing."""
    mock_report = {
        "primary_model": {
            "p_value": 0.03,
            # Missing 'pearson_r'
            "mae": 0.85,
            "r_squared": 0.20
        },
        "null_model": {
            "mean_mae": 0.08,
            "std_mae": 0.02,
            "max_mae": 0.12
        },
        "robustness": {
            "alpha_sweep": {
                "corr_std": 0.03,
                "mae_range": [0.82, 0.88],
                "optimal_alpha": 1.0
            },
            "variance_metric": {
                "pearson_r": 0.43,
                "p_value": 0.02
            },
            "partial_correlation": {
                "pearson_r": 0.41,
                "p_value": 0.04
            }
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "final_report.json"
        with open(report_path, 'w') as f:
            json.dump(mock_report, f)
        
        results = verify_success_criteria(report_path)
        
        assert results["all_passed"] is False
        assert results["criteria_results"]["sc_004"]["status"] == "ERROR"

def test_verify_success_criteria_file_not_found():
    """Test verification when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        verify_success_criteria(Path("/nonexistent/path/final_report.json"))

def test_criteria_definitions():
    """Test that all criteria are properly defined."""
    expected_criteria = ["sc_001", "sc_002", "sc_003", "sc_004", "sc_005"]
    
    for criterion_id in expected_criteria:
        assert criterion_id in CRITERIA
        assert "description" in CRITERIA[criterion_id]
        assert "check" in CRITERIA[criterion_id]
        assert callable(CRITERIA[criterion_id]["check"])
        assert "critical" in CRITERIA[criterion_id]