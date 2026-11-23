"""
Tests for the output validation logic in code/validate_output.py.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# We need to mock the config paths for testing in isolation
from validate_output import load_schema, load_output_data, validate_structure, main


@pytest.fixture
def temp_schema_path():
    """Create a temporary valid schema file for testing."""
    schema_content = {
        "type": "object",
        "required": ["metadata", "data"],
        "properties": {
            "metadata": {
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string"}
                }
            },
            "data": {
                "type": "array",
                "items": {"type": "object"}
            }
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema_content, f)
        path = Path(f.name)
    yield path
    os.unlink(path)


@pytest.fixture
def valid_output_data():
    """Create valid output data structure."""
    return {
        "metadata": {
            "schema_version": "1.0.0",
            "generated_at": "2023-10-01T12:00:00Z",
            "source_ecosystems": ["ecosystem_1"],
            "total_pairs": 2,
            "positive_pairs": 1,
            "negative_pairs": 1,
            "feature_columns": ["trait_a", "trait_b"],
            "label_column": "link_label"
        },
        "data": [
            {
                "plant_species": "PlantA",
                "pollinator_species": "PollinatorA",
                "ecosystem_id": "ecosystem_1",
                "link_label": 1,
                "traits": {"trait_a": 0.5, "trait_b": 0.8}
            },
            {
                "plant_species": "PlantB",
                "pollinator_species": "PollinatorB",
                "ecosystem_id": "ecosystem_1",
                "link_label": 0,
                "traits": {"trait_a": 0.2, "trait_b": 0.3}
            }
        ]
    }


@pytest.fixture
def temp_output_path(valid_output_data):
    """Create a temporary output JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_output_data, f)
        path = Path(f.name)
    yield path
    os.unlink(path)


def test_load_schema_success(temp_schema_path):
    """Test successful loading of a schema."""
    schema = load_schema(temp_schema_path)
    assert "type" in schema
    assert schema["type"] == "object"


def test_load_schema_not_found():
    """Test loading a non-existent schema."""
    with pytest.raises(FileNotFoundError):
        load_schema(Path("/non/existent/path/schema.yaml"))


def test_load_output_data_success(temp_output_path):
    """Test successful loading of output data."""
    metadata, data = load_output_data(temp_output_path)
    assert metadata["schema_version"] == "1.0.0"
    assert len(data) == 2


def test_load_output_data_missing_keys(temp_output_path):
    """Test loading output data with missing required keys."""
    # Create a file with missing keys
    bad_data = {"metadata": {}}
    with open(temp_output_path, 'w') as f:
        json.dump(bad_data, f)

    with pytest.raises(ValueError, match="must contain 'metadata' and 'data' keys"):
        load_output_data(temp_output_path)


def test_validate_structure_pass(valid_output_data, temp_schema_path):
    """Test validation of a valid structure."""
    # Load the simple schema from fixture
    schema = load_schema(temp_schema_path)
    # Adjust the real schema to match the simple test schema for this specific test
    # or use the real schema logic. Here we use the simple schema for the test.
    is_valid, errors = validate_structure(valid_output_data['metadata'], valid_output_data['data'], schema)
    assert is_valid
    assert len(errors) == 0


def test_validate_structure_metadata_mismatch(valid_output_data, temp_schema_path):
    """Test validation when metadata counts don't match."""
    schema = load_schema(temp_schema_path)
    # Modify metadata to create mismatch
    valid_output_data['metadata']['total_pairs'] = 100 # Should be 2
    
    is_valid, errors = validate_structure(valid_output_data['metadata'], valid_output_data['data'], schema)
    assert not is_valid
    assert any("Metadata inconsistency" in err for err in errors)


def test_validate_structure_data_count_mismatch(valid_output_data, temp_schema_path):
    """Test validation when data row count doesn't match metadata."""
    schema = load_schema(temp_schema_path)
    # Remove a row from data but keep metadata
    valid_output_data['data'].pop()
    
    is_valid, errors = validate_structure(valid_output_data['metadata'], valid_output_data['data'], schema)
    assert not is_valid
    assert any("Data row count" in err for err in errors)


def test_main_success(temp_output_path, temp_schema_path, valid_output_data, caplog):
    """Test main function with valid data."""
    # We need to mock get_data_processed to point to our temp file if we were testing the full path
    # But here we test the function logic directly by patching the internal calls if necessary.
    # Since main() calls load_schema and load_output_data without arguments (using defaults),
    # we need to ensure the default paths exist or mock them.
    # For this unit test, we will mock the functions to return our test data.
    
    with patch('validate_output.load_schema', return_value={
        "type": "object", "required": ["metadata", "data"],
        "properties": {
            "metadata": {"type": "object", "required": ["schema_version"], "properties": {"schema_version": {"type": "string"}}},
            "data": {"type": "array"}
        }
    }):
        with patch('validate_output.load_output_data', return_value=(valid_output_data['metadata'], valid_output_data['data'])):
            result = main()
            assert result == 0


def test_main_failure(caplog):
    """Test main function when validation fails."""
    invalid_data = {
        "metadata": {"schema_version": "1.0.0", "total_pairs": 0, "positive_pairs": 1, "negative_pairs": 0},
        "data": []
    }
    
    with patch('validate_output.load_schema', return_value={
        "type": "object", "required": ["metadata", "data"],
        "properties": {
            "metadata": {"type": "object", "required": ["schema_version"], "properties": {"schema_version": {"type": "string"}}},
            "data": {"type": "array"}
        }
    }):
        with patch('validate_output.load_output_data', return_value=(invalid_data['metadata'], invalid_data['data'])):
            result = main()
            assert result == 1
            assert "Validation FAILED" in caplog.text