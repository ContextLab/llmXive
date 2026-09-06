import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.schema_discovery import (
    discover_schema,
    validate_schema,
    load_schema,
    save_schema,
    validate_dataset,
    RUBRIC_DIMENSIONS
)


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe matching the expected schema."""
    data = {
        "prompt": ["prompt1", "prompt2", "prompt3"],
        "image_url": ["url1", "url2", "url3"],
        "teacher_scores": [
            {"Alignment": 4.5, "Realism": 3.2, "Aesthetics": 4.0, "Plausibility": 3.8},
            {"Alignment": 3.9, "Realism": 4.1, "Aesthetics": 3.5, "Plausibility": 4.2},
            {"Alignment": 4.2, "Realism": 3.8, "Aesthetics": 4.1, "Plausibility": 3.9}
        ],
        "student_scalar": [3.5, 4.0, 3.8],
        "human_annotations": [
            {"Alignment": 4.0, "Realism": 3.5, "Aesthetics": 3.8, "Plausibility": 3.6},
            {"Alignment": 3.7, "Realism": 3.9, "Aesthetics": 3.2, "Plausibility": 4.0},
            {"Alignment": 4.1, "Realism": 3.6, "Aesthetics": 4.0, "Plausibility": 3.7}
        ],
        "primary_dimension": ["Alignment", "Realism", "Aesthetics"]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_template_schema():
    """Create a sample template schema."""
    return {
        "schema_version": "1.0",
        "fields": [
            {"name": "prompt", "type": "string"},
            {"name": "image_url", "type": "string"},
            {
                "name": "teacher_scores",
                "type": "object",
                "properties": {
                    "Alignment": "float",
                    "Realism": "float",
                    "Aesthetics": "float",
                    "Plausibility": "float"
                }
            },
            {"name": "student_scalar", "type": "float"},
            {
                "name": "human_annotations",
                "type": "object",
                "properties": {
                    "Alignment": "float",
                    "Realism": "float",
                    "Aesthetics": "float",
                    "Plausibility": "float"
                }
            },
            {"name": "primary_dimension", "type": "string"}
        ]
    }


def test_discover_schema(sample_dataframe):
    """Test schema discovery from a dataframe."""
    discovered = discover_schema(sample_dataframe)
    
    assert "schema_version" in discovered
    assert "fields" in discovered
    assert len(discovered["fields"]) == len(sample_dataframe.columns)
    
    # Check that all columns are discovered
    field_names = [f["name"] for f in discovered["fields"]]
    for col in sample_dataframe.columns:
        assert col in field_names


def test_validate_schema_valid(sample_dataframe, sample_template_schema):
    """Test validation with a valid schema."""
    discovered = discover_schema(sample_dataframe)
    result = validate_schema(discovered, sample_template_schema)
    
    assert result["is_valid"] is True
    assert len(result["missing_fields"]) == 0
    assert len(result["type_mismatches"]) == 0


def test_validate_schema_missing_field(sample_dataframe, sample_template_schema):
    """Test validation with a missing field."""
    # Remove a field from the dataframe
    df_modified = sample_dataframe.drop(columns=["primary_dimension"])
    discovered = discover_schema(df_modified)
    result = validate_schema(discovered, sample_template_schema)
    
    assert result["is_valid"] is False
    assert "primary_dimension" in result["missing_fields"]


def test_validate_schema_extra_fields(sample_dataframe, sample_template_schema):
    """Test validation with extra fields (should be allowed)."""
    # Add an extra column
    df_modified = sample_dataframe.copy()
    df_modified["extra_field"] = ["value1", "value2", "value3"]
    
    discovered = discover_schema(df_modified)
    result = validate_schema(discovered, sample_template_schema)
    
    # Extra fields are not an error, just logged
    assert result["is_valid"] is True
    assert "extra_field" in result.get("extra_fields", [])


def test_rubric_dimensions_present(sample_dataframe, sample_template_schema):
    """Test that rubric dimensions are detected in teacher_scores."""
    discovered = discover_schema(sample_dataframe)
    
    # Find teacher_scores field
    teacher_scores_field = None
    for field in discovered["fields"]:
        if field["name"] == "teacher_scores":
            teacher_scores_field = field
            break
    
    assert teacher_scores_field is not None
    assert teacher_scores_field.get("type") == "object"
    
    # Check that all rubric dimensions are present
    properties = teacher_scores_field.get("properties", [])
    for dim in RUBRIC_DIMENSIONS:
        assert dim in properties, f"Missing rubric dimension: {dim}"


def test_human_annotations_dimensions(sample_dataframe, sample_template_schema):
    """Test that human annotations dimensions are detected."""
    discovered = discover_schema(sample_dataframe)
    
    # Find human_annotations field
    ha_field = None
    for field in discovered["fields"]:
        if field["name"] == "human_annotations":
            ha_field = field
            break
    
    assert ha_field is not None
    assert ha_field.get("type") == "object"
    
    # Check that all rubric dimensions are present
    properties = ha_field.get("properties", [])
    for dim in RUBRIC_DIMENSIONS:
        assert dim in properties, f"Missing rubric dimension in human_annotations: {dim}"
