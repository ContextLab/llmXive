"""
Unit tests for Simulation Methodology documentation and metadata.
Verifies T055: simulation_methodology field presence in metadata.json
and consistency with plan.md/spec.md documentation.
"""
import json
import os
import pytest
from pathlib import Path

# Base path for data
DATA_RAW_PATH = Path("data/raw/metadata.json")
PLAN_PATH = Path("plan.md")
SPEC_PATH = Path("spec.md")

@pytest.fixture
def metadata():
    if not DATA_RAW_PATH.exists():
        pytest.skip("data/raw/metadata.json not found. Run ingestion pipeline first.")
    with open(DATA_RAW_PATH, "r") as f:
        return json.load(f)

def test_simulation_methodology_exists(metadata):
    """Ensure simulation_methodology key exists in metadata if simulation mode is true."""
    is_sim = metadata.get("simulation_mode", False)
    if is_sim:
        assert "simulation_methodology" in metadata, (
            "simulation_mode is True but 'simulation_methodology' field is missing from metadata.json"
        )

def test_simulation_methodology_structure(metadata):
    """Verify the structure of simulation_methodology."""
    if not metadata.get("simulation_mode", False):
        pytest.skip("Simulation mode is not active.")
    
    methodology = metadata.get("simulation_methodology", {})
    
    required_keys = ["random_seed", "distribution_parameters", "sample_size", "generation_logic"]
    missing = [k for k in required_keys if k not in methodology]
    
    assert not missing, f"simulation_methodology missing required keys: {missing}"

def test_random_seed_is_integer(metadata):
    """Verify random_seed is an integer."""
    if not metadata.get("simulation_mode", False):
        pytest.skip("Simulation mode is not active.")
    
    seed = metadata.get("simulation_methodology", {}).get("random_seed")
    assert isinstance(seed, int), f"random_seed must be an integer, got {type(seed)}"

def test_plan_docs_simulation_methodology():
    """Verify plan.md documents the simulation_methodology field."""
    assert PLAN_PATH.exists(), "plan.md not found"
    with open(PLAN_PATH, "r") as f:
        content = f.read()
    
    assert "simulation_methodology" in content, (
        "plan.md must document the 'simulation_methodology' field in metadata.json"
    )
    assert "Verified Accuracy" in content or "Reproducibility" in content, (
        "plan.md must reference Verification/Reproducibility gates for simulation"
    )

def test_spec_docs_simulation_methodology():
    """Verify spec.md documents the simulation_methodology field."""
    assert SPEC_PATH.exists(), "spec.md not found"
    with open(SPEC_PATH, "r") as f:
        content = f.read()
    
    assert "simulation_methodology" in content, (
        "spec.md must document the 'simulation_methodology' field in metadata.json"
    )
    assert "Verification & Accuracy Gates" in content, (
        "spec.md must include a section on Verification & Accuracy Gates"
    )