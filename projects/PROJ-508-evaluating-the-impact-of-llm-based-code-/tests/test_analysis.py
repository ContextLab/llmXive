"""
Tests for the statistical analysis module (code/analyze.py).
"""
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from analyze import (
    calculate_vif,
    flag_high_vif,
    apply_bonferroni_correction,
    run_sensitivity_analysis,
)


def test_vif_calculation():
    """Test Variance Inflation Factor calculation."""
    # Create a dataset with known correlation
    np.random.seed(42)
    df = pd.DataFrame({
        "y": np.random.rand(100),
        "x1": np.random.rand(100),
        "x2": np.random.rand(100),
    })
    # x3 is highly correlated with x1
    df["x3"] = df["x1"] * 0.99 + np.random.rand(100) * 0.1

    vif_values = calculate_vif(df, ["x1", "x2", "x3"])

    # x3 should have high VIF
    assert vif_values["x3"] > 5.0


def test_vif_flagging():
    """Test VIF flagging logic."""
    vif_data = {"x1": 2.0, "x2": 6.5, "x3": 1.2}
    flagged = flag_high_vif(vif_data, threshold=5.0)
    assert flagged == ["x2"]


def test_bonferroni_correction():
    """Test Bonferroni correction for p-values."""
    p_values = [0.01, 0.05, 0.10, 0.20]
    corrected = apply_bonferroni_correction(p_values)

    # Corrected values should be p * n, capped at 1.0
    n = len(p_values)
    expected = [min(p * n, 1.0) for p in p_values]

    for c, e in zip(corrected, expected):
        assert abs(c - e) < 1e-6


def test_sensitivity_analysis():
    """Test sensitivity analysis sweep logic."""
    # Mock dataset
    df = pd.DataFrame({
        "llm_adoption": np.random.choice([0, 1], 50),
        "iteration_count": np.random.randint(1, 10, 50),
        "control": np.random.rand(50),
    })

    # Run sweep over thresholds
    thresholds = [1, 2, 3]
    results = run_sensitivity_analysis(df, thresholds)

    assert len(results) == len(thresholds)
    assert all("effect_size" in r for r in results)
