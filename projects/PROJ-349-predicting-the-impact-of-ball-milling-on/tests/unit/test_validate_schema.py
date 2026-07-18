"""
Unit tests for the dataset schema validation logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import yaml

from src.utils.validate_schema import validate_schema, load_schema, validate_dataframe_size
from src.exceptions import SchemaValidationError, InsufficientDataError, DataFormatError


@pytest.fixture
def valid_data():
    """Create a minimal valid dataset with >150 rows."""
    data = {
        'experiment_id': [f"exp_{i}" for i in range(200)],
        'source': ['NIST'] * 200,
        'material_type': ['Aluminum'] * 200,
        'milling_speed': [300.0] * 200,
        'milling_time': [2.0] * 200,
        'ball_to_powder_ratio': [10.0] * 200,
        'youngs_modulus': [70.0] * 200,
        'density': [2.7] * 200,
        'd10': [1.0] * 200,
        'd50': [5.0] * 200,
        'd90': [10.0] * 200,
        'process_duration': [2.0] * 200
    }
    return pd.DataFrame(data)


@pytest.fixture
def small_data():
    """Create a dataset with <150 rows."""
    data = {
        'experiment_id': [f"exp_{i}" for i in range(100)],
        'source': ['NIST'] * 100,
        'material_type': ['Aluminum'] * 100,
        'milling_speed': [300.0] * 100,
        'milling_time': [2.0] * 100,
        'ball_to_powder_ratio': [10.0] * 100,
        'youngs_modulus': [70.0] * 100,
        'density': [2.7] * 100,
        'd10': [1.0] * 100,
        'd50': [5.0] * 100,
        'd90': [10.0] * 100,
        'process_duration': [2.0] * 100
    }
    return pd.DataFrame(data)


@pytest.fixture
def invalid_columns_data():
    """Create data missing required columns."""
    data = {
        'experiment_id': [f"exp_{i}" for i in range(200)],
        'source': ['NIST'] * 200,
        # Missing 'material_type'
        'milling_speed': [300.0] * 200,
    }
    return pd.DataFrame(data)


def test_validate_schema_success(valid_data):
    """Test that valid data passes validation."""
    result = validate_schema(valid_data)
    assert result is not None
    assert len(result) == 200


def test_validate_schema_insufficient_rows(small_data):
    """Test that data with <150 rows raises InsufficientDataError."""
    with pytest.raises(InsufficientDataError) as exc_info:
        validate_schema(small_data)
    
    assert "below minimum viable threshold" in str(exc_info.value)
    assert exc_info.value.current_count == 100


def test_validate_schema_missing_columns(invalid_columns_data):
    """Test that missing required columns raise SchemaValidationError."""
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_schema(invalid_columns_data)
    
    assert "Missing required columns" in str(exc_info.value)
    assert "material_type" in str(exc_info.value)


def test_validate_schema_invalid_type():
    """Test that invalid types raise SchemaValidationError."""
    data = {
        'experiment_id': [f"exp_{i}" for i in range(200)],
        'source': ['NIST'] * 200,
        'material_type': ['Aluminum'] * 200,
        'milling_speed': ['fast'] * 200,  # String instead of number
        'milling_time': [2.0] * 200,
        'ball_to_powder_ratio': [10.0] * 200,
        'youngs_modulus': [70.0] * 200,
        'density': [2.7] * 200,
        'd10': [1.0] * 200,
        'd50': [5.0] * 200,
        'd90': [10.0] * 200,
        'process_duration': [2.0] * 200
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_schema(df)
    
    assert "must be numeric" in str(exc_info.value)


def test_validate_schema_negative_values():
    """Test that negative values in numeric fields raise error."""
    data = {
        'experiment_id': [f"exp_{i}" for i in range(200)],
        'source': ['NIST'] * 200,
        'material_type': ['Aluminum'] * 200,
        'milling_speed': [-100.0] * 200,  # Negative speed
        'milling_time': [2.0] * 200,
        'ball_to_powder_ratio': [10.0] * 200,
        'youngs_modulus': [70.0] * 200,
        'density': [2.7] * 200,
        'd10': [1.0] * 200,
        'd50': [5.0] * 200,
        'd90': [10.0] * 200,
        'process_duration': [2.0] * 200
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_schema(df)
    
    assert "below minimum" in str(exc_info.value)


def test_validate_dataframe_size_success(valid_data):
    """Test standalone size check passes."""
    validate_dataframe_size(valid_data, min_rows=150)  # Should not raise


def test_validate_dataframe_size_failure(small_data):
    """Test standalone size check fails."""
    with pytest.raises(InsufficientDataError):
        validate_dataframe_size(small_data, min_rows=150)