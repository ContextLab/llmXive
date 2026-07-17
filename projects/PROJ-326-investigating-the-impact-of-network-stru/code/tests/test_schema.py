"""
Unit tests for the simulation schema validation and I/O.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from code.src.simulation.schema import (
    SchemaError,
    get_schema,
    get_results_schema,
    validate_simulation_run,
    validate_results_file,
    save_results,
    load_results
)

@pytest.fixture
def valid_single_run():
    """Create a valid single simulation run dictionary."""
    return {
        "network_id": "test_network_001",
        "seed": 42,
        "diffusion_rate": 0.0523,
        "topology_class": "ER",
        "energy_density_profile": [1.0, 0.95, 0.90],
        "spatial_variance": 0.12,
        "time_steps": 100,
        "timestamp": datetime.now().isoformat(),
        "parameters": {"beta": 1.0}
    }

@pytest.fixture
def valid_results_file(tmp_path, valid_single_run):
    """Create a temporary valid results file."""
    results = {
        "runs": [valid_single_run],
        "metadata": {
            "generated_at": valid_single_run["timestamp"],
            "total_runs": 1
        }
    }
    file_path = tmp_path / "test_results.json"
    with open(file_path, 'w') as f:
        json.dump(results, f)
    return str(file_path)

def test_schema_structure():
    """Test that the schema returns the expected structure."""
    schema = get_schema()
    assert "$schema" in schema
    assert schema["type"] == "object"
    assert "network_id" in schema["required"]
    assert "seed" in schema["required"]
    assert "diffusion_rate" in schema["required"]
    assert "topology_class" in schema["required"]
    assert "timestamp" in schema["required"]

def test_validate_valid_run(valid_single_run):
    """Test validation of a valid single run."""
    assert validate_simulation_run(valid_single_run) is True

def test_validate_missing_required_field(valid_single_run):
    """Test validation fails when a required field is missing."""
    run = valid_single_run.copy()
    del run["seed"]
    with pytest.raises(SchemaError, match="Missing required field: seed"):
        validate_simulation_run(run)

def test_validate_wrong_type_network_id(valid_single_run):
    """Test validation fails when network_id is not a string."""
    run = valid_single_run.copy()
    run["network_id"] = 123
    with pytest.raises(SchemaError, match="network_id must be a string"):
        validate_simulation_run(run)

def test_validate_wrong_type_seed(valid_single_run):
    """Test validation fails when seed is not an integer."""
    run = valid_single_run.copy()
    run["seed"] = "42"
    with pytest.raises(SchemaError, match="seed must be an integer"):
        validate_simulation_run(run)

def test_validate_wrong_type_diffusion_rate(valid_single_run):
    """Test validation fails when diffusion_rate is not a number."""
    run = valid_single_run.copy()
    run["diffusion_rate"] = "high"
    with pytest.raises(SchemaError, match="diffusion_rate must be a number"):
        validate_simulation_run(run)

def test_validate_empty_energy_profile(valid_single_run):
    """Test validation fails when energy_density_profile is empty."""
    run = valid_single_run.copy()
    run["energy_density_profile"] = []
    with pytest.raises(SchemaError, match="energy_density_profile cannot be empty"):
        validate_simulation_run(run)

def test_validate_results_file_valid(valid_results_file):
    """Test validation of a valid results file."""
    with open(valid_results_file, 'r') as f:
        data = json.load(f)
    assert validate_results_file(data) is True

def test_validate_results_file_missing_runs(valid_results_file):
    """Test validation fails when 'runs' is missing."""
    with open(valid_results_file, 'r') as f:
        data = json.load(f)
    del data["runs"]
    with pytest.raises(SchemaError, match="Missing required field: 'runs'"):
        validate_results_file(data)

def test_validate_results_file_invalid_run(valid_results_file, valid_single_run):
    """Test validation fails when a run in the list is invalid."""
    with open(valid_results_file, 'r') as f:
        data = json.load(f)
    # Corrupt the first run
    data["runs"][0]["seed"] = "invalid"
    with pytest.raises(SchemaError, match="seed must be an integer"):
        validate_results_file(data)

def test_save_results_valid(tmp_path, valid_single_run):
    """Test saving valid results to a file."""
    output_path = tmp_path / "saved_results.json"
    save_results([valid_single_run], str(output_path))
    assert output_path.exists()
    
    # Verify content
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert "runs" in saved_data
    assert len(saved_data["runs"]) == 1
    assert saved_data["runs"][0]["network_id"] == valid_single_run["network_id"]

def test_save_results_empty_list(tmp_path):
    """Test that saving an empty list raises an error."""
    output_path = tmp_path / "empty_results.json"
    with pytest.raises(ValueError, match="Cannot save empty results list"):
        save_results([], str(output_path))

def test_load_results_valid(valid_results_file):
    """Test loading valid results from a file."""
    loaded = load_results(valid_results_file)
    assert len(loaded) == 1
    assert loaded[0]["network_id"] == "test_network_001"

def test_load_results_file_not_found(tmp_path):
    """Test that loading a non-existent file raises FileNotFoundError."""
    non_existent = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        load_results(str(non_existent))

def test_load_results_invalid_schema(tmp_path):
    """Test that loading an invalid schema file raises SchemaError."""
    file_path = tmp_path / "invalid.json"
    with open(file_path, 'w') as f:
        json.dump({"runs": [{"network_id": 123}]}, f)  # Invalid network_id type
    
    with pytest.raises(SchemaError):
        load_results(str(file_path))