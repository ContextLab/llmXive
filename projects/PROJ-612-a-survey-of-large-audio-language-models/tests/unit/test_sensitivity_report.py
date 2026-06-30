"""
Unit tests for T022b: Sensitivity Report Generation.
"""
import json
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_sensitivity_report import (
    calculate_p_value,
    generate_sensitivity_report,
    load_sensitivity_config
)
from analyze_correlation import compute_spearman_correlation

def test_calculate_p_value():
    """Test p-value calculation from permutation distribution."""
    # Simulate a null distribution centered around 0
    permuted_corrs = [0.1, -0.2, 0.05, -0.1, 0.0, 0.15, -0.05, 0.2, -0.15, 0.1]
    
    # Test with an extreme value
    p_val = calculate_p_value(permuted_corrs, 0.9)
    assert p_val == 0.0, "Extreme value should have p=0.0"
    
    # Test with a common value
    p_val = calculate_p_value(permuted_corrs, 0.1)
    assert p_val > 0.5, "Common value should have high p-value"
    
    # Test with empty list
    p_val = calculate_p_value([], 0.5)
    assert p_val == 1.0, "Empty list should return p=1.0"

def test_generate_sensitivity_report_minimal():
    """Test report generation with minimal data."""
    # Create minimal valid inputs
    training_data = {
        "speech": {"total_hours": 1000.0},
        "music": {"total_hours": 500.0},
        "env": {"total_hours": 200.0}
    }
    
    hallucination_rates = [
        {"domain": "speech", "rate": 0.1},
        {"domain": "music", "rate": 0.3},
        {"domain": "env", "rate": 0.5}
    ]
    
    report = generate_sensitivity_report(
        training_data, hallucination_rates, num_permutations=10, seed=42
    )
    
    assert report["status"] == "complete"
    assert "original_correlation" in report
    assert "p_value" in report
    assert "significance" in report
    assert "null_distribution_percentiles" in report
    assert report["num_permutations"] == 10
    assert report["random_seed"] == 42

def test_load_sensitivity_config_default():
    """Test that default config is returned when file missing."""
    # Temporarily rename config if it exists
    config_path = Path("config.yaml")
    backup_path = Path("config.yaml.backup")
    
    if config_path.exists():
        config_path.rename(backup_path)
    
    try:
        config = load_sensitivity_config()
        assert "num_permutations" in config
        assert "random_seed" in config
        assert config["num_permutations"] == 1000
        assert config["random_seed"] == 42
    finally:
        # Restore config if it existed
        if backup_path.exists():
            backup_path.rename(config_path)

def test_spearman_correlation_basic():
    """Basic test for Spearman correlation function."""
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    
    corr, p_val = compute_spearman_correlation(x, y)
    assert abs(corr - 1.0) < 0.01, "Perfect positive correlation expected"
    
    # Negative correlation
    y_neg = [10, 8, 6, 4, 2]
    corr_neg, _ = compute_spearman_correlation(x, y_neg)
    assert abs(corr_neg - (-1.0)) < 0.01, "Perfect negative correlation expected"

def test_report_structure():
    """Verify the report structure matches specification."""
    training_data = {
        "speech": {"total_hours": 1000.0},
        "music": {"total_hours": 500.0},
        "env": {"total_hours": 200.0}
    }
    
    hallucination_rates = [
        {"domain": "speech", "rate": 0.1},
        {"domain": "music", "rate": 0.3},
        {"domain": "env", "rate": 0.5}
    ]
    
    report = generate_sensitivity_report(
        training_data, hallucination_rates, num_permutations=5, seed=123
    )
    
    # Check required fields
    required_fields = [
        "status", "original_correlation", "p_value", "significance",
        "num_permutations", "random_seed", "null_distribution_percentiles",
        "interpretation", "data_points", "domains_analyzed"
    ]
    
    for field in required_fields:
        assert field in report, f"Missing required field: {field}"
    
    # Check percentiles structure
    percentiles = report["null_distribution_percentiles"]
    required_percentiles = ["p10", "p25", "p50", "p75", "p90"]
    for p in required_percentiles:
        assert p in percentiles, f"Missing percentile: {p}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])