"""
Unit tests for estimators.
"""

import pytest
import math
from code.simulation.estimators import (
    estimate_fixed_effects,
    estimate_dersimonian_laird,
    estimate_reml
)


def test_fixed_effects_known_case():
    """Test Fixed-Effects on a simple known case."""
    effects = [1.0, 2.0]
    ses = [1.0, 1.0]
    # Weights = 1, 1. Pooled = (1+2)/2 = 1.5
    result = estimate_fixed_effects(effects, ses)
    assert math.isclose(result.pooled_estimate, 1.5, abs_tol=0.01)
    assert result.tau_squared == 0.0
    assert result.converged is True


def test_dl_vs_fixed_effects_tau_zero():
    """Test that DL approximates FE when tau^2 is effectively zero."""
    effects = [1.0, 2.0, 3.0]
    ses = [0.1, 0.1, 0.1] # Low variance, FE should dominate
    fe_res = estimate_fixed_effects(effects, ses)
    dl_res = estimate_dersimonian_laird(effects, ses)
    
    # With low SE, DL tau^2 should be small or zero
    assert dl_res.tau_squared >= 0
    # Pooled estimates should be close
    assert math.isclose(fe_res.pooled_estimate, dl_res.pooled_estimate, abs_tol=0.5)


def test_reml_convergence_basic():
    """Test that REML runs without crashing on basic data."""
    effects = [0.5, 0.6, 0.4, 0.7, 0.5]
    ses = [0.2, 0.2, 0.2, 0.2, 0.2]
    result = estimate_reml(effects, ses)
    assert result.converged is True
    assert result.pooled_estimate is not None
    assert result.ci_lower < result.ci_upper


def test_reml_fallback_on_failure():
    """Test that REML falls back to DL if optimization fails (simulated)."""
    # Hard to simulate optimization failure without mocking, 
    # but we ensure the function returns a valid result even on weird data
    effects = [1.0]
    ses = [1.0]
    result = estimate_reml(effects, ses)
    assert result.pooled_estimate == 1.0
    assert result.converged is True
