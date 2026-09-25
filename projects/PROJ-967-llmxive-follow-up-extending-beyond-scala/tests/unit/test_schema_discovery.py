import pytest
import pandas as pd
import pyarrow.parquet as pq
import yaml
import json
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from schema_discovery import (
    load_schema,
    save_schema,
    load_dataset,
    discover_schema,
    validate_schema,
    update_contract
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def sample_dataframe():
    data = {
        "image_path": ["img1.jpg", "img2.jpg"],
        "species_id": [1, 2],
        "prompt_text": ["prompt A", "prompt B"],
        "teacher_scores": [[0.5, 0.6, 0.7, 0.8], [0.1, 0.2, 0.3, 0.4]],
        "student_scalar": [0.55, 0.25],
        "human_annotations": [0.6, 0.3],
        "primary_dimension": [0, 1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_provisional_schema():
    return {
        "fields": [
            {"name": "image_path", "type": "object"},
            {"name": "species_id", "type": "int64"},
            {"name": "prompt_text", "type": "object"},
            {"name": "teacher_scores", "type": "object"},
            {"name": "student_scalar", "type": "float64"},
            {"name": "human_annotations", "type": "float64"},
            {"name": "primary_dimension", "type": "int64"}
        ]
    }

@pytest.fixture
def sample_schema_with_rubric_dims():
    # Schema expecting specific rubric columns that might be missing
    return {
        "fields": [
            {"name": "image_path", "type": "object"},
            {"name": "rubric_0", "type": "float64"}, # Expected but not in DF
            {"name": "rubric_1", "type": "float64"},
            {"name": "rubric_2", "type": "float64"},
            {"name": "rubric_3", "type": "float64"}
        ]
    }

def test_load_schema(temp_dir, sample_provisional_schema):
    schema_path = temp_dir / "schema.yaml"
    with open(schema_path, 'w') as f:
        yaml.dump(sample_provisional_schema, f)
    
    loaded = load_schema(schema_path, None)
    assert loaded == sample_provisional_schema

def test_save_schema(temp_dir, sample_provisional_schema):
    schema_path = temp_dir / "schema_out.yaml"
    save_schema(sample_provisional_schema, schema_path, None)
    assert schema_path.exists()
    
    with open(schema_path, 'r') as f:
        loaded = yaml.safe_load(f)
    assert loaded == sample_provisional_schema

def test_load_dataset(temp_dir, sample_dataframe):
    data_path = temp_dir / "data.parquet"
    sample_dataframe.to_parquet(data_path)
    
    loaded_df = load_dataset(data_path, None)
    assert len(loaded_df) == 2
    assert list(loaded_df.columns) == list(sample_dataframe.columns)

def test_discover_schema(temp_dir, sample_dataframe):
    schema = discover_schema(sample_dataframe, None)
    assert "fields" in schema
    assert len(schema["fields"]) == len(sample_dataframe.columns)
    
    field_names = [f["name"] for f in schema["fields"]]
    assert "image_path" in field_names
    assert "teacher_scores" in field_names

def test_validate_schema_match(temp_dir, sample_dataframe, sample_provisional_schema):
    discovered = discover_schema(sample_dataframe, None)
    is_valid, discrepancies, missing_rubric = validate_schema(discovered, sample_provisional_schema, None)
    
    assert is_valid is True
    assert len(discrepancies) == 0
    assert len(missing_rubric) == 0

def test_validate_schema_mismatch(temp_dir, sample_dataframe, sample_provisional_schema):
    # Modify provisional to expect a column that doesn't exist
    bad_schema = sample_provisional_schema.copy()
    bad_schema["fields"].append({"name": "nonexistent_col", "type": "int64"})
    
    discovered = discover_schema(sample_dataframe, None)
    is_valid, discrepancies, missing_rubric = validate_schema(discovered, bad_schema, None)
    
    assert is_valid is False
    assert len(discrepancies) > 0
    assert any("nonexistent_col" in d for d in discrepancies)

def test_validate_missing_rubric_dims(temp_dir, sample_dataframe, sample_schema_with_rubric_dims):
    discovered = discover_schema(sample_dataframe, None)
    is_valid, discrepancies, missing_rubric = validate_schema(discovered, sample_schema_with_rubric_dims, None)
    
    assert is_valid is False
    assert len(missing_rubric) > 0
    assert "rubric_0" in missing_rubric

def test_update_contract(temp_dir, sample_dataframe, sample_provisional_schema):
    schema_path = temp_dir / "schema.yaml"
    # Save initial (provisional)
    with open(schema_path, 'w') as f:
        yaml.dump(sample_provisional_schema, f)
    
    # Discover a new schema (simulating a change)
    discovered = discover_schema(sample_dataframe, None)
    # Add a new field to discovered to simulate change
    discovered["fields"].append({"name": "new_field", "type": "string"})
    
    update_contract(discovered, schema_path, None)
    
    # Verify file was updated
    with open(schema_path, 'r') as f:
        updated_schema = yaml.safe_load(f)
    
    assert len(updated_schema["fields"]) == len(discovered["fields"])
    assert any(f["name"] == "new_field" for f in updated_schema["fields"])