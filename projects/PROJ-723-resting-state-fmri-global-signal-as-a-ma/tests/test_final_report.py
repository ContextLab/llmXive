import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from run_final_report import evaluate_success_criteria

class TestSuccessCriteriaEvaluation:
    
    def test_sc001_significant_p_value(self):
        """Test SC-001 when p-value < 0.05"""
        mock_model = {"p_value": 0.03}
        mock_robustness = {}
        mock_diagnostics = {}
        mock_delta_r2 = {}
        mock_null_dist = {}
        mock_full_model = {"mae": 1.0, "r": 0.3, "r_squared": 0.09}

        result = evaluate_success_criteria(
            mock_model, mock_robustness, mock_diagnostics, mock_delta_r2, mock_null_dist, mock_full_model
        )
        
        assert "SC-001" in result
        assert result["SC-001"]["status"] == "met"
        assert "Significant" in result["SC-001"]["narrative_summary"]
        assert result["SC-001"]["metrics"]["p_value"] == 0.03

    def test_sc001_null_p_value(self):
        """Test SC-001 when p-value >= 0.05"""
        mock_model = {"p_value": 0.12}
        mock_robustness = {}
        mock_diagnostics = {}
        mock_delta_r2 = {}
        mock_null_dist = {}
        mock_full_model = {"mae": 1.0, "r": 0.3, "r_squared": 0.09}

        result = evaluate_success_criteria(
            mock_model, mock_robustness, mock_diagnostics, mock_delta_r2, mock_null_dist, mock_full_model
        )
        
        assert result["SC-001"]["status"] == "not met"
        assert "Null finding" in result["SC-001"]["narrative_summary"]

    def test_sc003_stable_correlation(self):
        """Test SC-003 when |r_var - r_sd| <= 0.05"""
        mock_model = {"p_value": 0.03}
        mock_robustness = {
            "variance_metric_analysis": {
                "correlation_sd": 0.30,
                "correlation_var": 0.32
            }
        }
        mock_diagnostics = {}
        mock_delta_r2 = {}
        mock_null_dist = {}
        mock_full_model = {"mae": 1.0, "r": 0.3, "r_squared": 0.09}

        result = evaluate_success_criteria(
            mock_model, mock_robustness, mock_diagnostics, mock_delta_r2, mock_null_dist, mock_full_model
        )
        
        assert result["SC-003"]["status"] == "met"
        assert abs(result["SC-003"]["metrics"]["absolute_difference"] - 0.02) < 0.001

    def test_sc003_unstable_correlation(self):
        """Test SC-003 when |r_var - r_sd| > 0.05"""
        mock_model = {"p_value": 0.03}
        mock_robustness = {
            "variance_metric_analysis": {
                "correlation_sd": 0.30,
                "correlation_var": 0.40
            }
        }
        mock_diagnostics = {}
        mock_delta_r2 = {}
        mock_null_dist = {}
        mock_full_model = {"mae": 1.0, "r": 0.3, "r_squared": 0.09}

        result = evaluate_success_criteria(
            mock_model, mock_robustness, mock_diagnostics, mock_delta_r2, mock_null_dist, mock_full_model
        )
        
        assert result["SC-003"]["status"] == "not met"

    def test_sc004_stable_mae(self):
        """Test SC-004 when MAE variation < 10%"""
        mock_model = {"p_value": 0.03}
        mock_robustness = {
            "alpha_sweep": {
                "mean_mae": 1.0,
                "max_mae": 1.05,
                "min_mae": 0.95
            }
        }
        mock_diagnostics = {}
        mock_delta_r2 = {}
        mock_null_dist = {}
        mock_full_model = {"mae": 1.0, "r": 0.3, "r_squared": 0.09}

        result = evaluate_success_criteria(
            mock_model, mock_robustness, mock_diagnostics, mock_delta_r2, mock_null_dist, mock_full_model
        )
        
        # Variation = (1.05 - 0.95) / 1.0 = 0.10 = 10%. 
        # Threshold is < 10%. So 10% exactly should be "not met".
        # Let's adjust test data to be clearly under.
        mock_robustness["alpha_sweep"]["max_mae"] = 1.04
        mock_robustness["alpha_sweep"]["min_mae"] = 0.96
        # Variation = 0.08 / 1.0 = 8%
        
        result = evaluate_success_criteria(
            mock_model, mock_robustness, mock_diagnostics, mock_delta_r2, mock_null_dist, mock_full_model
        )
        
        assert result["SC-004"]["status"] == "met"
        assert result["SC-004"]["metrics"]["variation_percentage"] < 10.0

    def test_sc002_and_sc005_partial_corr(self):
        """Test SC-002 and SC-005 using partial correlation p-value"""
        mock_model = {"p_value": 0.03}
        mock_robustness = {
            "partial_correlation": {
                "p_value": 0.04
            }
        }
        mock_diagnostics = {}
        mock_delta_r2 = {}
        mock_null_dist = {}
        mock_full_model = {"mae": 1.0, "r": 0.3, "r_squared": 0.09}

        result = evaluate_success_criteria(
            mock_model, mock_robustness, mock_diagnostics, mock_delta_r2, mock_null_dist, mock_full_model
        )
        
        assert result["SC-002"]["status"] == "met"
        assert result["SC-005"]["status"] == "met"
        
        # Test null case
        mock_robustness["partial_correlation"]["p_value"] = 0.15
        result = evaluate_success_criteria(
            mock_model, mock_robustness, mock_diagnostics, mock_delta_r2, mock_null_dist, mock_full_model
        )
        
        assert result["SC-002"]["status"] == "not met"
        assert result["SC-005"]["status"] == "not met"
        assert "Null finding" in result["SC-002"]["narrative_summary"]