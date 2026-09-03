"""
Contract Test for T091: Power Analysis Results JSON

Verifies that data/processed/power_analysis_results.json exists and contains
the required keys and meets the threshold criteria.
"""
import json
import pytest
from pathlib import Path
from config import get_processed_data_dir

def test_power_analysis_results_exists():
    """Check that the power analysis results file exists."""
    processed_dir = get_processed_data_dir()
    output_path = processed_dir / "power_analysis_results.json"
    assert output_path.exists(), f"Power analysis results file not found at {output_path}"

def test_power_analysis_results_schema():
    """Check that the JSON contains required keys."""
    processed_dir = get_processed_data_dir()
    output_path = processed_dir / "power_analysis_results.json"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    required_keys = ["estimated_power", "target_N", "method"]
    for key in required_keys:
        assert key in data, f"Missing required key '{key}' in power analysis results"

def test_power_analysis_thresholds():
    """Check that estimated_power >= 0.80 and target_N >= 60 (if applicable)."""
    processed_dir = get_processed_data_dir()
    output_path = processed_dir / "power_analysis_results.json"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    estimated_power = data.get("estimated_power", 0.0)
    target_n = data.get("target_N", 0)
    
    # The task verification states: estimated_power >= 0.80
    # If the simulation was run correctly on a dataset with effect size 0.25 and N=60,
    # we expect power to be around 0.80 or higher.
    assert estimated_power >= 0.80, f"Estimated power {estimated_power} is below the required threshold of 0.80"
    
    # Target N should be at least the current N or higher
    assert target_n >= 60, f"Target N {target_n} is below the minimum sample size of 60"

def test_power_analysis_method():
    """Check that the method is documented."""
    processed_dir = get_processed_data_dir()
    output_path = processed_dir / "power_analysis_results.json"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    method = data.get("method", "")
    assert len(method) > 0, "Method description is empty"
    assert "LMM" in method or "Mixed" in method, f"Method '{method}' does not indicate LMM usage"