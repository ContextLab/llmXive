import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
import tempfile
from pathlib import Path
import yaml

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala" / "code"))

from schema_discovery import discover_schema, validate_schema, load_schema, save_schema

def test_discover_schema_basic():
    """Test basic schema discovery on a simple DataFrame."""
    data = {
        "prompt": ["text1", "text2"],
        "image_url": ["url1", "url2"],
        "student_scalar": [1.0, 2.0]
    }
    df = pd.DataFrame(data)
    schema = discover_schema(df)
    
    assert schema["schema_version"] == "1.0"
    assert len(schema["fields"]) == 3
    
    field_names = [f["name"] for f in schema["fields"]]
    assert "prompt" in field_names
    assert "image_url" in field_names
    assert "student_scalar" in field_names

def test_discover_schema_nested():
    """Test schema discovery on a DataFrame with nested dictionary columns."""
    data = {
        "prompt": ["text1"],
        "teacher_scores": [
            {"Alignment": 0.9, "Realism": 0.8, "Aesthetics": 0.7, "Plausibility": 0.6}
        ]
    }
    df = pd.DataFrame(data)
    schema = discover_schema(df)
    
    teacher_field = next((f for f in schema["fields"] if f["name"] == "teacher_scores"), None)
    assert teacher_field is not None
    assert teacher_field["type"] == "object"
    assert "properties" in teacher_field
    assert "Alignment" in teacher_field["properties"]
    assert "Realism" in teacher_field["properties"]

def test_validate_schema_match():
    """Test validation when discovered schema matches provisional."""
    provisional = {
        "schema_version": "1.0",
        "fields": [
            {"name": "prompt", "type": "object"}, # Simplified type check
            {"name": "teacher_scores", "type": "object", "properties": {"Alignment": "float"}}
        ]
    }
    discovered = {
        "schema_version": "1.0",
        "fields": [
            {"name": "prompt", "type": "object"},
            {"name": "teacher_scores", "type": "object", "properties": {"Alignment": "float"}}
        ]
    }
    
    discrepancies = validate_schema(discovered, provisional)
    assert len(discrepancies) == 0

def test_validate_schema_missing_field():
    """Test validation when a required field is missing."""
    provisional = {
        "schema_version": "1.0",
        "fields": [
            {"name": "prompt", "type": "string"},
            {"name": "required_field", "type": "string"}
        ]
    }
    discovered = {
        "schema_version": "1.0",
        "fields": [
            {"name": "prompt", "type": "string"}
        ]
    }
    
    discrepancies = validate_schema(discovered, provisional)
    assert len(discrepancies) == 1
    assert "Missing required field: required_field" in discrepancies

def test_validate_schema_missing_properties():
    """Test validation when object properties are missing."""
    provisional = {
        "schema_version": "1.0",
        "fields": [
            {
                "name": "teacher_scores", 
                "type": "object", 
                "properties": {"Alignment": "float", "Realism": "float"}
            }
        ]
    }
    discovered = {
        "schema_version": "1.0",
        "fields": [
            {
                "name": "teacher_scores", 
                "type": "object", 
                "properties": {"Alignment": "float"}
            }
        ]
    }
    
    discrepancies = validate_schema(discovered, provisional)
    assert len(discrepancies) == 1
    assert "Missing property 'Realism'" in discrepancies[0]

def test_save_and_load_schema(tmp_path):
    """Test saving and loading a schema to/from file."""
    schema = {
        "schema_version": "1.0",
        "fields": [{"name": "test", "type": "string"}]
    }
    file_path = tmp_path / "test_schema.yaml"
    
    save_schema(schema, str(file_path))
    assert file_path.exists()
    
    loaded = load_schema(str(file_path))
    assert loaded == schema