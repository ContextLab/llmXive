"""
Unit tests for sensitivity metrics verification (Task T034).

These tests verify that:
1. E-values are calculated correctly
2. Sensitivity metrics are framed as robustness measures, not causal effects
3. The verification report correctly identifies causal vs associational language
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from sensitivity_metrics import (
    compute_sensitivity_metrics,
    generate_sensitivity_verification_report,
    calculate_e_value
)
from robustness import calculate_e_value as robustness_e_value

class TestEValueCalculation:
    """Tests for E-value calculation accuracy."""
    
    def test_e_value_basic_calculation(self):
        """Test basic E-value calculation with known values."""
        # For p=0.05 and coefficient=0.5, E-value should be calculable
        p_val = 0.05
        coeff = 0.5
        
        e_val = calculate_e_value(p_val, coeff)
        
        # E-value should be positive and greater than 1 for significant results
        assert e_val > 1.0
        assert isinstance(e_val, float)
    
    def test_e_value_with_high_significance(self):
        """Test E-value with highly significant p-value."""
        p_val = 0.001
        coeff = 1.0
        
        e_val = calculate_e_value(p_val, coeff)
        
        # More significant results should have higher E-values
        assert e_val > 1.5
    
    def test_e_value_with_non_significant(self):
        """Test E-value with non-significant p-value."""
        p_val = 0.5
        coeff = 0.1
        
        e_val = calculate_e_value(p_val, coeff)
        
        # Non-significant results should have E-values closer to 1
        assert e_val >= 1.0

class TestSensitivityMetrics:
    """Tests for sensitivity metric computation."""
    
    def test_sensitivity_metrics_structure(self):
        """Test that sensitivity metrics contain all required fields."""
        coeff = 0.5
        p_val = 0.03
        
        metrics = compute_sensitivity_metrics(coeff, p_val)
        
        required_fields = [
            "e_value", "robustness_level", "interpretation",
            "observed_coefficient", "observed_p_value", "framing"
        ]
        
        for field in required_fields:
            assert field in metrics, f"Missing required field: {field}"
    
    def test_sensitivity_metrics_framing(self):
        """Test that sensitivity metrics use associational framing."""
        coeff = 0.5
        p_val = 0.03
        
        metrics = compute_sensitivity_metrics(coeff, p_val)
        
        # Verify framing is set correctly
        assert metrics["framing"] == "associational_sensitivity_metric"
        
        # Verify no causal language in interpretation
        causal_terms = ["causes", "leads to", "effect size", "causal impact"]
        interpretation_lower = metrics["interpretation"].lower()
        
        for term in causal_terms:
            assert term not in interpretation_lower, \
                f"Causal language detected in interpretation: {term}"
    
    def test_robustness_level_classification(self):
        """Test that robustness levels are correctly classified."""
        # Strong robustness (E-value > 2.0)
        metrics_strong = compute_sensitivity_metrics(0.8, 0.001)
        assert metrics_strong["robustness_level"] in ["Strong", "Moderate"]
        
        # Weak robustness (E-value < 1.5)
        metrics_weak = compute_sensitivity_metrics(0.1, 0.5)
        assert metrics_weak["robustness_level"] in ["Weak", "Moderate"]

class TestVerificationReport:
    """Tests for the verification report generation."""
    
    def test_report_structure(self):
        """Test that verification report contains all required sections."""
        mock_model_results = {
            "primary_analysis": {
                "coefficient": 0.5,
                "p_value": 0.03
            }
        }
        
        mock_sensitivity_data = pd.DataFrame({
            "threshold": [0.01, 0.05, 0.1],
            "coefficient": [0.5, 0.48, 0.52],
            "p_value": [0.03, 0.04, 0.025]
        })
        
        report = generate_sensitivity_verification_report(
            mock_model_results, 
            mock_sensitivity_data
        )
        
        required_sections = [
            "task_id", "verification_status", "framing_verification",
            "sensitivity_metrics", "threshold_stability", "conclusion"
        ]
        
        for section in required_sections:
            assert section in report, f"Missing required section: {section}"
    
    def test_framing_verification_accuracy(self):
        """Test that framing verification correctly identifies language."""
        mock_model_results = {
            "primary_analysis": {
                "coefficient": 0.5,
                "p_value": 0.03
            }
        }
        
        mock_sensitivity_data = pd.DataFrame({
            "threshold": [0.01, 0.05, 0.1],
            "coefficient": [0.5, 0.48, 0.52],
            "p_value": [0.03, 0.04, 0.025]
        })
        
        report = generate_sensitivity_verification_report(
            mock_model_results, 
            mock_sensitivity_data
        )
        
        # Verify framing check is performed
        assert "causal_language_detected" in report["framing_verification"]
        assert "sensitivity_framing_present" in report["framing_verification"]
        
        # In our implementation, causal language should NOT be detected
        assert report["framing_verification"]["causal_language_detected"] is False
    
    def test_threshold_stability_analysis(self):
        """Test that threshold stability is correctly analyzed."""
        mock_model_results = {
            "primary_analysis": {
                "coefficient": 0.5,
                "p_value": 0.03
            }
        }
        
        mock_sensitivity_data = pd.DataFrame({
            "threshold": [0.01, 0.05, 0.1],
            "coefficient": [0.5, 0.48, 0.52],
            "p_value": [0.03, 0.04, 0.025]
        })
        
        report = generate_sensitivity_verification_report(
            mock_model_results, 
            mock_sensitivity_data
        )
        
        # Verify threshold stability results
        assert "threshold_stability" in report
        assert len(report["threshold_stability"]) == 3
        
        # Check that each threshold result has required fields
        for result in report["threshold_stability"]:
            assert "threshold" in result
            assert "e_value" in result
            assert "is_significant" in result

class TestIntegration:
    """Integration tests for the full verification pipeline."""
    
    def test_end_to_end_verification(self):
        """Test the complete verification workflow."""
        # Create mock data that simulates real pipeline output
        mock_model_results = {
            "primary_analysis": {
                "coefficient": 0.45,
                "p_value": 0.02,
                "method": "weighted_regression"
            },
            "diagnostics": {
                "vif_max": 2.1,
                "weight_stability": "stable"
            }
        }
        
        mock_sensitivity_data = pd.DataFrame({
            "threshold": [0.01, 0.05, 0.1],
            "coefficient": [0.45, 0.42, 0.48],
            "p_value": [0.02, 0.035, 0.018]
        })
        
        # Generate report
        report = generate_sensitivity_verification_report(
            mock_model_results, 
            mock_sensitivity_data
        )
        
        # Verify the report meets T034 requirements
        assert report["task_id"] == "T034"
        assert report["verification_status"] == "completed"
        assert not report["framing_verification"]["causal_language_detected"]
        assert report["framing_verification"]["sensitivity_framing_present"]
        
        # Verify sensitivity metrics are present and valid
        assert report["sensitivity_metrics"]["e_value"] > 1.0
        assert report["sensitivity_metrics"]["framing"] == "associational_sensitivity_metric"
        
        # Verify conclusion emphasizes associational framing
        conclusion = report["conclusion"].lower()
        assert "associational" in conclusion or "sensitivity" in conclusion
        
        # Verify recommendations focus on associational framing
        recommendations = report["recommendations"]
        assert any("associational" in rec.lower() for rec in recommendations)