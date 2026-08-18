import pytest
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config
from analysis.run_pilot_sensitivity import run_pilot_analysis

class TestPilotSensitivityAnalysis:
    """Tests for the pilot sensitivity analysis functionality."""

    def test_pilot_analysis_runs(self):
        """Test that the pilot analysis runs without errors."""
        results = run_pilot_analysis(num_test_matrices=10, num_pilot_steps=5, seed=42)
        
        assert len(results) > 0, "Pilot analysis should produce results"
        assert all(isinstance(r, dict) for r in results), "Each result should be a dict"
        
        for result in results:
            assert "epsilon" in result, "Result should contain epsilon"
            assert "delta_kl_per_step" in result, "Result should contain delta_kl_per_step"
            assert "status" in result, "Result should contain status"
            assert result["status"] in ["PASS", "WARN", "FAIL"], "Status should be valid"

    def test_pilot_analysis_output_schema(self):
        """Test that the output matches the expected schema."""
        results = run_pilot_analysis(num_test_matrices=5, num_pilot_steps=3, seed=42)
        
        for result in results:
            assert isinstance(result["epsilon"], (int, float)), "Epsilon should be numeric"
            assert isinstance(result["delta_kl_per_step"], (int, float)), "Delta KL should be numeric"
            assert isinstance(result["status"], str), "Status should be string"

    def test_pilot_analysis_bounds_check(self):
        """Test that the pilot analysis correctly identifies bounds violations."""
        config = get_config()
        results = run_pilot_analysis(num_test_matrices=5, num_pilot_steps=3, seed=42)
        
        for result in results:
            if result["delta_kl_per_step"] != result["delta_kl_per_step"]:  # NaN check
                continue
                
            bounds = config.EPSILON_PILOT_BOUNDS
            if bounds["min"] <= result["delta_kl_per_step"] <= bounds["max"]:
                # Should be PASS or WARN
                assert result["status"] in ["PASS", "WARN"], \
                    f"Result within bounds should be PASS or WARN, got {result['status']}"
            else:
                # Should be FAIL
                assert result["status"] == "FAIL", \
                    f"Result outside bounds should be FAIL, got {result['status']}"

    def test_pilot_analysis_deterministic(self):
        """Test that the pilot analysis is deterministic with the same seed."""
        results1 = run_pilot_analysis(num_test_matrices=5, num_pilot_steps=3, seed=42)
        results2 = run_pilot_analysis(num_test_matrices=5, num_pilot_steps=3, seed=42)
        
        assert len(results1) == len(results2), "Results should have the same length"
        
        for r1, r2 in zip(results1, results2):
            assert r1["epsilon"] == r2["epsilon"], "Epsilon values should match"
            assert r1["delta_kl_per_step"] == r2["delta_kl_per_step"], \
                "Delta KL values should match"
            assert r1["status"] == r2["status"], "Status should match"
