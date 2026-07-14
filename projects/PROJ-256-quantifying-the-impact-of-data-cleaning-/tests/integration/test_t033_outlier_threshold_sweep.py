"""
Integration tests for T033: Outlier Threshold Sweep
"""
import os
import json
import pytest
import pandas as pd
import numpy as np

# Import the module functions
from t033_outlier_threshold_sweep import (
    calculate_fpr_per_threshold,
    calculate_inconsistency_rate,
    run_threshold_sweep
)


@pytest.fixture
def sample_baseline_metrics():
    """Sample baseline metrics for testing."""
    return {
        "datasets": [
            {
                "dataset_name": "test_dataset_1",
                "t_test": {"p_value": 0.03},
                "analysis": {"t_test": {"p_value": 0.03}}
            },
            {
                "dataset_name": "test_dataset_2",
                "t_test": {"p_value": 0.07},
                "analysis": {"t_test": {"p_value": 0.07}}
            }
        ]
    }


@pytest.fixture
def sample_cleaned_metrics():
    """Sample cleaned metrics for testing."""
    return {
        "datasets": [
            {
                "dataset_name": "test_dataset_1",
                "cleaning_strategy": "outlier_removal_k=1.5",
                "t_test": {"p_value": 0.06}  # Changed significance
            },
            {
                "dataset_name": "test_dataset_2",
                "cleaning_strategy": "outlier_removal_k=1.5",
                "t_test": {"p_value": 0.08}  # No change in significance
            }
        ]
    }


@pytest.fixture
def sample_null_metrics():
    """Sample null metrics for FPR testing."""
    return {
        "datasets": [
            {"p_value": 0.02},  # Significant (false positive)
            {"p_value": 0.15},  # Not significant
            {"p_value": 0.01},  # Significant (false positive)
            {"p_value": 0.30},  # Not significant
            {"p_value": 0.04}   # Significant (false positive)
        ]
    }


def test_calculate_fpr_per_threshold(sample_null_metrics):
    """Test FPR calculation."""
    thresholds = [1.5]
    fpr_results = calculate_fpr_per_threshold(sample_null_metrics, thresholds)

    # 3 out of 5 are <= 0.05, so FPR should be 0.6
    assert 1.5 in fpr_results
    assert abs(fpr_results[1.5] - 0.6) < 0.01


def test_calculate_inconsistency_rate(sample_baseline_metrics, sample_cleaned_metrics):
    """Test inconsistency rate calculation."""
    thresholds = [1.5]
    inconsistency_results = calculate_inconsistency_rate(
        sample_baseline_metrics, sample_cleaned_metrics, thresholds
    )

    # Dataset 1: baseline sig (0.03), cleaned not sig (0.06) -> inconsistent
    # Dataset 2: baseline not sig (0.07), cleaned not sig (0.08) -> consistent
    # Inconsistency rate = 1/2 = 0.5
    assert 1.5 in inconsistency_results
    assert abs(inconsistency_results[1.5] - 0.5) < 0.01


def test_calculate_fpr_empty_null_metrics():
    """Test FPR with empty null metrics."""
    thresholds = [1.5]
    fpr_results = calculate_fpr_per_threshold({"datasets": []}, thresholds)
    assert fpr_results[1.5] == 0.0


def test_calculate_inconsistency_empty_metrics():
    """Test inconsistency rate with empty metrics."""
    thresholds = [1.5]
    inconsistency_results = calculate_inconsistency_rate(
        {"datasets": []}, {"datasets": []}, thresholds
    )
    assert inconsistency_results[1.5] == 0.0


def test_run_threshold_sweep_missing_files(tmp_path, caplog):
    """Test run_threshold_sweep with missing files."""
    # Create temporary paths
    baseline_file = os.path.join(tmp_path, "baseline.json")
    cleaned_file = os.path.join(tmp_path, "cleaned.json")
    null_file = os.path.join(tmp_path, "null.json")
    output_file = os.path.join(tmp_path, "output.json")

    # Don't create the files, so they're missing
    result = run_threshold_sweep(
        baseline_file=baseline_file,
        cleaned_file=cleaned_file,
        null_file=null_file,
        output_file=output_file
    )

    # Should return an error
    assert "error" in result
    assert "Baseline metrics file not found" in result["error"]