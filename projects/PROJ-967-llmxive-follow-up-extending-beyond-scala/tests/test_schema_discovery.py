import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from schema_discovery import (
    discover_schema,
    validate_schema,
    load_schema,
    save_schema,
    load_dataset
)

@pytest.fixture
def sample_dataframe():
    """Create a mock DataFrame matching the expected Z-Reward schema."""
    data = {
        "prompt": ["What is this?", "Describe the image."],
        "image_url": ["http://img1.jpg", "http://img2.jpg"],
        "teacher_scores": [
            json.dumps({"Alignment": 4.5, "Realism": 3.2, "Aesthetics": 4.0, "Plausibility": 3.8}),
            json.dumps({"Alignment": 2.1, "Realism": 5.0, "Aesthetics": 2.5, "Plausibility": 4.2})
        ],
        "student_scalar": [3.5, 4.0],
        "human_annotations": [
            json.dumps({"Alignment": 4.0, "Realism": 3.0, "Aesthetics": 4.5, "Plausibility": 3.5}),
            json.dumps({"Alignment": 2.0, "Realism": 4.8, "Aesthetics": 2.0, "Plausibility": 4.0})
        ],
        "primary_dimension": ["Alignment", "Realism"]
    }
    return pd.DataFrame(data)

@pytest.fixture
def provisional_schema():
    return {
        "schema_version": "1.0",
        "fields": [
            {"name": "prompt", "type": "string"},
            {"name": "teacher_scores", "type": "object", "properties": {"Alignment": "float"}}
        ]
    }

def test_discover_schema_structure(sample_dataframe):
    """Test that schema discovery correctly identifies columns and types."""
    schema = discover_schema(sample_dataframe)
    
    assert schema["schema_version"] == "1.0"
    assert len(schema["fields"]) == len(sample_dataframe.columns)
    
    field_names = {f["name"] for f in schema["fields"]}
    assert "prompt" in field_names
    assert "teacher_scores" in field_names
    assert "student_scalar" in field_names
    assert "primary_dimension" in field_names

def test_discover_schema_types(sample_dataframe):
    """Test that types are inferred correctly."""
    schema = discover_schema(sample_dataframe)
    
    type_map = {f["name"]: f["type"] for f in schema["fields"]}
    assert type_map["prompt"] == "string"
    assert type_map["student_scalar"] == "float"
    assert type_map["primary_dimension"] == "string"
    
    # Check teacher_scores is object with properties
    ts_field = next(f for f in schema["fields"] if f["name"] == "teacher_scores")
    assert ts_field["type"] == "object"
    assert "properties" in ts_field
    assert "Alignment" in ts_field["properties"]
    assert ts_field["properties"]["Alignment"]["type"] == "float"

def test_validate_schema_pass(provisional_schema, sample_dataframe):
    """Test validation when schema is correct."""
    discovered = discover_schema(sample_dataframe)
    # Create a provisional schema that matches the critical requirements
    matching_provisional = {
        "schema_version": "1.0",
        "fields": [
            {"name": "prompt", "type": "string"},
            {"name": "image_url", "type": "string"},
            {"name": "teacher_scores", "type": "object", "properties": {}},
            {"name": "student_scalar", "type": "float"},
            {"name": "human_annotations", "type": "object", "properties": {}},
            {"name": "primary_dimension", "type": "string"}
        ]
    }
    
    errors = validate_schema(discovered, matching_provisional)
    # Should have no CRITICAL errors
    critical_errors = [e for e in errors if "CRITICAL" in e]
    assert len(critical_errors) == 0

def test_validate_schema_missing_critical(provisional_schema, sample_dataframe):
    """Test validation when critical columns are missing."""
    # Create a DF missing 'prompt'
    bad_df = sample_dataframe.drop(columns=["prompt"])
    discovered = discover_schema(bad_df)
    
    matching_provisional = {
        "schema_version": "1.0",
        "fields": []
    }
    
    errors = validate_schema(discovered, matching_provisional)
    critical_errors = [e for e in errors if "CRITICAL" in e]
    assert any("prompt" in e for e in critical_errors)

def test_validate_schema_missing_dimensions(provisional_schema, sample_dataframe):
    """Test validation when rubric dimensions are missing."""
    # Modify DF to have teacher_scores missing a dimension
    bad_df = sample_dataframe.copy()
    bad_df.loc[0, "teacher_scores"] = json.dumps({"Alignment": 4.5, "Realism": 3.2}) # Missing Aesthetics, Plausibility
    
    discovered = discover_schema(bad_df)
    matching_provisional = {
        "schema_version": "1.0",
        "fields": []
    }
    
    errors = validate_schema(discovered, matching_provisional)
    critical_errors = [e for e in errors if "CRITICAL" in e]
    assert any("Aesthetics" in e or "Plausibility" in e for e in critical_errors)