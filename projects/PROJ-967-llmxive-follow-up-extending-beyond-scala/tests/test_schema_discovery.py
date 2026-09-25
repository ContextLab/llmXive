import pytest
import json
import yaml
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, 'code')

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
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_df():
    data = {
        "image_path": ["img1.jpg", "img2.jpg"],
        "species_id": [1, 2],
        "prompt_text": ["prompt A", "prompt B"],
        "teacher_scores": [[0.5, 0.6, 0.7, 0.8], [0.4, 0.5, 0.6, 0.7]],
        "student_scalar": [0.55, 0.52],
        "human_annotations": [0.6, 0.58],
        "primary_dimension": [0, 1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_contract():
    return {
        "required_columns": ["image_path", "species_id", "prompt_text", "teacher_scores", "student_scalar", "human_annotations"],
        "rubric_dimensions": ["dimension_1", "dimension_2", "dimension_3", "dimension_4"],
        "columns": [
            {"name": "image_path", "dtype": "object"},
            {"name": "species_id", "dtype": "int64"},
            {"name": "prompt_text", "dtype": "object"},
            {"name": "teacher_scores", "dtype": "object"},
            {"name": "student_scalar", "dtype": "float64"},
            {"name": "human_annotations", "dtype": "float64"},
            {"name": "primary_dimension", "dtype": "int64"}
        ]
    }

def test_discover_schema(temp_dir, sample_df):
    schema_file = temp_dir / "schema.yaml"
    sample_df.to_parquet(schema_file)
    df = load_dataset(schema_file)
    discovered = discover_schema(df)
    assert len(discovered["columns"]) == 7
    assert any(c["name"] == "image_path" for c in discovered["columns"])
    assert any(c["name"] == "student_scalar" for c in discovered["columns"])

def test_validate_schema_no_discrepancies(temp_dir, sample_df, sample_contract):
    schema_file = temp_dir / "schema.yaml"
    sample_df.to_parquet(schema_file)
    df = load_dataset(schema_file)
    discovered = discover_schema(df)
    discrepancies = validate_schema(discovered, sample_contract)
    # No discrepancies expected as all required columns are present
    assert len([d for d in discrepancies if "Missing" in d]) == 0

def test_validate_schema_missing_column(temp_dir, sample_df, sample_contract):
    # Remove a required column from the contract temporarily to test detection
    modified_contract = sample_contract.copy()
    modified_contract["required_columns"] = modified_contract["required_columns"] + ["missing_column"]
    schema_file = temp_dir / "schema.yaml"
    sample_df.to_parquet(schema_file)
    df = load_dataset(schema_file)
    discovered = discover_schema(df)
    discrepancies = validate_schema(discovered, modified_contract)
    assert any("Missing required column: missing_column" in d for d in discrepancies)

def test_update_contract(temp_dir, sample_df, sample_contract):
    schema_file = temp_dir / "schema.yaml"
    sample_df.to_parquet(schema_file)
    df = load_dataset(schema_file)
    discovered = discover_schema(df)
    updated = update_contract(sample_contract, discovered, type('Logger', (), {'info': lambda s, m: None, 'warning': lambda s, m: None})())
    assert len(updated["columns"]) >= len(sample_contract["columns"])
    assert any(c["name"] == "image_path" for c in updated["columns"])

def test_load_dataset_missing_file(temp_dir):
    with pytest.raises(FileNotFoundError):
        load_dataset(temp_dir / "nonexistent.parquet")

def test_load_schema_missing_file(temp_dir):
    with pytest.raises(FileNotFoundError):
        load_schema(temp_dir / "nonexistent.yaml")
