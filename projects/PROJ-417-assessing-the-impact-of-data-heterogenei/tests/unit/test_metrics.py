import pytest
import math
from typing import List, Dict, Any
from pathlib import Path
import sys

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.metrics import (
    calculate_bias,
    calculate_coverage,
    compute_metrics_from_simulation,
    MetricsResult
)

def test_calculate_bias_zero():
    """Verify that a pooled estimate exactly equal to the true effect results in zero bias."""
    assert calculate_bias(0.5, 0.5) == 0.0
    assert calculate_bias(-1.2, -1.2) == 0.0

def test_calculate_bias_positive_negative():
    """Verify bias calculation direction."""
    assert calculate_bias(0.6, 0.5) == pytest.approx(0.1)
    assert calculate_bias(0.4, 0.5) == pytest.approx(-0.1)

def test_calculate_coverage_true():
    """Verify that true effect within CI results in a coverage flag of True."""
    # True effect in middle
    assert calculate_coverage(0.4, 0.6, 0.5) is True
    # True effect on lower boundary
    assert calculate_coverage(0.5, 0.6, 0.5) is True
    # True effect on upper boundary
    assert calculate_coverage(0.4, 0.5, 0.5) is True

def test_calculate_coverage_false():
    """Verify that true effect outside CI results in a coverage flag of False."""
    # Below lower
    assert calculate_coverage(0.6, 0.7, 0.5) is False
    # Above upper
    assert calculate_coverage(0.4, 0.45, 0.5) is False

def test_compute_metrics_from_simulation_success():
    """Verify computation from simulation records using injected_true_effect."""
    records = [
        {
            "injected_true_effect": 0.5,
            "pooled_effect": 0.5,
            "ci_lower": 0.4,
            "ci_upper": 0.6,
            "replicate_id": 1
        },
        {
            "injected_true_effect": 0.5,
            "pooled_effect": 0.7,
            "ci_lower": 0.6,
            "ci_upper": 0.8,
            "replicate_id": 2
        }
    ]
    results = compute_metrics_from_simulation(records)
    
    assert len(results) == 2
    # Rep 1: Zero bias, coverage True
    assert results[0].bias == 0.0
    assert results[0].coverage_flag is True
    # Rep 2: Bias 0.2, coverage False
    assert results[1].bias == pytest.approx(0.2)
    assert results[1].coverage_flag is False

def test_compute_metrics_strict_column_check():
    """Verify that the logic strictly requires 'injected_true_effect' (FR-003)."""
    # Record has 'true_effect' but not 'injected_true_effect'
    records = [{
        "true_effect": 0.5,
        "pooled_effect": 0.5,
        "ci_lower": 0.4,
        "ci_upper": 0.6
    }]
    with pytest.raises(KeyError) as excinfo:
        compute_metrics_from_simulation(records)
    assert "injected_true_effect" in str(excinfo.value)

def test_compute_metrics_non_finite_values():
    """Verify that non-finite values raise ValueError."""
    records = [{
        "injected_true_effect": float('nan'),
        "pooled_effect": 0.5,
        "ci_lower": 0.4,
        "ci_upper": 0.6
        }]
    with pytest.raises(ValueError):
        compute_metrics_from_simulation(records)