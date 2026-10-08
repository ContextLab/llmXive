"""
Integration test for main_us1.py.

Verifies that the script runs end-to-end, loads real data (or a small subset),
executes the simulation loop, and produces a valid JSON output file.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import SimulationConfig
from main_us1 import run_single_condition_simulation

@pytest.mark.integration
def test_main_us1_execution(tmp_path):
    """
    Test that main_us1.py executes successfully and produces a valid JSON output.
    Uses a small, known dataset ID (53) and a reduced iteration count for speed.
    """
    output_file = tmp_path / "us1_results.json"
    
    # Use a small dataset and few iterations for CI speed
    config_dict = {
        "dataset_id": 53,  # OpenML: "diabetes" (small, numeric)
        "mechanism": "MCAR",
        "rate": 0.1,
        "outcome_type": "continuous",
        "iterations": 50,  # Reduced for testing
        "seed": 42,
        "method": "CC"
    }

    # Run the simulation
    results = run_single_condition_simulation(config_dict, str(output_file))

    # Assertions
    assert output_file.exists(), "Output file was not created."
    
    with open(output_file, 'r') as f:
        loaded_results = json.load(f)

    # Check structure
    assert "empirical_type1_error" in loaded_results
    assert "p_value_distribution" in loaded_results
    assert "total_iterations" in loaded_results
    assert "significant_count" in loaded_results
    assert "config" in loaded_results

    # Check values
    assert loaded_results["total_iterations"] == 50
    assert 0.0 <= loaded_results["empirical_type1_error"] <= 1.0
    assert "dataset_info" in loaded_results
    assert loaded_results["dataset_info"]["id"] == 53

    logger = __import__('logging').getLogger(__name__)
    logger.info(f"Integration test passed. Empirical Type I Error: {loaded_results['empirical_type1_error']}")
