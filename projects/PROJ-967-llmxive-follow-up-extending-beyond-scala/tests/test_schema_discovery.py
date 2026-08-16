import pytest
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import sys
import os

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from schema_discovery import (
    discover_schema,
    validate_schema,
    REQUIRED_COLUMNS,
    RUBRIC_KEYS
)

@pytest.fixture
def mock_dataframe():
    """Create a mock dataframe matching the expected schema."""
    data = {
        "prompt": ["prompt1", "prompt2"],
        "image_url": ["url1", "url2"],
        "teacher_scores": [
            {"Alignment": 5.0, "Realism": 4.0, "Aesthetics": 3.0, "Plausibility": 4.5},
            {"Alignment": 6.0, "Realism": 5.0, "Aesthetics": 4.0, "Plausibility": 5.0}
        ],
        "student_scalar": [4.2, 5.1],
        "human_annotations": [
            {"Alignment": 4.8, "Realism": 3.9, "Aesthetics": 3.1, "Plausibility": 4.4},
            {"Alignment": 5.9, "Realism": 4.8, "Aesthetics": 3.9, "Plausibility": 4.9}
        ],
        "primary_dimension": ["Alignment", "Realism"]
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_template_schema():
    """Create a minimal template schema."""
    return {
        "schema_version": "1.0",
        "fields": [
            {"name": "prompt", "type": "string"},
            {"name": "teacher_scores", "type": "object", "properties": {}}
        ]
    }

def test_discover_schema_structure(mock_dataframe):
    """Test that discover_schema returns the correct structure."""
    schema = discover_schema(mock_dataframe)
    
    assert "schema_version" in schema
    assert "fields" in schema
    assert len(schema["fields"]) == len(mock_dataframe.columns)
    
    field_names = [f["name"] for f in schema["fields"]]
    for col in mock_dataframe.columns:
        assert col in field_names

def test_discover_schema_properties(mock_dataframe):
    """Test that object columns have properties discovered."""
    schema = discover_schema(mock_dataframe)
    
    teacher_field = next(f for f in schema["fields"] if f["name"] == "teacher_scores")
    assert "properties" in teacher_field
    for key in RUBRIC_KEYS:
        assert key in teacher_field["properties"]

def test_validate_schema_missing_critical(mock_dataframe, mock_template_schema):
    """Test validation fails on missing critical columns."""
    # Remove a critical column
    bad_df = mock_dataframe.drop(columns=["prompt"])
    bad_schema = discover_schema(bad_df)
    
    errors = validate_schema(bad_schema, mock_template_schema)
    critical_errors = [e for e in errors if e.startswith("CRITICAL")]
    
    assert len(critical_errors) > 0
    assert any("prompt" in e for e in critical_errors)

def test_validate_schema_rubric_keys(mock_dataframe, mock_template_schema):
    """Test validation checks for rubric keys."""
    # Modify dataframe to have missing rubric key
    bad_data = mock_dataframe.copy()
    bad_scores = bad_data["teacher_scores"].tolist()
    bad_scores[0] = {"Alignment": 5.0, "Realism": 4.0} # Missing Aesthetics, Plausibility
    bad_data["teacher_scores"] = bad_scores
    
    bad_schema = discover_schema(bad_data)
    errors = validate_schema(bad_schema, mock_template_schema)
    
    critical_errors = [e for e in errors if e.startswith("CRITICAL")]
    assert any("rubric keys" in e.lower() for e in critical_errors)

def test_validate_schema_pass(mock_dataframe, mock_template_schema):
    """Test validation passes with valid data."""
    schema = discover_schema(mock_dataframe)
    errors = validate_schema(schema, mock_template_schema)
    
    critical_errors = [e for e in errors if e.startswith("CRITICAL")]
    assert len(critical_errors) == 0