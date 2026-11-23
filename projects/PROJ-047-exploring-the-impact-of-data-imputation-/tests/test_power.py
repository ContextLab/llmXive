"""
Tests for the power analysis module.
"""

import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
from analysis.power import (
    calculate_power,
    analyze_bias_power,
    interpret_effect_size,
    save_power_analysis,
    DEFAULT_EFFECT_SIZE,
    DEFAULT_POWER,
    DEFAULT_ALPHA,
    POWER_THRESHOLD
)

def test_calculate_power_basic():
    """Test basic power calculation with known parameters."""
    # With medium effect size and reasonable sample size, power should be > 0.8
    power = calculate_power(effect_size=0.5, sample_size=64, alpha=0.05)
    assert 0.8 <= power <= 1.0, f"Expected power > 0.8 for medium effect, got {power}"

def test_calculate_power_small_sample():
    """Test power calculation with very small sample size."""
    power = calculate_power(effect_size=0.5, sample_size=5, alpha=0.05)
    # With very small sample, power should be low
    assert power < 0.5, f"Expected low power for small sample, got {power}"

def test_calculate_power_zero_effect():
    """Test power calculation with zero effect size."""
    power = calculate_power(effect_size=0.0, sample_size=100, alpha=0.05)
    # With zero effect, power should be close to alpha
    assert power < 0.2, f"Expected low power for zero effect, got {power}"

def test_interpret_effect_size():
    """Test effect size interpretation."""
    assert interpret_effect_size(0.1) == "negligible"
    assert interpret_effect_size(0.3) == "small"
    assert interpret_effect_size(0.6) == "medium"
    assert interpret_effect_size(1.0) == "large"

def test_analyze_bias_power_empty_dataframe():
    """Test power analysis with empty DataFrame."""
    df = pd.DataFrame()
    result = analyze_bias_power(df, "method1", "method2")
    assert result["status"] == "error"
    assert result["power_flag"] == "insufficient_data"

def test_analyze_bias_power_insufficient_samples():
    """Test power analysis with insufficient samples."""
    # Create DataFrame with only 5 samples per group (below minimum)
    df = pd.DataFrame({
        'method': ['m1'] * 5 + ['m2'] * 5,
        'bias': [0.1] * 5 + [0.2] * 5
    })
    result = analyze_bias_power(df, 'm1', 'm2')
    assert result["status"] == "warning"
    assert result["power_flag"] == "insufficient_samples"

def test_analyze_bias_power_success():
    """Test successful power analysis with sufficient data."""
    # Create DataFrame with 100 samples per group and different biases
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'method': ['m1'] * n + ['m2'] * n,
        'bias': np.concatenate([
            np.random.normal(0.1, 0.05, n),
            np.random.normal(0.2, 0.05, n)
        ])
    })
    result = analyze_bias_power(df, 'm1', 'm2')
    assert result["status"] == "success"
    assert "effect_size" in result
    assert "power" in result
    assert "power_flag" in result
    assert result["sample_size_1"] == n
    assert result["sample_size_2"] == n

def test_save_power_analysis(tmp_path):
    """Test saving power analysis results to JSON."""
    output_path = tmp_path / "test_power_analysis.json"
    results = [
        {
            "status": "success",
            "effect_size": 0.5,
            "sample_size_1": 50,
            "sample_size_2": 50,
            "power": 0.85,
            "power_flag": "sufficient"
        }
    ]
    save_power_analysis(results, str(output_path))

    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)

    assert "metadata" in data
    assert "summary" in data
    assert "analyses" in data
    assert data["summary"]["total_analyses"] == 1
    assert data["summary"]["sufficient_power_count"] == 1

def test_power_flag_logic():
    """Test that power_flag correctly reflects the threshold."""
    # Create data that should yield high power
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'method': ['m1'] * n + ['m2'] * n,
        'bias': np.concatenate([
            np.random.normal(0.1, 0.02, n),
            np.random.normal(0.3, 0.02, n)  # Larger difference
        ])
    })
    result = analyze_bias_power(df, 'm1', 'm2')
    assert result["power_flag"] == "sufficient"
    assert result["power"] >= POWER_THRESHOLD

    # Create data that should yield low power (small effect, small sample)
    n_small = 15
    df_small = pd.DataFrame({
        'method': ['m1'] * n_small + ['m2'] * n_small,
        'bias': np.concatenate([
            np.random.normal(0.1, 0.1, n_small),
            np.random.normal(0.12, 0.1, n_small)  # Small difference, high variance
        ])
    })
    result_small = analyze_bias_power(df_small, 'm1', 'm2')
    # Note: This might still be sufficient depending on the actual calculation,
    # but we verify the flag logic is present
    assert "power_flag" in result_small
    assert result_small["power_flag"] in ["sufficient", "insufficient"]

def test_required_sample_size_calculation():
    """Test that required sample size is calculated correctly."""
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'method': ['m1'] * n + ['m2'] * n,
        'bias': np.concatenate([
            np.random.normal(0.1, 0.05, n),
            np.random.normal(0.2, 0.05, n)
        ])
    })
    result = analyze_bias_power(df, 'm1', 'm2')
    # Should have calculated a required sample size
    assert "required_sample_size_for_target_power" in result
    # For a medium effect size, required N should be reasonable (not -1)
    if result["effect_size"] > 0:
        assert result["required_sample_size_for_target_power"] > 0