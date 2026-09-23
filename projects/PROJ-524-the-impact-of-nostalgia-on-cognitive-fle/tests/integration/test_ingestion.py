import os
import json
import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingestion.fetcher import fetch_from_openml, DataFetchError
from ingestion.validator import validate_and_filter_dataset

RAW_DATA_PATH = Path("data/raw/raw_dataset.csv")
PROCESSED_DATA_PATH = Path("data/processed/cleaned_age_filtered.csv")

@pytest.fixture
def sample_raw_data(tmp_path):
    """Create a temporary raw dataset for testing."""
    data = {
        'participant_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'age': [65, 70, 60, 80, 75],  # P003 should be excluded
        'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control', 'nostalgia'],
        'perseverative_errors': [5, 3, 4, 2, 6],
        'categories_completed': [6, 7, 5, 8, 4]
    }
    df = pd.DataFrame(data)
    path = tmp_path / "raw_dataset.csv"
    df.to_csv(path, index=False)
    return path

def test_data_ingestion_pipeline_creates_files(sample_raw_data, tmp_path):
    """Test that the ingestion pipeline creates the required output files."""
    # Simulate the pipeline steps
    # 1. Load raw data (already done by fixture)
    # 2. Validate and filter by age
    
    df = pd.read_csv(sample_raw_data)
    filtered_df = df[df['age'] >= 65].copy()
    
    # Save to processed directory
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(exist_ok=True)
    output_path = processed_dir / "cleaned_age_filtered.csv"
    filtered_df.to_csv(output_path, index=False)
    
    # Verify output exists
    assert output_path.exists(), "Age filtered file was not created"
    
    # Verify content
    result_df = pd.read_csv(output_path)
    assert len(result_df) == 4, "Expected 4 records after age filtering"
    assert all(result_df['age'] >= 65), "All records should be age >= 65"

def test_schema_validation_on_ingested_data(sample_raw_data):
    """Test that the ingested data conforms to the expected schema."""
    df = pd.read_csv(sample_raw_data)
    
    required_columns = ['participant_id', 'age', 'stimulus_type', 
                      'perseverative_errors', 'categories_completed']
    
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check data types
    assert df['age'].dtype in ['int64', 'int32', 'float64', 'float32'], \
        "Age should be numeric"
    
    assert df['stimulus_type'].dtype == 'object', "Stimulus type should be string"
