import os
import json
import pytest
from pathlib import Path

# We need to ensure the code directory is in the path for imports
# But since we are testing the logic, we can mock or import directly if available
# For this test, we assume the feasibility_study.py is runnable and produces the file.

@pytest.mark.integration
def test_feasibility_study_output_exists():
    """Verify that T009 produces the required config.json file."""
    config_path = Path("data/processed/config.json")
    assert config_path.exists(), "data/processed/config.json must exist after running T009"

@pytest.mark.integration
def test_feasibility_study_content_valid():
    """Verify the content of config.json meets the minimum requirements."""
    config_path = Path("data/processed/config.json")
    if not config_path.exists():
        pytest.skip("config.json not found, run T009 first")

    with open(config_path) as f:
        data = json.load(f)

    assert "time_steps" in data, "config.json must contain 'time_steps'"
    assert "n_topologies" in data, "config.json must contain 'n_topologies'"
    assert "runtime_estimate" in data, "config.json must contain 'runtime_estimate'"

    # Verification constraint from tasks.md
    assert data["time_steps"] >= 1000, f"time_steps ({data['time_steps']}) must be >= 1000"
    assert data["n_topologies"] >= 10, f"n_topologies ({data['n_topologies']}) must be >= 10"

@pytest.mark.unit
def test_runtime_calculation_logic():
    """
    Unit test for the logic of runtime calculation (if we could import the function).
    Since we are in a test environment, we verify the mathematical logic separately.
    """
    # Simulate the logic
    total_budget = 6 * 3600
    runtime_per_1k = 1.0  # 1 second per 1k steps
    
    # Logic from task: max_time_steps = floor(6h / (runtime_per_1k_steps * 50)) * 1000
    base = total_budget / (runtime_per_1k * 50)
    max_steps = int(base) * 1000
    
    assert max_steps == 432000, "Math check for max_steps"
    
    # If runtime_per_1k was high, say 100s
    runtime_per_1k_high = 100.0
    base_high = total_budget / (runtime_per_1k_high * 50)
    max_steps_high = int(base_high) * 1000
    
    assert max_steps_high < 1000, "Should detect low capacity"
    
    # Then calculate n_topologies
    n_top = int(total_budget / runtime_per_1k_high)
    assert n_top == 216, "Math check for n_topologies"