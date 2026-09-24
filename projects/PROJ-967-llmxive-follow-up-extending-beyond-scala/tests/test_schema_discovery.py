import pytest
import pandas as pd
import json
import yaml
import os
from pathlib import Path
import sys
import tempfile
import shutil

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from schema_discovery import (
    load_schema,
    save_schema,
    discover_schema,
    validate_schema,
    update_contract,
    load_dataset
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        "image_path": ["img1.jpg", "img2.jpg"],
        "species_id": [1, 2],
        "teacher_scores": [
            [0.8, 0.9, 0.7, 0.6],
            [0.5, 0.6, 0.7, 0.8]
        ],
        "student_scalar": [0.75, 0.65],
        "human_annotations": [
            {"dimension_1": 0.8, "dimension_2": 0.9, "dimension_3": 0.7, "dimension_4": 0.6},
            {"dimension_1": 0.5, "dimension_2": 0.6, "dimension_3": 0.7, "dimension_4": 0.8}
        ],
        "primary_dimension": [0, 1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_parquet_file(sample_dataframe, temp_dir):
    """Save sample DataFrame to a parquet file."""
    path = os.path.join(temp_dir, "test_data.parquet")
    sample_dataframe.to_parquet(path)
    return path

@pytest.fixture
def sample_contract_schema(temp_dir):
    """Create a sample contract schema."""
    schema = {
        "columns": {
            "image_path": {"type": "object"},
            "species_id": {"type": "int64"},
            "teacher_scores": {"type": "object"},
            "student_scalar": {"type": "float64"},
            "human_annotations": {"type": "object"},
            "primary_dimension": {"type": "int64"}
        }
    }
    path = os.path.join(temp_dir, "contract_schema.yaml")
    with open(path, 'w') as f:
        yaml.dump(schema, f)
    return path

def test_discover_schema(sample_dataframe):
    """Test schema discovery from a DataFrame."""
    schema = discover_schema(sample_dataframe)
    
    assert "columns" in schema
    assert len(schema["columns"]) == len(sample_dataframe.columns)
    
    for col in sample_dataframe.columns:
        assert col in schema["columns"]
        assert "type" in schema["columns"][col]
        assert "sample_values" in schema["columns"][col]

def test_validate_schema_match(temp_dir, sample_dataframe, sample_contract_schema):
    """Test validation when schemas match."""
    discovered = discover_schema(sample_dataframe)
    contract = load_schema(sample_contract_schema)
    
    result = validate_schema(discovered, contract)
    
    assert result["is_valid"]
    assert len(result["discrepancies"]) == 0
    assert len(result["missing_columns"]) == 0

def test_validate_schema_missing_columns(temp_dir, sample_dataframe, sample_contract_schema):
    """Test validation when contract has extra columns."""
    discovered = discover_schema(sample_dataframe)
    contract = load_schema(sample_contract_schema)
    
    # Add a column to contract that doesn't exist in data
    contract["columns"]["extra_column"] = {"type": "object"}
    
    result = validate_schema(discovered, contract)
    
    assert not result["is_valid"]
    assert "extra_column" in result["missing_columns"]

def test_validate_schema_extra_columns(temp_dir, sample_dataframe, sample_contract_schema):
    """Test validation when data has extra columns."""
    # Create a DataFrame with an extra column
    df_extra = sample_dataframe.copy()
    df_extra["new_column"] = [1, 2]
    
    discovered = discover_schema(df_extra)
    contract = load_schema(sample_contract_schema)
    
    result = validate_schema(discovered, contract)
    
    # Extra columns are not necessarily invalid, just logged
    assert "new_column" in result["extra_columns"]

def test_validate_schema_missing_rubric_dimensions(temp_dir, sample_dataframe, sample_contract_schema):
    """Test validation when rubric dimensions are missing."""
    # Remove dimension columns from the DataFrame
    df_no_dims = sample_dataframe.drop(columns=["human_annotations"])
    
    # Update contract to require dimension columns
    contract = load_schema(sample_contract_schema)
    contract["columns"]["dimension_1"] = {"type": "float64"}
    contract["columns"]["dimension_2"] = {"type": "float64"}
    contract["columns"]["dimension_3"] = {"type": "float64"}
    contract["columns"]["dimension_4"] = {"type": "float64"}
    
    discovered = discover_schema(df_no_dims)
    result = validate_schema(discovered, contract)
    
    assert not result["is_valid"]
    assert "dimension_1" in result["missing_columns"]

def test_update_contract_creates_new(temp_dir, sample_dataframe):
    """Test that update_contract creates a new contract if none exists."""
    discovered = discover_schema(sample_dataframe)
    new_contract_path = os.path.join(temp_dir, "new_contract.yaml")
    
    update_contract(discovered, new_contract_path, force_update=True)
    
    assert os.path.exists(new_contract_path)
    loaded = load_schema(new_contract_path)
    assert "columns" in loaded
    assert len(loaded["columns"]) == len(sample_dataframe.columns)

def test_load_dataset(sample_parquet_file):
    """Test loading a dataset from parquet file."""
    df = load_dataset(sample_parquet_file)
    
    assert isinstance(df, pd.DataFrame)
    assert not df.empty

def test_load_dataset_file_not_found():
    """Test loading a non-existent dataset raises an error."""
    with pytest.raises(FileNotFoundError):
        load_dataset("non_existent_file.parquet")

def test_save_and_load_schema(temp_dir, sample_dataframe):
    """Test saving and loading a schema."""
    discovered = discover_schema(sample_dataframe)
    schema_path = os.path.join(temp_dir, "test_schema.yaml")
    
    save_schema(discovered, schema_path)
    
    assert os.path.exists(schema_path)
    
    loaded = load_schema(schema_path)
    assert loaded == discovered
