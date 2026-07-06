"""
Tests for verifying the validity and structure of the data schemas.
"""
import os
import sys
import json
import yaml
from pathlib import Path

# Add parent to path for imports if running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

def load_schema(schema_path: str) -> dict:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_waveform_schema_exists():
    """Verify waveform schema file exists."""
    schema_path = Path("code/contracts/waveform.schema.yaml")
    assert schema_path.exists(), f"Schema file not found: {schema_path}"

def test_result_schema_exists():
    """Verify result schema file exists."""
    schema_path = Path("code/contracts/result.schema.yaml")
    assert schema_path.exists(), f"Schema file not found: {schema_path}"

def test_waveform_schema_syntax():
    """Verify waveform schema is valid YAML and has required top-level keys."""
    schema_path = Path("code/contracts/waveform.schema.yaml")
    schema = load_schema(str(schema_path))
    
    assert "title" in schema, "Schema missing 'title'"
    assert schema["title"] == "Gravitational Waveform Dataset Schema"
    assert "type" in schema, "Schema missing 'type'"
    assert schema["type"] == "object"
    assert "properties" in schema, "Schema missing 'properties'"
    assert "metadata" in schema["properties"], "Schema missing 'metadata' property"
    assert "signals" in schema["properties"], "Schema missing 'signals' property"

def test_result_schema_syntax():
    """Verify result schema is valid YAML and has required top-level keys."""
    schema_path = Path("code/contracts/result.schema.yaml")
    schema = load_schema(str(schema_path))
    
    assert "title" in schema, "Schema missing 'title'"
    assert schema["title"] == "Parameter Estimation Result Schema"
    assert "type" in schema, "Schema missing 'type'"
    assert schema["type"] == "object"
    assert "properties" in schema, "Schema missing 'properties'"
    assert "metadata" in schema["properties"], "Schema missing 'metadata' property"
    assert "results" in schema["properties"], "Schema missing 'results' property"

def test_waveform_schema_required_fields():
    """Verify waveform schema defines required fields."""
    schema_path = Path("code/contracts/waveform.schema.yaml")
    schema = load_schema(str(schema_path))
    
    assert "required" in schema, "Root schema missing 'required'"
    assert "metadata" in schema["required"], "Root 'required' missing 'metadata'"
    assert "signals" in schema["required"], "Root 'required' missing 'signals'"

    metadata_schema = schema["properties"]["metadata"]
    assert "required" in metadata_schema, "Metadata schema missing 'required'"
    assert "version" in metadata_schema["required"], "Metadata 'required' missing 'version'"
    
    signals_schema = schema["properties"]["signals"]
    assert "items" in signals_schema, "Signals schema missing 'items'"
    assert "required" in signals_schema["items"], "Signal item schema missing 'required'"
    assert "signal_id" in signals_schema["items"]["required"], "Signal item 'required' missing 'signal_id'"

def test_result_schema_required_fields():
    """Verify result schema defines required fields."""
    schema_path = Path("code/contracts/result.schema.yaml")
    schema = load_schema(str(schema_path))
    
    assert "required" in schema, "Root schema missing 'required'"
    assert "metadata" in schema["required"], "Root 'required' missing 'metadata'"
    assert "results" in schema["required"], "Root 'required' missing 'results'"

    results_schema = schema["properties"]["results"]
    assert "items" in results_schema, "Results schema missing 'items'"
    assert "required" in results_schema["items"], "Result item schema missing 'required'"
    assert "signal_id" in results_schema["items"]["required"], "Result item 'required' missing 'signal_id'"
    assert "status" in results_schema["items"]["required"], "Result item 'required' missing 'status'"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
