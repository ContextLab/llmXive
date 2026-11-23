"""
Unit tests for T029: Borderline Flag Implementation.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from code.task_t029_threshold_sensitivity import is_borderline, analyze_threshold_sensitivity

class TestIsBorderline:
    """Tests for the is_borderline function."""

    def test_borderline_lower_bound(self):
        """Test p-value exactly at lower bound (0.04)."""
        assert is_borderline(0.04) is True

    def test_borderline_upper_bound(self):
        """Test p-value exactly at upper bound (0.06)."""
        assert is_borderline(0.06) is True

    def test_borderline_middle(self):
        """Test p-value in the middle of the range."""
        assert is_borderline(0.05) is True

    def test_below_borderline(self):
        """Test p-value below the borderline range."""
        assert is_borderline(0.039) is False
        assert is_borderline(0.01) is False

    def test_above_borderline(self):
        """Test p-value above the borderline range."""
        assert is_borderline(0.061) is False
        assert is_borderline(0.10) is False

    def test_none_input(self):
        """Test handling of None input."""
        assert is_borderline(None) is False

    def test_tolerance_low(self):
        """Test p-value within tolerance below lower bound."""
        assert is_borderline(0.04 - 1e-9) is True

    def test_tolerance_high(self):
        """Test p-value within tolerance above upper bound."""
        assert is_borderline(0.06 + 1e-9) is True

class TestAnalyzeThresholdSensitivity:
    """Tests for the analyze_threshold_sensitivity function."""

    def test_flag_set_for_borderline_pe(self):
        """Test flag is set when primary_pe_p_value is borderline."""
        report = {
            "summary": {
                "primary_pe_p_value": 0.045,
                "primary_cc_p_value": 0.032
            },
            "results": [
                {"threshold": 0.01, "is_sensitive_to_threshold": False},
                {"threshold": 0.05, "is_sensitive_to_threshold": False}
            ]
        }
        
        updated = analyze_threshold_sensitivity(report)
        
        # Both results should have the flag set because PE is borderline
        assert updated["results"][0]["is_sensitive_to_threshold"] is True
        assert updated["results"][1]["is_sensitive_to_threshold"] is True

    def test_flag_set_for_borderline_cc(self):
        """Test flag is set when primary_cc_p_value is borderline."""
        report = {
            "summary": {
                "primary_pe_p_value": 0.01,
                "primary_cc_p_value": 0.055
            },
            "results": [
                {"threshold": 0.01, "is_sensitive_to_threshold": False}
            ]
        }
        
        updated = analyze_threshold_sensitivity(report)
        
        assert updated["results"][0]["is_sensitive_to_threshold"] is True

    def test_flag_false_when_not_borderline(self):
        """Test flag is False when neither p-value is borderline."""
        report = {
            "summary": {
                "primary_pe_p_value": 0.01,
                "primary_cc_p_value": 0.005
            },
            "results": [
                {"threshold": 0.01, "is_sensitive_to_threshold": False}
            ]
        }
        
        updated = analyze_threshold_sensitivity(report)
        
        assert updated["results"][0]["is_sensitive_to_threshold"] is False

    def test_flag_false_when_none(self):
        """Test flag is False when p-values are None."""
        report = {
            "summary": {
                "primary_pe_p_value": None,
                "primary_cc_p_value": None
            },
            "results": [
                {"threshold": 0.01, "is_sensitive_to_threshold": False}
            ]
        }
        
        updated = analyze_threshold_sensitivity(report)
        
        assert updated["results"][0]["is_sensitive_to_threshold"] is False

    def test_multiple_results_updated(self):
        """Test that all results in the list are updated."""
        report = {
            "summary": {
                "primary_pe_p_value": 0.05,
                "primary_cc_p_value": 0.05
            },
            "results": [
                {"threshold": 0.01, "is_sensitive_to_threshold": False},
                {"threshold": 0.04, "is_sensitive_to_threshold": False},
                {"threshold": 0.05, "is_sensitive_to_threshold": False},
                {"threshold": 0.06, "is_sensitive_to_threshold": False},
                {"threshold": 0.10, "is_sensitive_to_threshold": False}
            ]
        }
        
        updated = analyze_threshold_sensitivity(report)
        
        for result in updated["results"]:
            assert result["is_sensitive_to_threshold"] is True
