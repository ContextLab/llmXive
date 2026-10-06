"""
Unit tests for T044: Initialize metadata.json
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# We assume the function is in code/init_metadata.py
import sys
from pathlib import Path as PathLib
sys.path.insert(0, str(PathLib(__file__).parent.parent.parent / "code"))

from init_metadata import get_metadata_schema, initialize_metadata

def test_get_metadata_schema_structure():
    """Verify the schema has the required keys and default values."""
    schema = get_metadata_schema()
    
    assert isinstance(schema, dict)
    assert "skipped_electrodes" in schema
    assert "assumptions" in schema
    assert "data_source_url" in schema
    assert "fetch_method" in schema
    
    assert schema["skipped_electrodes"] == []
    assert schema["assumptions"] == {}
    assert schema["data_source_url"] is None
    assert schema["fetch_method"] is None

def test_initialize_metadata_creates_file():
    """Verify that initialize_metadata creates the file with correct content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metadata.json"
        initialize_metadata(str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            content = json.load(f)
        
        assert content == get_metadata_schema()

def test_initialize_metadata_creates_directories():
    """Verify that initialize_metadata creates parent directories if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Deep nested path that doesn't exist
        output_path = Path(tmpdir) / "level1" / "level2" / "metadata.json"
        
        assert not output_path.parent.exists()
        
        initialize_metadata(str(output_path))
        
        assert output_path.exists()
        assert output_path.parent.exists()

def test_initialize_metadata_overwrites_existing():
    """Verify that initialize_metadata overwrites an existing file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metadata.json"
        
        # Write invalid content first
        with open(output_path, 'w') as f:
            json.dump({"invalid": "data"}, f)
        
        # Re-initialize
        initialize_metadata(str(output_path))
        
        with open(output_path, 'r') as f:
            content = json.load(f)
        
        assert content == get_metadata_schema()
        assert content.get("invalid") is None