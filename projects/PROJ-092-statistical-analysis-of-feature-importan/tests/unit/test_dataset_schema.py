"""
Unit tests for dataset schema validation and utilities.
"""
import pytest
from pathlib import Path
from contracts.dataset import DatasetSchema, DataSource, WindowMetadata

def test_dataset_schema_valid():
    """Test creating a valid DatasetSchema."""
    schema = DatasetSchema(
        source=DataSource.CUSTOM_CSV,
        raw_path=Path("/data/raw/test.csv"),
        processed_path=Path("/data/processed/test.csv"),
        columns=['timestamp', 'feature1', 'feature2', 'load'],
        target_column='load',
        timestamp_column='timestamp'
    )

    assert schema.source == DataSource.CUSTOM_CSV
    assert schema.target_column == 'load'

def test_dataset_schema_invalid_target():
    """Test that invalid target column raises error."""
    with pytest.raises(ValueError):
        DatasetSchema(
            source=DataSource.CUSTOM_CSV,
            raw_path=Path("/data/raw/test.csv"),
            processed_path=Path("/data/processed/test.csv"),
            columns=['timestamp', 'feature1'],
            target_column='load'  # Not in columns
        )

def test_dataset_schema_invalid_window_size():
    """Test that invalid window size raises error."""
    with pytest.raises(ValueError):
        DatasetSchema(
            source=DataSource.CUSTOM_CSV,
            raw_path=Path("/data/raw/test.csv"),
            processed_path=Path("/data/processed/test.csv"),
            columns=['timestamp', 'feature1', 'load'],
            target_column='load',
            window_size_days=-1
        )

def test_get_feature_list_default():
    """Test default feature list generation."""
    schema = DatasetSchema(
        source=DataSource.CUSTOM_CSV,
        raw_path=Path("/data/raw/test.csv"),
        processed_path=Path("/data/processed/test.csv"),
        columns=['timestamp', 'feature1', 'feature2', 'load'],
        target_column='load',
        timestamp_column='timestamp'
    )

    features = schema.get_feature_list()
    assert features == ['feature1', 'feature2']

def test_get_feature_list_explicit():
    """Test explicit feature list override."""
    schema = DatasetSchema(
        source=DataSource.CUSTOM_CSV,
        raw_path=Path("/data/raw/test.csv"),
        processed_path=Path("/data/processed/test.csv"),
        columns=['timestamp', 'feature1', 'feature2', 'load'],
        target_column='load',
        timestamp_column='timestamp',
        feature_columns=['feature1']
    )

    features = schema.get_feature_list()
    assert features == ['feature1']
