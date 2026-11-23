"""
Tests for the JSON-Schema generation script (T009c).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def contracts_dir():
    return Path("contracts")


@pytest.fixture
def schema_files(contracts_dir):
    return [
        contracts_dir / "MoralResponse.schema.json",
        contracts_dir / "TemperatureRecord.schema.json",
        contracts_dir / "MergedDataset.schema.json",
    ]


def test_schema_generation_script_exists():
    """Verify the generation script exists."""
    script_path = Path("contracts/generate_schemas.py")
    assert script_path.exists(), f"Script {script_path} does not exist."


def test_schema_generation_runs_successfully():
    """Verify the script runs without errors."""
    script_path = Path("contracts/generate_schemas.py")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed with: {result.stderr}"


def test_schema_files_created(schema_files):
    """Verify all expected schema files are created."""
    for schema_file in schema_files:
        assert schema_file.exists(), f"Schema file {schema_file} was not created."
        assert schema_file.stat().st_size > 0, f"Schema file {schema_file} is empty."


def test_schema_files_are_valid_json(schema_files):
    """Verify all created schema files are valid JSON."""
    for schema_file in schema_files:
        with open(schema_file, 'r', encoding='utf-8') as f:
            try:
                json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {schema_file}: {e}")


def test_schema_files_contain_expected_properties(schema_files, contracts_dir):
    """Verify the schemas contain the expected top-level keys."""
    expected_keys = ["$schema", "type", "properties", "required"]
    
    # Map file names to expected root type
    # Note: JSON schema for a Pydantic model typically has 'type': 'object'
    
    for schema_file in schema_files:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        
        # Check for standard JSON Schema keywords
        assert "$schema" in schema, f"{schema_file} missing $schema"
        assert "type" in schema, f"{schema_file} missing type"
        assert "properties" in schema, f"{schema_file} missing properties"
        
        # Verify properties are not empty
        assert len(schema["properties"]) > 0, f"{schema_file} has no properties defined"


def test_moral_response_schema_has_expected_fields(schema_files, contracts_dir):
    """Verify MoralResponse schema contains required fields."""
    schema_path = contracts_dir / "MoralResponse.schema.json"
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    expected_fields = [
        "participant_id", "latitude", "longitude", 
        "timestamp", "response_time", "country", "dilemma_id"
    ]
    
    for field in expected_fields:
        assert field in schema["properties"], f"Missing field '{field}' in MoralResponse schema"


def test_temperature_record_schema_has_expected_fields(schema_files, contracts_dir):
    """Verify TemperatureRecord schema contains required fields."""
    schema_path = contracts_dir / "TemperatureRecord.schema.json"
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    expected_fields = [
        "grid_id", "timestamp", "latitude", "longitude", "temperature_celsius"
    ]
    
    for field in expected_fields:
        assert field in schema["properties"], f"Missing field '{field}' in TemperatureRecord schema"


def test_merged_dataset_schema_has_expected_fields(schema_files, contracts_dir):
    """Verify MergedDataset schema contains required fields including derived ones."""
    schema_path = contracts_dir / "MergedDataset.schema.json"
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    expected_fields = [
        "dilemma_choice", "dilemma_complexity", "time_of_day", 
        "temperature_celsius", "participant_id", "cultural_region"
    ]
    
    for field in expected_fields:
        assert field in schema["properties"], f"Missing field '{field}' in MergedDataset schema"
