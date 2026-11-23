"""
Unit tests for the configuration loader (code/config/loader.py).
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the module under test
from config.loader import (
    load_schema_map, 
    get_target_columns, 
    get_source_columns_for_target,
    get_mapping_for_source
)

# Path to the schema file relative to the test execution context
# Assuming tests are run from project root
SCHEMA_PATH = Path("code/config/schema_map.json")

@pytest.fixture
def mock_schema_data():
    return {
        "description": "Test schema",
        "version": "1.0.0",
        "mappings": {
            "power": ["power", "laser_power", "laser_pwr"],
            "hardness": ["hv", "vickers", "hardness"]
        },
        "target_columns": ["power", "hardness"]
    }

def test_load_schema_map_exists():
    """Test that load_schema_map successfully loads the existing file."""
    schema = load_schema_map()
    assert isinstance(schema, dict)
    assert "mappings" in schema
    assert "target_columns" in schema
    assert "power" in schema["mappings"]

def test_get_target_columns():
    """Test retrieval of target columns."""
    targets = get_target_columns()
    assert isinstance(targets, list)
    assert "power" in targets
    assert "hardness" in targets

def test_get_source_columns_for_target_valid():
    """Test retrieval of source columns for a valid target."""
    sources = get_source_columns_for_target("power")
    assert isinstance(sources, list)
    assert "laser_power" in sources
    assert "power" in sources

def test_get_source_columns_for_target_invalid():
    """Test that KeyError is raised for an invalid target."""
    with pytest.raises(KeyError):
        get_source_columns_for_target("non_existent_column")

def test_get_mapping_for_source_valid():
    """Test mapping from source to target for valid source."""
    target = get_mapping_for_source("laser_pwr")
    assert target == "power"
    
    target2 = get_mapping_for_source("hv")
    assert target2 == "hardness"

def test_get_mapping_for_source_case_insensitive():
    """Test that mapping is case-insensitive."""
    target = get_mapping_for_source("LASER_PWR")
    assert target == "power"

def test_get_mapping_for_source_invalid():
    """Test that None is returned for a source with no mapping."""
    target = get_mapping_for_source("unknown_column_xyz")
    assert target is None

def test_load_schema_map_file_not_found():
    """Test behavior when schema file is missing."""
    # Temporarily rename the file or mock the path
    original_path = Path("code/config/schema_map.json")
    backup_path = Path("code/config/schema_map.json.bak")
    
    if original_path.exists():
        original_path.rename(backup_path)
    
    try:
        # Clear cache to force reload
        import config.loader
        config.loader._schema_cache = None
        
        with pytest.raises(FileNotFoundError):
            load_schema_map()
    finally:
        # Restore the file
        if backup_path.exists():
            backup_path.rename(original_path)
        # Reset cache
        config.loader._schema_cache = None
