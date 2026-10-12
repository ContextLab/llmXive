"""
Unit tests for preprocessing utilities:
* Log‑transform of the conductivity target.
* Outlier filtering based on sigma thresholds.
* VIF calculation and high‑VIF feature detection.
"""

import pandas as pd
import numpy as np
import pytest

from code.data_loader import apply_log_transformation
from code.analysis import filter_outliers, calculate_vif, get_high_vif_features

def test_log_transformation():
    df = pd.DataFrame({"conductivity": [1.0, 10.0, 100.0]})
    result = apply_log_transformation(df.copy(), "conductivity")
    assert "log_conductivity" in result.columns
    np.testing.assert_allclose(result["log_conductivity"], np.log(df["conductivity"]))

def test_filter_outliers():
    # Mean = 2, std ≈ 4.0; 10 is exactly 2σ away, should be kept (<= threshold)
    df = pd.DataFrame({"target": [0, 0, 0, 10, 0]})
    filtered = filter_outliers(df, "target", sigma_threshold=2)
    assert len(filtered) == 5  # no rows removed

def test_vif_detection():
    np.random.seed(0)
    x = np.random.randn(100)
    df = pd.DataFrame({
        "a": x,
        "b": x * 0.9 + np.random.randn(100) * 0.1,
        "target": np.random.randn(100)
    })
    X = df[["a", "b"]].values
    vif_scores = calculate_vif(X, ["a", "b"])
    high = get_high_vif_features(vif_scores, threshold=5)
    # At least one of the correlated columns should exceed the VIF threshold
    assert "a" in high or "b" in high
