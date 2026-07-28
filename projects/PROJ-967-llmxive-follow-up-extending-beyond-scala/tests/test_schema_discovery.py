import os
import sys
import tempfile
import yaml
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add project code to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala" / "code"))

from schema_discovery import discover_schema, validate_schema, load_schema, save_schema

@pytest.fixture
def sample_dataframe():
    """Create a mock dataframe matching the expected Z-Reward schema."""
    data = {
        "prompt": ["What is this?", "Describe the scene"],
        "image_url": ["http://img1.jpg", "http://img2.jpg"],
        "teacher_scores": [
            {"Alignment": 0.9, "Realism": 0.8, "Aesthetics": 0.7, "Plausibility": 0.85},
            {"Alignment": 0.6, "Realism": 0.5, "Aesthetics": 0.9, "Plausibility": 0.4}
        ],
        "student_scalar": [0.82, 0.65],
        "human_annotations": [
            {"Alignment": 0.95, "Realism": 0.85, "Aesthetics": 0.75, "Plausibility": 0.9},
            {"Alignment": 0.65, "Realism": 0.55, "Aesthetics": 0.85, "Plausibility": 0.45}
        ],
        "primary_dimension": ["Alignment", "Realism"],
        "sample_id": ["id_001", "id_002"],
        "excluded_reason": [None, None]
    }
    return pd.DataFrame(data)

@pytest.fixture
def template_schema_path(tmp_path):
    """Create a temporary template schema file."""
    schema_content = {
        "schema": {
            "fields": [
                {"name": "prompt", "type": "string"},
                {"name": "teacher_scores", "type": "object"}
            ]
        }
    }
    path = tmp_path / "template.schema.yaml"
    with open(path, "w") as f:
        yaml.dump(schema_content, f)
    return path

def test_discover_schema_valid(sample_dataframe):
    """Test schema discovery on valid data."""
    template = {"schema": {"fields": []}}
    result = discover_schema(sample_dataframe, template)

    assert result["validation_status"] == "PASSED"
    assert "prompt" in result["critical_columns_found"]
    assert "teacher_scores" in result["critical_columns_found"]
    assert "student_scalar" in result["critical_columns_found"]
    assert "human_annotations" in result["critical_columns_found"]
    assert "primary_dimension" in result["critical_columns_found"]

    # Check field mapping
    fields = {f["logical_field"]: f for f in result["schema"]["fields"]}
    assert fields["prompt"]["source_column"] == "prompt"
    assert fields["teacher_scores"]["dimensions"] == ["Alignment", "Realism", "Aesthetics", "Plausibility"]

def test_discover_schema_missing_critical(sample_dataframe):
    """Test schema discovery when a critical column is missing."""
    # Drop a critical column
    df_missing = sample_dataframe.drop(columns=["primary_dimension"])
    template = {"schema": {"fields": []}}
    result = discover_schema(df_missing, template)

    assert result["validation_status"] == "FAILED"
    assert "primary_dimension" not in result["critical_columns_found"]

def test_validate_schema_valid():
    """Test validation function on a valid schema dict."""
    valid_schema = {
        "validation_status": "PASSED",
        "critical_columns_found": ["prompt", "teacher_scores", "student_scalar", "human_annotations", "primary_dimension"]
    }
    assert validate_schema(valid_schema) is True

def test_validate_schema_invalid():
    """Test validation function on an invalid schema dict."""
    invalid_schema = {
        "validation_status": "FAILED",
        "critical_columns_found": ["prompt"]
    }
    assert validate_schema(invalid_schema) is False

def test_save_and_load_schema(tmp_path):
    """Test saving and loading schema YAML."""
    schema = {
        "schema": {"fields": [{"name": "test", "type": "string"}]},
        "validation_status": "PASSED"
    }
    output_path = tmp_path / "test_schema.yaml"
    
    save_schema(schema, output_path)
    
    assert output_path.exists()
    loaded = load_schema(output_path)
    assert loaded["validation_status"] == "PASSED"
    assert loaded["schema"]["fields"][0]["name"] == "test"

def test_schema_dimensions_detection(sample_dataframe):
    """Ensure dimensions are correctly detected in teacher_scores."""
    template = {"schema": {"fields": []}}
    result = discover_schema(sample_dataframe, template)
    
    ts_field = next(f for f in result["schema"]["fields"] if f["logical_field"] == "teacher_scores")
    assert "dimensions" in ts_field
    assert len(ts_field["dimensions"]) == 4
    assert "Alignment" in ts_field["dimensions"]
