"""
Unit tests for rank stability check functionality.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure parent directory is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models.rank_stability import (
    get_top_n_features,
    calculate_rank_shift,
    verify_rank_stability,
    generate_stability_report
)

@pytest.fixture
def mock_sensitivity_results():
    """Mock sensitivity analysis results for testing."""
    return {
        "thresholds": [0.45, 0.50, 0.55],
        "results": {
            "0.45": {
                "feature_importances": {
                    "feature_a": 0.30,
                    "feature_b": 0.25,
                    "feature_c": 0.20,
                    "feature_d": 0.15,
                    "feature_e": 0.10
                }
            },
            "0.50": {
                "feature_importances": {
                    "feature_a": 0.31,
                    "feature_b": 0.24,
                    "feature_c": 0.21,
                    "feature_d": 0.14,
                    "feature_e": 0.10
                }
            },
            "0.55": {
                "feature_importances": {
                    "feature_a": 0.29,
                    "feature_b": 0.26,
                    "feature_c": 0.19,
                    "feature_d": 0.16,
                    "feature_e": 0.10
                }
            }
        }
    }

@pytest.fixture
def mock_sensitivity_results_unstable():
    """Mock sensitivity results where top features shift significantly."""
    return {
        "thresholds": [0.45, 0.50],
        "results": {
            "0.45": {
                "feature_importances": {
                    "feature_a": 0.40,
                    "feature_b": 0.30,
                    "feature_c": 0.20,
                    "feature_d": 0.10
                }
            },
            "0.50": {
                "feature_importances": {
                    "feature_d": 0.45,
                    "feature_c": 0.35,
                    "feature_b": 0.15,
                    "feature_a": 0.05
                }
            }
        }
    }

def test_get_top_n_features():
    """Test that top N features are correctly identified."""
    importances = {"a": 0.1, "b": 0.5, "c": 0.3, "d": 0.2}
    top_2 = get_top_n_features(importances, n=2)
    assert len(top_2) == 2
    assert top_2[0][0] == "b"  # Highest
    assert top_2[0][1] == 0.5
    assert top_2[1][0] == "c"  # Second highest
    assert top_2[1][1] == 0.3

def test_calculate_rank_shift():
    """Test rank shift calculation."""
    assert calculate_rank_shift(0, 0) == 0
    assert calculate_rank_shift(0, 1) == 1
    assert calculate_rank_shift(1, 3) == 2
    assert calculate_rank_shift(2, 0) == 2

def test_verify_rank_stability_stable(mock_sensitivity_results):
    """Test verification with stable data (shifts <= 1)."""
    is_stable, details = verify_rank_stability(mock_sensitivity_results, max_shift=1, top_n=3)
    assert is_stable is True
    # Check that details contain the expected features
    assert "feature_a" in details
    assert "feature_b" in details
    assert "feature_c" in details
    # Check shifts are 0 or 1
    for feature, threshold_details in details.items():
        for threshold, info in threshold_details.items():
            assert info["shift"] <= 1

def test_verify_rank_stability_unstable(mock_sensitivity_results_unstable):
    """Test verification with unstable data (shifts > 1)."""
    is_stable, details = verify_rank_stability(mock_sensitivity_results_unstable, max_shift=1, top_n=3)
    assert is_stable is False
    # feature_a was rank 0, now rank 3 -> shift 3
    assert details["feature_a"]["0.50"]["shift"] == 3

def test_generate_stability_report(tmp_path):
    """Test report generation."""
    is_stable = True
    details = {
        "feature_a": {"0.45": {"baseline_rank": 0, "current_rank": 0, "shift": 0, "stable": True}}
    }
    output_path = tmp_path / "test_report.txt"
    
    report = generate_stability_report(is_stable, details, output_path)
    
    assert "RANK STABILITY ANALYSIS REPORT" in report
    assert "Overall Result: STABLE" in report
    assert output_path.exists()
    with open(output_path, 'r') as f:
        content = f.read()
    assert "feature_a" in content

def test_verify_rank_stability_missing_threshold():
    """Test handling of missing threshold results."""
    results = {
        "thresholds": [0.45, 0.50],
        "results": {
            "0.45": {"feature_importances": {"a": 0.5, "b": 0.3}}
            # Missing 0.50
        }
    }
    # Should not raise, just skip missing
    is_stable, details = verify_rank_stability(results, max_shift=1, top_n=2)
    assert is_stable is True  # Only one comparison possible, and it's identical

def test_verify_rank_stability_invalid_structure():
    """Test handling of invalid structure."""
    results = {"thresholds": [], "results": {}}
    with pytest.raises(ValueError, match="Invalid sensitivity results structure"):
        verify_rank_stability(results)
    
    results = {"thresholds": [0.45], "results": {}}
    with pytest.raises(ValueError, match="Results for baseline threshold"):
        verify_rank_stability(results)