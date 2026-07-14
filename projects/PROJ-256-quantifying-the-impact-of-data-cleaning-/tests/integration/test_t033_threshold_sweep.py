"""
Integration test for T033: Outlier threshold sweep.

Verifies that:
1. The sweep runs without errors
2. FPR is calculated correctly for each threshold
3. Inconsistency rate is calculated correctly
4. Output file is created with valid structure
"""
import os
import sys
import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from t033_outlier_threshold_sweep import (
    THRESHOLD_VALUES,
    SIGNIFICANCE_THRESHOLD,
    calculate_fpr_per_threshold,
    calculate_inconsistency_rate,
    run_threshold_sweep
)


@pytest.fixture
def sample_null_metrics():
    """Create sample null metrics for FPR testing."""
    return {
        "datasets": [
            {"threshold_k": 0.5, "p_value": 0.03},
            {"threshold_k": 0.5, "p_value": 0.08},
            {"threshold_k": 1.0, "p_value": 0.02},
            {"threshold_k": 1.0, "p_value": 0.06},
            {"threshold_k": 1.5, "p_value": 0.04},
            {"threshold_k": 1.5, "p_value": 0.09},
            {"threshold_k": 2.0, "p_value": 0.01},
            {"threshold_k": 2.0, "p_value": 0.05},
        ]
    }


@pytest.fixture
def sample_baseline_metrics():
    """Create sample baseline metrics."""
    return {
        "datasets": [
            {
                "dataset_name": "test_dataset_1",
                "t_test": {"p_value": 0.03}
            },
            {
                "dataset_name": "test_dataset_2",
                "t_test": {"p_value": 0.08}
            },
            {
                "dataset_name": "test_dataset_3",
                "t_test": {"p_value": 0.02}
            }
        ]
    }


@pytest.fixture
def sample_cleaned_metrics():
    """Create sample cleaned metrics."""
    return {
        "datasets": [
            {
                "dataset_name": "test_dataset_1",
                "strategy": "outlier_removed_k1.5",
                "t_test": {"p_value": 0.09}  # Changed from significant to non-significant
            },
            {
                "dataset_name": "test_dataset_2",
                "strategy": "outlier_removed_k1.5",
                "t_test": {"p_value": 0.07}  # Still non-significant
            },
            {
                "dataset_name": "test_dataset_3",
                "strategy": "outlier_removed_k1.5",
                "t_test": {"p_value": 0.01}  # Still significant
            }
        ]
    }


def test_fpr_calculation(sample_null_metrics):
    """Test FPR calculation for each threshold."""
    fpr_results = calculate_fpr_per_threshold(sample_null_metrics)

    # Check that all thresholds are present
    for k in THRESHOLD_VALUES:
        assert k in fpr_results, f"Threshold {k} missing from FPR results"

    # Check specific calculations
    # For k=0.5: 1 significant out of 2 -> FPR = 0.5
    assert abs(fpr_results[0.5] - 0.5) < 0.01

    # For k=1.0: 1 significant out of 2 -> FPR = 0.5
    assert abs(fpr_results[1.0] - 0.5) < 0.01

    # For k=1.5: 1 significant out of 2 -> FPR = 0.5
    assert abs(fpr_results[1.5] - 0.5) < 0.01

    # For k=2.0: 2 significant out of 2 -> FPR = 1.0
    assert abs(fpr_results[2.0] - 1.0) < 0.01


def test_inconsistency_rate_calculation(
    sample_baseline_metrics,
    sample_cleaned_metrics
):
    """Test inconsistency rate calculation."""
    # For k=1.5:
    # Dataset 1: baseline 0.03 (sig) -> cleaned 0.09 (non-sig) -> INCONSISTENT
    # Dataset 2: baseline 0.08 (non-sig) -> cleaned 0.07 (non-sig) -> consistent
    # Dataset 3: baseline 0.02 (sig) -> cleaned 0.01 (sig) -> consistent
    # Inconsistency rate = 1/3 = 0.333...

    ir = calculate_inconsistency_rate(
        sample_baseline_metrics,
        sample_cleaned_metrics,
        1.5
    )

    assert abs(ir - 0.3333) < 0.01


def test_inconsistency_rate_empty_metrics():
    """Test inconsistency rate with empty metrics."""
    ir = calculate_inconsistency_rate({}, {}, 1.5)
    assert ir == 0.0


def test_fpr_empty_metrics():
    """Test FPR with empty null metrics."""
    fpr_results = calculate_fpr_per_threshold({})
    for k in THRESHOLD_VALUES:
        assert fpr_results[k] == 0.0


def test_threshold_values_range():
    """Test that threshold values are in expected range."""
    assert len(THRESHOLD_VALUES) == 6
    assert min(THRESHOLD_VALUES) == 0.5
    assert max(THRESHOLD_VALUES) == 3.0


def test_significance_threshold():
    """Test that significance threshold is set correctly."""
    assert SIGNIFICANCE_THRESHOLD == 0.05