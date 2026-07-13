"""
Contract test for simulation output schema.

Validates that the output from simulate_agent.py conforms to the expected
JSON schema defined in the project specifications.

This test ensures:
1. The output file exists at the expected path.
2. The root is a list of records.
3. Each record contains required fields: trajectory_id, retention_horizon, 
   density, critical_evidence_turn, success, total_turns.
4. Data types match the specification (int, float, bool, str).
5. Numeric values are within logical bounds (e.g., success is 0 or 1).
"""
import json
import os
import pytest
from pathlib import Path
from typing import Any, Dict, List

# Configuration matching simulate_agent.py output paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
SIMULATION_OUTPUT_FILE = OUTPUT_DIR / "simulation_results.json"

# Required schema definition
REQUIRED_FIELDS = {
    "trajectory_id": str,
    "retention_horizon": int,
    "density": float,
    "critical_evidence_turn": int,
    "success": bool,
    "total_turns": int,
    "timestamp": str  # Optional but expected if added by main
}

@pytest.fixture
def load_simulation_data():
    """Load the simulation output file if it exists."""
    if not SIMULATION_OUTPUT_FILE.exists():
        pytest.fail(f"Simulation output file not found at {SIMULATION_OUTPUT_FILE}. "
                    "Run simulate_agent.py before running this contract test.")
    
    with open(SIMULATION_OUTPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        pytest.fail("Simulation output root must be a list of records.")
    
    if len(data) == 0:
        pytest.fail("Simulation output file is empty. Ensure simulate_agent.py ran successfully.")
    
    return data

def test_output_file_exists():
    """Contract: The output file must exist at the specified path."""
    assert SIMULATION_OUTPUT_FILE.exists(), f"Output file {SIMULATION_OUTPUT_FILE} does not exist."

def test_root_structure_is_list(load_simulation_data):
    """Contract: The root element must be a list."""
    assert isinstance(load_simulation_data, list), "Root must be a list."

def test_all_records_have_required_fields(load_simulation_data):
    """Contract: Every record must contain all required fields."""
    for i, record in enumerate(load_simulation_data):
        missing_fields = [field for field in REQUIRED_FIELDS if field not in record]
        assert not missing_fields, f"Record {i} missing required fields: {missing_fields}"

def test_field_types_match_schema(load_simulation_data):
    """Contract: Field types must match the defined schema."""
    for i, record in enumerate(load_simulation_data):
        for field, expected_type in REQUIRED_FIELDS.items():
            if field in record:
                actual_type = type(record[field])
                assert actual_type == expected_type, (
                    f"Record {i}, field '{field}': expected {expected_type.__name__}, "
                    f"got {actual_type.__name__}. Value: {record[field]}"
                )

def test_success_value_is_boolean(load_simulation_data):
    """Contract: 'success' field must be a boolean (True/False), not int 0/1."""
    for i, record in enumerate(load_simulation_data):
        assert isinstance(record["success"], bool), (
            f"Record {i}: 'success' must be boolean. Found {type(record['success'])}."
        )

def test_retention_horizon_is_positive(load_simulation_data):
    """Contract: retention_horizon must be a positive integer."""
    for i, record in enumerate(load_simulation_data):
        assert record["retention_horizon"] > 0, (
            f"Record {i}: retention_horizon must be > 0, got {record['retention_horizon']}"
        )

def test_density_is_non_negative(load_simulation_data):
    """Contract: density must be >= 0."""
    for i, record in enumerate(load_simulation_data):
        assert record["density"] >= 0, (
            f"Record {i}: density must be >= 0, got {record['density']}"
        )

def test_critical_evidence_turn_within_bounds(load_simulation_data):
    """Contract: critical_evidence_turn must be within [0, total_turns)."""
    for i, record in enumerate(load_simulation_data):
        turn = record["critical_evidence_turn"]
        total = record["total_turns"]
        assert 0 <= turn < total, (
            f"Record {i}: critical_evidence_turn ({turn}) must be in [0, {total})"
        )

def test_trajectory_id_is_string(load_simulation_data):
    """Contract: trajectory_id must be a non-empty string."""
    for i, record in enumerate(load_simulation_data):
        assert isinstance(record["trajectory_id"], str), (
            f"Record {i}: trajectory_id must be string."
        )
        assert len(record["trajectory_id"]) > 0, (
            f"Record {i}: trajectory_id cannot be empty."
        )

def test_no_extra_fields(load_simulation_data):
    """Contract: Records should not contain unexpected fields (strict schema)."""
    # Note: If the spec allows extra fields, this test should be removed or adjusted.
    # Currently enforcing strict schema based on REQUIRED_FIELDS.
    for i, record in enumerate(load_simulation_data):
        extra_fields = set(record.keys()) - set(REQUIRED_FIELDS.keys())
        # Allow 'timestamp' if it exists, otherwise strict check
        allowed_extra = {"timestamp"}
        if extra_fields - allowed_extra:
            pytest.fail(f"Record {i} contains unexpected fields: {extra_fields - allowed_extra}")