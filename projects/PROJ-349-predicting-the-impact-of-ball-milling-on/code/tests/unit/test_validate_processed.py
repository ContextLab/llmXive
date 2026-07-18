"""
Unit tests for the T017 dataset validation module.

Tests the validate_processed_dataset function to ensure it:
1. Correctly validates datasets against the schema
2. Raises appropriate exceptions for insufficient data
3. Handles missing files gracefully
4. Returns the validated dataframe on success
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest
import yaml

from src.utils.exceptions import InsufficientDataError, SchemaValidationError
from src.preprocess.validate import (
    validate_processed_dataset,
    run_validation_pipeline,
    MIN_ROWS,
    TARGET_ROWS
)


@pytest.fixture
def sample_schema():
    """Create a temporary schema file for testing."""
    schema = {
        "fields": [
            {"name": "experiment_id", "type": "string", "required": True},
            {"name": "source", "type": "string", "required": True},
            {"name": "material_type", "type": "string", "required": True},
            {"name": "milling_speed", "type": "float", "required": True},
            {"name": "milling_time", "type": "float", "required": True},
            {"name": "ball_to_powder_ratio", "type": "float", "required": True},
            {"name": "youngs_modulus", "type": "float", "required": True},
            {"name": "density", "type": "float", "required": True},
            {"name": "process_duration", "type": "float", "required": True},
            {"name": "d10", "type": "float", "required": True},
            {"name": "d50", "type": "float", "required": True},
            {"name": "d90", "type": "float", "required": True}
        ],
        "min_rows": MIN_ROWS
    }
    return schema


@pytest.fixture
def valid_dataframe():
    """Create a valid dataframe for testing."""
    data = {
        "experiment_id": [f"exp_{i}" for i in range(200)],
        "source": ["source_a"] * 200,
        "material_type": ["material_x"] * 200,
        "milling_speed": [300.0] * 200,
        "milling_time": [60.0] * 200,
        "ball_to_powder_ratio": [10.0] * 200,
        "youngs_modulus": [200.0] * 200,
        "density": [7.8] * 200,
        "process_duration": [120.0] * 200,
        "d10": [5.0] * 200,
        "d50": [10.0] * 200,
        "d90": [15.0] * 200
    }
    return pd.DataFrame(data)


@pytest.fixture
def small_dataframe():
    """Create a dataframe with insufficient rows for testing."""
    data = {
        "experiment_id": [f"exp_{i}" for i in range(100)],
        "source": ["source_a"] * 100,
        "material_type": ["material_x"] * 100,
        "milling_speed": [300.0] * 100,
        "milling_time": [60.0] * 100,
        "ball_to_powder_ratio": [10.0] * 100,
        "youngs_modulus": [200.0] * 100,
        "density": [7.8] * 100,
        "process_duration": [120.0] * 100,
        "d10": [5.0] * 100,
        "d50": [10.0] * 100,
        "d90": [15.0] * 100
    }
    return pd.DataFrame(data)


@pytest.fixture
def invalid_nulls_dataframe():
    """Create a dataframe with null values in required columns."""
    data = {
        "experiment_id": [f"exp_{i}" if i != 0 else None for i in range(200)],
        "source": ["source_a"] * 200,
        "material_type": ["material_x"] * 200,
        "milling_speed": [300.0] * 200,
        "milling_time": [60.0] * 200,
        "ball_to_powder_ratio": [10.0] * 200,
        "youngs_modulus": [200.0] * 200,
        "density": [7.8] * 200,
        "process_duration": [120.0] * 200,
        "d10": [5.0] * 200,
        "d50": [10.0] * 200,
        "d90": [15.0] * 200
    }
    return pd.DataFrame(data)


@pytest.fixture
def missing_column_dataframe():
    """Create a dataframe missing a required column."""
    data = {
        "experiment_id": [f"exp_{i}" for i in range(200)],
        "source": ["source_a"] * 200,
        "material_type": ["material_x"] * 200,
        "milling_speed": [300.0] * 200,
        "milling_time": [60.0] * 200,
        "ball_to_powder_ratio": [10.0] * 200,
        "youngs_modulus": [200.0] * 200,
        "density": [7.8] * 200,
        "process_duration": [120.0] * 200,
        "d10": [5.0] * 200,
        "d50": [10.0] * 200,
        # Missing d90
    }
    return pd.DataFrame(data)


def test_validate_schema_success(tmp_path, valid_dataframe, sample_schema):
    """Test successful validation of a valid dataframe."""
    # Create temporary files
    schema_file = tmp_path / "schema.yaml"
    data_file = tmp_path / "data.parquet"
    
    # Write schema
    with open(schema_file, "w") as f:
        yaml.dump(sample_schema, f)
    
    # Write data
    valid_dataframe.to_parquet(data_file)
    
    # Run validation
    result = validate_processed_dataset(
        input_path=data_file,
        schema_path=schema_file
    )
    
    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 200
    assert list(result.columns) == list(valid_dataframe.columns)


def test_validate_schema_insufficient_rows(tmp_path, small_dataframe, sample_schema):
    """Test that validation fails for insufficient rows."""
    # Create temporary files
    schema_file = tmp_path / "schema.yaml"
    data_file = tmp_path / "data.parquet"
    
    # Write schema
    with open(schema_file, "w") as f:
        yaml.dump(sample_schema, f)
    
    # Write data
    small_dataframe.to_parquet(data_file)
    
    # Run validation and expect InsufficientDataError
    with pytest.raises(InsufficientDataError):
        validate_processed_dataset(
            input_path=data_file,
            schema_path=schema_file
        )


def test_validate_schema_null_values(tmp_path, invalid_nulls_dataframe, sample_schema):
    """Test that validation fails for null values in required columns."""
    # Create temporary files
    schema_file = tmp_path / "schema.yaml"
    data_file = tmp_path / "data.parquet"
    
    # Write schema
    with open(schema_file, "w") as f:
        yaml.dump(sample_schema, f)
    
    # Write data
    invalid_nulls_dataframe.to_parquet(data_file)
    
    # Run validation and expect SchemaValidationError
    with pytest.raises(SchemaValidationError):
        validate_processed_dataset(
            input_path=data_file,
            schema_path=schema_file
        )


def test_validate_schema_missing_column(tmp_path, missing_column_dataframe, sample_schema):
    """Test that validation fails for missing required columns."""
    # Create temporary files
    schema_file = tmp_path / "schema.yaml"
    data_file = tmp_path / "data.parquet"
    
    # Write schema
    with open(schema_file, "w") as f:
        yaml.dump(sample_schema, f)
    
    # Write data
    missing_column_dataframe.to_parquet(data_file)
    
    # Run validation and expect SchemaValidationError
    with pytest.raises(SchemaValidationError):
        validate_processed_dataset(
            input_path=data_file,
            schema_path=schema_file
        )


def test_file_not_found(tmp_path):
    """Test that validation fails gracefully when input file is missing."""
    schema_file = tmp_path / "schema.yaml"
    data_file = tmp_path / "nonexistent.parquet"
    
    # Write a dummy schema
    with open(schema_file, "w") as f:
        yaml.dump({"fields": []}, f)
    
    # Run validation and expect FileNotFoundError
    with pytest.raises(FileNotFoundError):
        validate_processed_dataset(
            input_path=data_file,
            schema_path=schema_file
        )


def test_run_validation_pipeline_success(tmp_path, valid_dataframe, sample_schema):
    """Test the run_validation_pipeline function with valid data."""
    # Create temporary files
    schema_file = tmp_path / "schema.yaml"
    data_file = tmp_path / "data.parquet"
    
    # Write schema
    with open(schema_file, "w") as f:
        yaml.dump(sample_schema, f)
    
    # Write data
    valid_dataframe.to_parquet(data_file)
    
    # Run pipeline
    result = run_validation_pipeline(
        input_path=data_file,
        schema_path=schema_file
    )
    
    # Assertions
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 200


def test_run_validation_pipeline_insufficient_data(tmp_path, small_dataframe, sample_schema):
    """Test that run_validation_pipeline exits on insufficient data."""
    # Create temporary files
    schema_file = tmp_path / "schema.yaml"
    data_file = tmp_path / "data.parquet"
    
    # Write schema
    with open(schema_file, "w") as f:
        yaml.dump(sample_schema, f)
    
    # Write data
    small_dataframe.to_parquet(data_file)
    
    # Mock sys.exit to capture the exit code
    with pytest.raises(SystemExit) as exc_info:
        run_validation_pipeline(
            input_path=data_file,
            schema_path=schema_file
        )
    
    # Verify exit code is 1
    assert exc_info.value.code == 1