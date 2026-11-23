"""
Tests for JSON-Schema generation functionality.

Verifies that:
1. The generate_json_schemas script runs without errors.
2. The generated schema files exist and are valid JSON.
3. The generated schemas contain the expected top-level keys.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"


def test_generate_json_schemas_runs_successfully():
    """Test that the script executes without errors."""
    script_path = PROJECT_ROOT / "contracts" / "generate_json_schemas.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed with:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    assert "generated successfully" in result.stdout.lower()


def test_moral_response_schema_exists_and_is_valid_json():
    """Test that MoralResponse.schema.json exists and is valid JSON."""
    schema_path = CONTRACTS_DIR / "MoralResponse.schema.json"
    
    assert schema_path.exists(), f"File not found: {schema_path}"
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    # Basic validation of JSON schema structure
    assert "$schema" in schema or "type" in schema, "Invalid JSON Schema structure"
    assert "properties" in schema, "Missing 'properties' in schema"
    
    # Check for expected fields from MoralResponse model
    expected_fields = ["participant_id", "latitude", "longitude", "timestamp", "response_time", "country", "dilemma_id"]
    for field in expected_fields:
        assert field in schema["properties"], f"Missing expected field '{field}' in MoralResponse schema"


def test_temperature_record_schema_exists_and_is_valid_json():
    """Test that TemperatureRecord.schema.json exists and is valid JSON."""
    schema_path = CONTRACTS_DIR / "TemperatureRecord.schema.json"
    
    assert schema_path.exists(), f"File not found: {schema_path}"
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    # Basic validation of JSON schema structure
    assert "$schema" in schema or "type" in schema, "Invalid JSON Schema structure"
    assert "properties" in schema, "Missing 'properties' in schema"
    
    # Check for expected fields from TemperatureRecord model
    expected_fields = ["grid_id", "timestamp", "latitude", "longitude", "temperature_celsius"]
    for field in expected_fields:
        assert field in schema["properties"], f"Missing expected field '{field}' in TemperatureRecord schema"


def test_merged_dataset_schema_exists_and_is_valid_json():
    """Test that MergedDataset.schema.json exists and is valid JSON."""
    schema_path = CONTRACTS_DIR / "MergedDataset.schema.json"
    
    assert schema_path.exists(), f"File not found: {schema_path}"
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    # Basic validation of JSON schema structure
    assert "$schema" in schema or "type" in schema, "Invalid JSON Schema structure"
    assert "properties" in schema, "Missing 'properties' in schema"
    
    # Check for expected fields from MergedDataset model
    expected_fields = [
        # From raw models
        "participant_id", "latitude", "longitude", "timestamp", "response_time", "country", "dilemma_id",
        "grid_id", "temperature_celsius",
        # Derived fields
        "dilemma_choice", "dilemma_complexity", "time_of_day", "cultural_region"
    ]
    for field in expected_fields:
        assert field in schema["properties"], f"Missing expected field '{field}' in MergedDataset schema"


def test_schemas_are_consistent_with_models():
    """
    Verify that the generated schemas match the Pydantic model definitions.
    This is a sanity check to ensure the generation process is working correctly.
    """
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    
    from contracts.models import MoralResponse, TemperatureRecord, MergedDataset
    
    # Get model fields
    moral_response_fields = set(MoralResponse.model_fields.keys())
    temperature_record_fields = set(TemperatureRecord.model_fields.keys())
    merged_dataset_fields = set(MergedDataset.model_fields.keys())
    
    # Load generated schemas
    with open(CONTRACTS_DIR / "MoralResponse.schema.json") as f:
        moral_schema = json.load(f)
    with open(CONTRACTS_DIR / "TemperatureRecord.schema.json") as f:
        temp_schema = json.load(f)
    with open(CONTRACTS_DIR / "MergedDataset.schema.json") as f:
        merged_schema = json.load(f)
    
    # Compare fields
    assert set(moral_schema["properties"].keys()) == moral_response_fields, \
        "MoralResponse schema fields do not match model fields"
    assert set(temp_schema["properties"].keys()) == temperature_record_fields, \
        "TemperatureRecord schema fields do not match model fields"
    assert set(merged_schema["properties"].keys()) == merged_dataset_fields, \
        "MergedDataset schema fields do not match model fields"