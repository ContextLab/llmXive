import pytest
import numpy as np
from pathlib import Path
import json
import tempfile
import os

from code.analysis.baseline import (
    NonChaoticSystemError,
    BaselineConvergenceError,
    BaselineResult,
    compute_asymptotic_baseline,
    validate_clean_system_baseline,
    save_baseline_result,
    load_baseline_result,
    validate_and_gate_for_baseline,
    check_non_chaotic_regime
)
from code.config import get_full_config, set_simulation_seed


class TestNonChaoticDetection:
    """Tests for T026: Non-chaotic regime detection."""

    def test_check_non_chaotic_regime_positive_lambda(self):
        """Should not raise when lambda_max > 0."""
        # This should pass without raising
        check_non_chaotic_regime(lambda_max=0.5, N=3)

    def test_check_non_chaotic_regime_zero_lambda(self):
        """Should raise NonChaoticSystemError when lambda_max == 0."""
        with pytest.raises(NonChaoticSystemError) as excinfo:
            check_non_chaotic_regime(lambda_max=0.0, N=3)
        assert "lambda_max=0.0 <= 0" in str(excinfo.value)

    def test_check_non_chaotic_regime_negative_lambda(self):
        """Should raise NonChaoticSystemError when lambda_max < 0."""
        with pytest.raises(NonChaoticSystemError) as excinfo:
            check_non_chaotic_regime(lambda_max=-0.1, N=3)
        assert "lambda_max=-0.1 <= 0" in str(excinfo.value)

    def test_validate_and_gate_for_baseline_non_chaotic(self):
        """validate_and_gate_for_baseline should raise for non-chaotic baselines."""
        # Create a mock baseline with non-positive lambda_max
        bad_result = BaselineResult(
            lambda_max=-0.05,
            error_estimate=0.01,
            configuration={"N": 3},
            status="converged"
        )
        
        with pytest.raises(NonChaoticSystemError) as excinfo:
            validate_and_gate_for_baseline({"N=3": bad_result})
        
        assert "Non-chaotic regime detected" in str(excinfo.value)
        assert "lambda_max=-0.05 <= 0" in str(excinfo.value)

    def test_validate_and_gate_for_baseline_all_positive(self):
        """validate_and_gate_for_baseline should pass when all lambda_max > 0."""
        good_result = BaselineResult(
            lambda_max=0.9,
            error_estimate=0.01,
            configuration={"N": 3},
            status="converged"
        )
        
        # Should not raise
        result = validate_and_gate_for_baseline({"N=3": good_result})
        assert result is True


class TestBaselineComputation:
    """Tests for baseline computation functionality."""

    def test_compute_asymptotic_baseline_returns_positive_lambda(self):
        """Baseline computation should return a positive lambda_max for chaotic Lorenz."""
        # Use a small N and T for testing speed
        result = compute_asymptotic_baseline(N=1, T_max=1000, seed=42)
        
        assert result.lambda_max > 0, f"Expected positive lambda_max, got {result.lambda_max}"
        assert result.error_estimate >= 0

    def test_validate_clean_system_baseline_positive(self):
        """Validation should pass for positive lambda_max."""
        result = BaselineResult(
            lambda_max=0.8,
            error_estimate=0.05,
            configuration={"N": 1},
            status="converged"
        )
        
        assert validate_clean_system_baseline(result) is True

    def test_validate_clean_system_baseline_negative(self):
        """Validation should fail for non-positive lambda_max."""
        result = BaselineResult(
            lambda_max=-0.1,
            error_estimate=0.05,
            configuration={"N": 1},
            status="converged"
        )
        
        with pytest.raises(BaselineConvergenceError):
            validate_clean_system_baseline(result)

    def test_save_and_load_baseline_result(self):
        """Test saving and loading baseline results."""
        original = BaselineResult(
            lambda_max=0.9,
            error_estimate=0.02,
            configuration={"N": 2, "D": 3, "T_max": 2000},
            convergence_history=[(500, 0.85), (1000, 0.88), (2000, 0.90)],
            status="converged"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_baseline.json"
            
            # Save
            save_baseline_result(original, path)
            assert path.exists()
            
            # Load
            loaded = load_baseline_result(path)
            
            # Verify
            assert loaded.lambda_max == original.lambda_max
            assert loaded.error_estimate == original.error_estimate
            assert loaded.configuration == original.configuration
            assert loaded.convergence_history == original.convergence_history
            assert loaded.status == original.status


class TestIntegration:
    """Integration tests for the baseline module."""

    def test_full_baseline_workflow(self):
        """Test the complete workflow: compute -> validate -> save -> load -> gate."""
        # Set a fixed seed for reproducibility
        set_simulation_seed(42)
        
        # Compute baseline
        result = compute_asymptotic_baseline(N=1, T_max=2000, seed=42)
        
        # Validate
        validate_clean_system_baseline(result)
        
        # Check non-chaotic (should pass for Lorenz)
        check_non_chaotic_regime(result.lambda_max, 1)
        
        # Save and load
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "baseline_1.json"
            save_baseline_result(result, path)
            
            loaded = load_baseline_result(path)
            assert loaded.lambda_max == result.lambda_max
            
            # Gate validation
            validate_and_gate_for_baseline({"N=1": loaded})

    def test_gate_fails_on_non_chaotic(self):
        """Gate should fail if any baseline is non-chaotic."""
        good = BaselineResult(lambda_max=0.9, error_estimate=0.01, configuration={"N": 1})
        bad = BaselineResult(lambda_max=-0.1, error_estimate=0.01, configuration={"N": 2})
        
        with pytest.raises(NonChaoticSystemError):
            validate_and_gate_for_baseline({"N=1": good, "N=2": bad})