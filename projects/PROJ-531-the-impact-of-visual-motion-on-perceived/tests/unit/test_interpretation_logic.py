"""
Unit tests for T031: Interpretation Logic.
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from interpretation_logic import (
    analyze_ols_results,
    analyze_rf_results,
    generate_interpretation
)

def test_analyze_ols_results_significant_positive():
    """Test OLS analysis with a significant positive coefficient."""
    ols_data = {
        "coefficients": {"latency": -0.45, "smoothness": 0.32, "lead_time": 0.10},
        "p_values": {"latency": 0.001, "smoothness": 0.02, "lead_time": 0.45},
        "feature_names": ["latency", "smoothness", "lead_time"]
    }
    
    results = analyze_ols_results(ols_data)
    
    assert len(results) > 0
    assert any("latency" in r and "significant" in r and "negative" in r for r in results)
    assert any("smoothness" in r and "significant" in r and "positive" in r for r in results)
    assert any("lead_time" in r and "not show" in r or "null" in r.lower() for r in results)

def test_analyze_ols_results_all_null():
    """Test OLS analysis when no features are significant."""
    ols_data = {
        "coefficients": {"latency": 0.05, "smoothness": -0.02, "lead_time": 0.01},
        "p_values": {"latency": 0.8, "smoothness": 0.9, "lead_time": 0.95},
        "feature_names": ["latency", "smoothness", "lead_time"]
    }
    
    results = analyze_ols_results(ols_data)
    
    assert len(results) > 0
    # Check for the specific null result message
    assert any("No motion features showed a statistically significant association" in r for r in results)

def test_analyze_rf_results():
    """Test Random Forest analysis."""
    importance = {"latency": 0.6, "smoothness": 0.3, "lead_time": 0.1}
    metrics = {"r2": 0.75, "rmse": 0.15}
    
    results = analyze_rf_results(importance, metrics)
    
    assert len(results) > 0
    assert any("75.0%" in r for r in results)
    assert any("latency" in r and "most influential" in r for r in results)

def test_generate_interpretation_full():
    """Test full interpretation generation with mock data."""
    mock_metrics = {
        "ols_results": {
            "coefficients": {"latency": -0.5, "smoothness": 0.4},
            "p_values": {"latency": 0.01, "smoothness": 0.03},
            "feature_names": ["latency", "smoothness"]
        },
        "rf_results": {
            "feature_importance": {"latency": 0.7, "smoothness": 0.3},
            "metrics": {"r2": 0.8, "rmse": 0.1}
        }
    }
    
    text = generate_interpretation(mock_metrics)
    
    assert "Multiple Linear Regression" in text
    assert "Random Forest" in text
    assert "latency" in text
    assert "smoothness" in text
    assert "synthetic data" in text.lower()
    assert "correlational" in text.lower()