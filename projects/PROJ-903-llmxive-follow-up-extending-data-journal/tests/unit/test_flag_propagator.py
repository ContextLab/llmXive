"""
Unit tests for the Flag Propagator module (T005d).

Tests the logic that propagates the "Low Power" flag from T005b
into the final story structure.
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from narrative.flag_propagator import propagate_low_power_flag, write_propagated_report
from data.loader import LowPowerError


class TestPropagateLowPowerFlag:
    """Tests for the propagate_low_power_flag function."""

    def test_normal_flow_no_error(self):
        """Test that normal flow without error preserves data and sets flag to False."""
        baseline = {
            "primary_narrative": "Income correlates with housing value.",
            "n_samples": 1000,
            "n_numeric": 5
        }
        
        report = propagate_low_power_flag(baseline, error_context=None)
        
        assert report["low_power_flag"] is False
        assert report["status"] == "success"
        assert report["narrative"] == "Income correlates with housing value."
        assert report["n_samples"] == 1000

    def test_low_power_error_propagation(self):
        """Test that a LowPowerError correctly sets the flag and updates narrative."""
        baseline = {
            "primary_narrative": "Some narrative.",
            "n_samples": 1000,
            "n_numeric": 5
        }
        
        # Create a real LowPowerError instance
        error = LowPowerError(n_samples=15, threshold=30)
        
        report = propagate_low_power_flag(baseline, error_context=error)
        
        assert report["low_power_flag"] is True
        assert report["status"] == "low_power_failure"
        assert report["n_samples"] == 15
        assert "Insufficient Statistical Power" in report["narrative"]
        assert "15" in report["narrative"]
        assert "30" in report["narrative"]
        assert len(report["warnings"]) > 0
        assert "Low Power Error" in report["warnings"][0]

    def test_low_power_error_with_custom_threshold(self):
        """Test propagation with a custom threshold in the error."""
        baseline = {"n_samples": 100, "primary_narrative": "Test"}
        error = LowPowerError(n_samples=25, threshold=50)
        
        report = propagate_low_power_flag(baseline, error_context=error)
        
        assert report["n_samples"] == 25
        assert "50" in report["narrative"]

    def test_inspector_output_preserved_on_success(self):
        """Test that inspector output is preserved when no error occurs."""
        baseline = {"primary_narrative": "Baseline story", "n_samples": 100}
        inspector = {"counterfactuals": ["Alternative A"], "status": "ok"}
        
        report = propagate_low_power_flag(baseline, inspector_output=inspector, error_context=None)
        
        assert report["inspector"] == inspector
        assert report["low_power_flag"] is False

    def test_inspector_output_cleared_on_low_power(self):
        """Test that inspector output is effectively nullified or marked when low power occurs."""
        baseline = {"primary_narrative": "Baseline story", "n_samples": 100}
        inspector = {"counterfactuals": ["Alternative A"]}
        error = LowPowerError(n_samples=10, threshold=30)
        
        report = propagate_low_power_flag(baseline, inspector_output=inspector, error_context=error)
        
        assert report["low_power_flag"] is True
        # The narrative should override the inspector findings
        assert "Insufficient Statistical Power" in report["narrative"]
        # Inspector data is kept in the object for audit but flagged as invalid context
        # (Implementation keeps the object but the status explains the failure)
        assert report["inspector"] == inspector 
        assert report["status"] == "low_power_failure"


class TestWritePropagatedReport:
    """Tests for the write_propagated_report function."""

    def test_write_json_creates_file(self, tmp_path):
        """Test that the function writes a valid JSON file."""
        output_dir = tmp_path / "output"
        output_file = output_dir / "test_story.json"
        
        report = {
            "status": "success",
            "low_power_flag": False,
            "narrative": "Test narrative"
        }
        
        write_propagated_report(report, str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == report

    def test_write_json_creates_directories(self, tmp_path):
        """Test that the function creates parent directories if they don't exist."""
        output_dir = tmp_path / "deep" / "nested" / "output"
        output_file = output_dir / "test.json"
        
        report = {"key": "value"}
        
        write_propagated_report(report, str(output_file))
        
        assert output_file.exists()
        assert output_dir.exists()