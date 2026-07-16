"""
Unit tests for the stratification logic in metrics.py.
"""
import pytest
import numpy as np
from metrics import stratify_by_phi


def test_stratify_by_phi_empty_results():
    """Test that stratify_by_phi handles empty results list."""
    result = stratify_by_phi([])
    assert result["bins"] == []
    assert result["summary"] == []


def test_stratify_by_phi_single_bin():
    """Test stratification with a single bin."""
    results = [
        {"phi": 0.05, "ordered_cov": 0.80, "shuffled_cov": 0.94, "diff": 0.14, "p_value": 0.01, "ci_width_ratio": 1.1},
        {"phi": 0.08, "ordered_cov": 0.82, "shuffled_cov": 0.95, "diff": 0.13, "p_value": 0.02, "ci_width_ratio": 1.05}
    ]
    bins = [0.0, 0.1, 0.2]
    result = stratify_by_phi(results, bins)

    assert len(result["summary"]) == 2
    assert result["summary"][0]["count"] == 2
    assert abs(result["summary"][0]["avg_ordered_cov"] - 0.81) < 0.01
    assert abs(result["summary"][0]["avg_shuffled_cov"] - 0.945) < 0.01


def test_stratify_by_phi_multiple_bins():
    """Test stratification across multiple bins."""
    results = [
        {"phi": 0.05, "ordered_cov": 0.90, "shuffled_cov": 0.95, "diff": 0.05, "p_value": 0.5, "ci_width_ratio": 1.0},
        {"phi": 0.55, "ordered_cov": 0.60, "shuffled_cov": 0.95, "diff": 0.35, "p_value": 0.001, "ci_width_ratio": 1.5},
        {"phi": 0.85, "ordered_cov": 0.40, "shuffled_cov": 0.95, "diff": 0.55, "p_value": 0.0001, "ci_width_ratio": 2.0}
    ]
    bins = [0.0, 0.5, 1.0]
    result = stratify_by_phi(results, bins)

    assert len(result["summary"]) == 2
    # Bin 0.0-0.5
    assert result["summary"][0]["count"] == 1
    assert abs(result["summary"][0]["avg_ordered_cov"] - 0.90) < 0.01
    # Bin 0.5-1.0
    assert result["summary"][1]["count"] == 2
    assert abs(result["summary"][1]["avg_ordered_cov"] - 0.50) < 0.01


def test_stratify_by_phi_missing_keys():
    """Test that missing keys in results are handled gracefully."""
    results = [
        {"phi": 0.05},  # Missing cov, diff, etc.
        {"phi": 0.05, "ordered_cov": 0.90}
    ]
    bins = [0.0, 0.1]
    result = stratify_by_phi(results, bins)

    assert result["summary"][0]["count"] == 2
    # Should handle None values in averages
    assert result["summary"][0]["avg_ordered_cov"] is not None
    assert result["summary"][0]["avg_shuffled_cov"] is None
    assert result["summary"][0]["avg_diff"] is None
    assert result["summary"][0]["avg_p_value"] is None
    assert result["summary"][0]["avg_ci_width_ratio"] is None
