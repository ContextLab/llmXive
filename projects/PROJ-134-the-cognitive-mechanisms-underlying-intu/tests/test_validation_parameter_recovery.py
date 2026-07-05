"""
Unit tests for Parameter Recovery validation logic in code/analysis/validation.py.

These tests verify that the validation module correctly identifies whether
the ground_truth_effect falls within the 95% credible interval.
"""
import pytest
import numpy as np
import pandas as pd
import arviz as az
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add code to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.validation import check_parameter_recovery, run_validation_pipeline


class MockInferenceData:
    """Mock Arviz InferenceData for testing without full PyMC run."""
    def __init__(self, samples: np.ndarray, param_name: str = "salience_effect"):
        self.posterior = MagicMock()
        self.posterior.data_vars = {param_name: MagicMock()}
        # Create a DataArray-like structure
        dims = ("chain", "draw")
        shape = (4, 1000)  # 4 chains, 1000 draws
        
        # Reshape samples to match expected dimensions if needed
        if samples.shape != shape:
            # Pad or truncate to match
            flat = samples.flatten()
            if len(flat) < shape[0] * shape[1]:
                # Pad with mean
                pad_len = shape[0] * shape[1] - len(flat)
                flat = np.concatenate([flat, np.full(pad_len, np.mean(flat))])
            else:
                flat = flat[:shape[0] * shape[1]]
            samples = flat.reshape(shape)
        
        # Create a mock DataArray
        mock_da = MagicMock()
        mock_da.values = samples
        self.posterior.__getitem__ = MagicMock(return_value=mock_da)


class TestParameterRecovery:
    """Tests for the check_parameter_recovery function."""

    def test_recovery_pass_when_gt_in_ci(self):
        """Test that recovery passes when ground truth is within CI."""
        # Generate samples centered around 0.5 with small std
        np.random.seed(42)
        samples = np.random.normal(loc=0.5, scale=0.1, size=4000)
        
        idata = MockInferenceData(samples)
        passed, details = check_parameter_recovery(
            idata, 
            param_name="salience_effect", 
            ground_truth=0.5
        )
        
        assert passed is True
        assert details["ground_truth"] == 0.5
        assert details["ci_lower"] <= 0.5 <= details["ci_upper"]
        assert details["passed"] is True

    def test_recovery_fail_when_gt_outside_ci(self):
        """Test that recovery fails when ground truth is outside CI."""
        # Generate samples centered around 0.5
        np.random.seed(42)
        samples = np.random.normal(loc=0.5, scale=0.1, size=4000)
        
        idata = MockInferenceData(samples)
        # Ground truth is far away (1.0)
        passed, details = check_parameter_recovery(
            idata, 
            param_name="salience_effect", 
            ground_truth=1.0
        )
        
        assert passed is False
        assert details["ci_upper"] < 1.0
        assert details["passed"] is False

    def test_missing_param_raises_error(self):
        """Test that missing parameter name returns error."""
        np.random.seed(42)
        samples = np.random.normal(loc=0.5, scale=0.1, size=4000)
        idata = MockInferenceData(samples, param_name="other_param")
        
        passed, details = check_parameter_recovery(
            idata, 
            param_name="salience_effect", 
            ground_truth=0.5
        )
        
        assert passed is False
        assert "error" in details
        assert details["error"] == "extraction_failed"

    def test_missing_ground_truth_returns_warning(self):
        """Test that missing ground truth returns False and warning."""
        np.random.seed(42)
        samples = np.random.normal(loc=0.5, scale=0.1, size=4000)
        idata = MockInferenceData(samples)
        
        passed, details = check_parameter_recovery(
            idata, 
            param_name="salience_effect", 
            ground_truth=None
        )
        
        assert passed is False
        assert details["error"] == "ground_truth_missing"

    def test_custom_credible_interval(self):
        """Test calculation with custom credible interval (e.g., 0.90)."""
        np.random.seed(42)
        samples = np.random.normal(loc=0.5, scale=0.1, size=4000)
        idata = MockInferenceData(samples)
        
        passed, details = check_parameter_recovery(
            idata, 
            param_name="salience_effect", 
            ground_truth=0.5,
            credible_interval=0.90
        )
        
        assert passed is True
        # 90% CI should be narrower than 95%
        assert details["credible_interval"] == 0.90