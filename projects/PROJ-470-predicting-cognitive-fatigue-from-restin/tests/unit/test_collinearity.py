"""Unit tests for collinearity diagnostics (T024)."""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))

from collinearity import (
    calculate_vif,
    run_collinearity_diagnostics,
    save_collinearity_report,
    load_analysis_results,
)


def test_calculate_vif_basic():
    """Test basic VIF calculation with known data."""
    # Create synthetic data with known relationships
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.9 + np.random.normal(0, 0.1, n)  # High correlation
    y = x1 + x2 + np.random.normal(0, 0.1, n)

    df = pd.DataFrame({"y": y, "x1": x1, "x2": x2})

    vif_results = calculate_vif(df, ["x1", "x2"])

    assert "x1" in vif_results
    assert "x2" in vif_results
    # With high correlation, VIF should be > 1
    assert vif_results["x1"] > 1.0
    assert vif_results["x2"] > 1.0


def test_calculate_vif_perfect_collinearity():
    """Test VIF with perfect collinearity (should be very high or inf)."""
    np.random.seed(42)
    n = 50
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 2.0  # Perfect linear relationship

    df = pd.DataFrame({"y": x1 + x2, "x1": x1, "x2": x2})

    vif_results = calculate_vif(df, ["x1", "x2"])

    # VIF should be very large (or inf) for perfect collinearity
    assert vif_results["x1"] > 100 or np.isinf(vif_results["x1"])
    assert vif_results["x2"] > 100 or np.isinf(vif_results["x2"])


def test_save_collinearity_report():
    """Test that report file is created with correct content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "vif_test.log")
        vif_results = {"fatigue_delta": 2.5, "pre_complexity": 1.8}
        passed = True

        save_collinearity_report(vif_results, passed, output_path)

        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            content = f.read()

        assert "Collinearity Diagnostics" in content
        assert "PASSED" in content
        assert "fatigue_delta" in content
        assert "pre_complexity" in content


def test_save_collinearity_report_failed():
    """Test report generation when VIF check fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "vif_fail.log")
        vif_results = {"fatigue_delta": 6.5, "pre_complexity": 1.8}
        passed = False

        save_collinearity_report(vif_results, passed, output_path)

        with open(output_path, "r") as f:
            content = f.read()

        assert "FAILED" in content
        assert "WARNING" in content
        assert "CRITICAL" in content


def test_vif_threshold_check():
    """Test that VIF >= 5.0 triggers failure."""
    # Create data with high collinearity
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.95 + np.random.normal(0, 0.05, n)  # Very high correlation

    df = pd.DataFrame({"fatigue_delta": x1, "pre_complexity": x2})

    vif_results, passed = calculate_vif(df, ["fatigue_delta", "pre_complexity"]), True
    # Manually check threshold
    for v in vif_results.values():
        if v >= 5.0:
            passed = False
            break

    # With 0.95 correlation, VIF should be > 5
    assert not passed or any(v >= 5.0 for v in vif_results.values())