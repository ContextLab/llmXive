"""Tests for the configuration loader and schema map."""
import json
import pytest
from pathlib import Path
import sys

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config.loader import load_schema_map, get_target_columns, get_source_columns_for_target


def test_load_schema_map_exists():
    """Test that the schema map file exists and loads valid JSON."""
    mappings = load_schema_map()
    assert isinstance(mappings, dict)
    assert len(mappings) > 0
    # Check for expected keys based on task requirements
    assert 'power' in mappings
    assert 'hardness' in mappings
    assert 'wear_rate' in mappings


def test_schema_map_content():
    """Test specific mapping content."""
    mappings = load_schema_map()
    
    # Check power mapping
    assert 'laser_power' in mappings['power']
    assert 'laser_pwr' in mappings['power']
    
    # Check hardness mapping
    assert 'hv' in mappings['hardness']
    assert 'vickers' in mappings['hardness']


def test_get_target_columns():
    """Test retrieval of target columns list."""
    targets = get_target_columns()
    assert isinstance(targets, list)
    assert 'power' in targets
    assert 'wear_rate' in targets
    assert 'pattern_geometry' in targets


def test_get_source_columns_for_target():
    """Test retrieval of source columns for a specific target."""
    sources = get_source_columns_for_target('power')
    assert isinstance(sources, list)
    assert 'laser_power' in sources
    
    # Test non-existent target
    empty_sources = get_source_columns_for_target('non_existent_column')
    assert empty_sources == []
