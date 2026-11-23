import pytest
import yaml
import json
from pathlib import Path
import tempfile
import os
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import validate_dataset, load_schema
from jsonschema import ValidationError

@pytest.fixture
def temp_schema():
    """Create a temporary schema file for testing."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["bulk_config_id", "impurity_species"],
        "properties": {
            "bulk_config_id": {"type": "string"},
            "impurity_species": {"type": "string"},
            "alloy_system_id": {"type": "string"},
            "clustering_descriptors": {
                "type": "object",
                "required": ["rdf_peak", "pair_corr", "voronoi_count"],
                "properties": {
                    "rdf_peak": {"type": "number"},
                    "pair_corr": {"type": "number"},
                    "voronoi_count": {"type": "number"}
                }
            },
            "segregation_energy": {"type": "number", "nullable": True}
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema, f)
        return Path(f.name)

@pytest.fixture
def valid_data():
    """Create valid test data."""
    return {
        "bulk_config_id": "mp-12345",
        "impurity_species": "Cr",
        "alloy_system_id": "BCC_Cr",
        "clustering_descriptors": {
            "rdf_peak": 2.5,
            "pair_corr": 0.8,
            "voronoi_count": 12
        },
        "segregation_energy": -0.5
    }

@pytest.fixture
def invalid_data():
    """Create invalid test data (missing required field)."""
    return {
        "bulk_config_id": "mp-12345",
        # Missing impurity_species
        "alloy_system_id": "BCC_Cr"
    }

def test_validate_valid_data(temp_schema, valid_data):
    """Test that valid data passes validation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_data, f)
        data_path = Path(f.name)
    
    try:
        result = validate_dataset(data_path, temp_schema)
        assert result is True
    finally:
        os.unlink(data_path)

def test_validate_invalid_data(temp_schema, invalid_data):
    """Test that invalid data raises ValidationError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(invalid_data, f)
        data_path = Path(f.name)
    
    try:
        with pytest.raises(ValidationError):
            validate_dataset(data_path, temp_schema)
    finally:
        os.unlink(data_path)

def test_validate_missing_data_file(temp_schema):
    """Test that missing data file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        validate_dataset(Path('/nonexistent/file.yaml'), temp_schema)

def test_validate_missing_schema_file(valid_data):
    """Test that missing schema file raises FileNotFoundError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(valid_data, f)
        data_path = Path(f.name)
    
    try:
        with pytest.raises(FileNotFoundError):
            validate_dataset(data_path, Path('/nonexistent/schema.yaml'))
    finally:
        os.unlink(data_path)

def test_load_schema(temp_schema):
    """Test schema loading."""
    schema = load_schema(temp_schema)
    assert "$schema" in schema
    assert schema["type"] == "object"
    assert "required" in schema

def test_validate_json_format(temp_schema, valid_data):
    """Test validation with JSON format data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(valid_data, f)
        data_path = Path(f.name)
    
    try:
        result = validate_dataset(data_path, temp_schema)
        assert result is True
    finally:
        os.unlink(data_path)

def test_validate_unsupported_format(temp_schema, valid_data):
    """Test that unsupported file format raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(str(valid_data))
        data_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError):
            validate_dataset(data_path, temp_schema)
    finally:
        os.unlink(data_path)
