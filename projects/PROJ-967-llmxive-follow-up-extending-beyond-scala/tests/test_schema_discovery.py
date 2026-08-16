import pytest
import pandas as pd
import yaml
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from schema_discovery import (
    load_schema,
    save_schema,
    load_dataset,
    discover_schema,
    validate_schema,
    update_contract
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame matching the expected schema."""
    data = {
        "prompt": ["prompt1", "prompt2"],
        "image_url": ["url1", "url2"],
        "teacher_scores": [
            {"Alignment": 0.8, "Realism": 0.7, "Aesthetics": 0.9, "Plausibility": 0.6},
            {"Alignment": 0.5, "Realism": 0.6, "Aesthetics": 0.4, "Plausibility": 0.8}
        ],
        "student_scalar": [0.75, 0.65],
        "human_annotations": [
            {"Alignment": 0.85, "Realism": 0.72, "Aesthetics": 0.88, "Plausibility": 0.65},
            {"Alignment": 0.55, "Realism": 0.62, "Aesthetics": 0.45, "Plausibility": 0.78}
        ],
        "primary_dimension": ["Alignment", "Realism"]
    }
    return pd.DataFrame(data)

@pytest.fixture
def provisional_schema_path(tmp_path):
    """Create a provisional schema file."""
    schema = {
        "schema_version": "1.0",
        "fields": [
            {"name": "prompt", "type": "string"},
            {"name": "image_url", "type": "string"},
            {
                "name": "teacher_scores",
                "type": "object",
                "properties": {
                    "Alignment": {"type": "float"},
                    "Realism": {"type": "float"},
                    "Aesthetics": {"type": "float"},
                    "Plausibility": {"type": "float"}
                }
            },
            {"name": "student_scalar", "type": "float"},
            {
                "name": "human_annotations",
                "type": "object",
                "properties": {
                    "Alignment": {"type": "float"},
                    "Realism": {"type": "float"},
                    "Aesthetics": {"type": "float"},
                    "Plausibility": {"type": "float"}
                }
            },
            {"name": "primary_dimension", "type": "string"}
        ]
    }
    path = tmp_path / "provisional_schema.yaml"
    with open(path, "w") as f:
        yaml.dump(schema, f)
    return path

@pytest.fixture
def sample_parquet_path(tmp_path, sample_dataframe):
    """Save sample DataFrame as parquet."""
    path = tmp_path / "sample_data.parquet"
    sample_dataframe.to_parquet(path)
    return path

def test_load_schema(provisional_schema_path):
    schema = load_schema(provisional_schema_path)
    assert schema["schema_version"] == "1.0"
    assert len(schema["fields"]) == 6

def test_discover_schema(sample_dataframe):
    discovered = discover_schema(sample_dataframe)
    assert discovered["row_count"] == 2
    assert discovered["column_count"] == 6
    field_names = [f["name"] for f in discovered["fields"]]
    assert "prompt" in field_names
    assert "teacher_scores" in field_names
    # Check nested properties
    ts_field = next(f for f in discovered["fields"] if f["name"] == "teacher_scores")
    assert "properties" in ts_field
    assert "Alignment" in ts_field["properties"]

def test_validate_schema_valid(sample_dataframe, provisional_schema_path):
    provisional = load_schema(provisional_schema_path)
    discovered = discover_schema(sample_dataframe)
    result = validate_schema(discovered, provisional)
    assert result["valid"] is True
    assert len(result["discrepancies"]) == 0

def test_validate_schema_missing_field(sample_dataframe, provisional_schema_path, tmp_path):
    # Create a schema with an extra required field that doesn't exist in data
    provisional = load_schema(provisional_schema_path)
    # Add a fake required field to the provisional schema
    provisional["fields"].append({"name": "missing_field", "type": "string"})
    
    # Save to a new file
    modified_path = tmp_path / "modified_provisional.yaml"
    with open(modified_path, "w") as f:
        yaml.dump(provisional, f)
    
    provisional_modified = load_schema(modified_path)
    discovered = discover_schema(sample_dataframe)
    result = validate_schema(discovered, provisional_modified)
    assert result["valid"] is False
    assert any("Missing required field: missing_field" in d for d in result["discrepancies"])

def test_update_contract(sample_dataframe, tmp_path):
    discovered = discover_schema(sample_dataframe)
    output_path = tmp_path / "validated_schema.yaml"
    update_contract(discovered, output_path)
    assert output_path.exists()
    
    # Load and verify
    with open(output_path, "r") as f:
        loaded = yaml.safe_load(f)
    assert loaded["schema_version"] == "1.0"
    assert len(loaded["fields"]) == 6

def test_load_dataset_parquet(sample_parquet_path):
    df = load_dataset(sample_parquet_path)
    assert len(df) == 2
    assert "prompt" in df.columns

def test_load_dataset_missing_file(tmp_path):
    non_existent = tmp_path / "nonexistent.parquet"
    with pytest.raises(FileNotFoundError):
        load_dataset(non_existent)

def test_schema_discovery_with_nested_objects(sample_dataframe):
    discovered = discover_schema(sample_dataframe)
    ts_field = next(f for f in discovered["fields"] if f["name"] == "teacher_scores")
    assert ts_field["type"] == "object"
    assert "properties" in ts_field
    assert ts_field["properties"]["Alignment"]["type"] == "float"
    assert ts_field["properties"]["Realism"]["type"] == "float"
    assert ts_field["properties"]["Aesthetics"]["type"] == "float"
    assert ts_field["properties"]["Plausibility"]["type"] == "float"

def test_validation_catches_missing_rubric_dimensions(tmp_path):
    # Create a dataframe missing one rubric dimension
    data = {
        "prompt": ["p1"],
        "image_url": ["u1"],
        "teacher_scores": [{"Alignment": 0.8, "Realism": 0.7}], # Missing Aesthetics, Plausibility
        "student_scalar": [0.75],
        "human_annotations": [{"Alignment": 0.85, "Realism": 0.72}],
        "primary_dimension": ["Alignment"]
    }
    df = pd.DataFrame(data)
    discovered = discover_schema(df)
    
    # Use standard provisional schema
    provisional = {
        "schema_version": "1.0",
        "fields": [
            {"name": "teacher_scores", "type": "object", "properties": {
                "Alignment": {"type": "float"}, "Realism": {"type": "float"},
                "Aesthetics": {"type": "float"}, "Plausibility": {"type": "float"}
            }},
            {"name": "human_annotations", "type": "object", "properties": {
                "Alignment": {"type": "float"}, "Realism": {"type": "float"},
                "Aesthetics": {"type": "float"}, "Plausibility": {"type": "float"}
            }}
        ]
    }
    
    result = validate_schema(discovered, provisional)
    assert result["valid"] is False
    assert any("Aesthetics" in d and "Plausibility" in d for d in result["discrepancies"])
