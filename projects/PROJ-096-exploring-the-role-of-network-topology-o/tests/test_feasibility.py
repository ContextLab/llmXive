import json
import os
import pytest
from pathlib import Path

def test_feasibility_study_output_exists():
    """Verify that the feasibility study produces the config.json file."""
    assert Path("data/processed/config.json").exists(), "config.json not found"

def test_feasibility_study_output_structure():
    """Verify the structure of the generated config.json."""
    with open("data/processed/config.json", "r") as f:
        data = json.load(f)
    
    required_keys = [
        "time_steps", "n_topologies", "runtime_estimate", 
        "contingency_flag", "SC_003_VIOLATION", "scope_reduction_factor"
    ]
    
    for key in required_keys:
        assert key in data, f"Missing key: {key}"
    
    assert isinstance(data["time_steps"], int), "time_steps must be an integer"
    assert isinstance(data["n_topologies"], int), "n_topologies must be an integer"
    assert isinstance(data["runtime_estimate"], (int, float)), "runtime_estimate must be numeric"
    assert isinstance(data["contingency_flag"], bool), "contingency_flag must be boolean"
    assert isinstance(data["SC_003_VIOLATION"], bool), "SC_003_VIOLATION must be boolean"
    assert isinstance(data["scope_reduction_factor"], (int, float)), "scope_reduction_factor must be numeric"

def test_feasibility_study_constraints():
    """Verify that the output meets the constraints defined in T009."""
    with open("data/processed/config.json", "r") as f:
        data = json.load(f)
    
    # If there's an error, time_steps should be 0
    if data.get("error"):
        assert data["time_steps"] == 0, "If error exists, time_steps must be 0"
        return

    # Otherwise, time_steps must be >= 1000
    assert data["time_steps"] >= 1000, f"time_steps ({data['time_steps']}) must be >= 1000"
    assert data["n_topologies"] >= 10, f"n_topologies ({data['n_topologies']}) must be >= 10"

def test_feasibility_study_logic():
    """Verify that the calculated runtime estimate is consistent with time_steps and n_topologies."""
    with open("data/processed/config.json", "r") as f:
        data = json.load(f)
    
    if data.get("error"):
        return

    # Basic sanity check: runtime_estimate should be positive if steps > 0
    if data["time_steps"] > 0:
        assert data["runtime_estimate"] > 0, "runtime_estimate must be positive"
    
    # Check contingency flag logic
    if data["n_topologies"] < 50: # Assuming 50 is the target
        assert data["contingency_flag"] == True, "contingency_flag should be True if n_topologies < 50"