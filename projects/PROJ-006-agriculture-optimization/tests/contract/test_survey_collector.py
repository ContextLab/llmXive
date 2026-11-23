"""
Contract tests for T015a: Survey Collector.
Validates that the output matches contracts/dataset.schema.yaml.
"""
import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config.schemas import validate_dataset_schema
from src.data.collectors.survey_collector import SurveyCollector

SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

@pytest.fixture
def collector():
    """Create a collector instance."""
    return SurveyCollector()

@pytest.fixture
def output_paths(collector):
    """Run the collector and return output paths."""
    return collector.run()

def test_raw_file_exists(output_paths):
    """Test that survey_raw.csv is created."""
    raw_path, _ = output_paths
    assert raw_path.exists(), f"Raw file {raw_path} does not exist."

def test_filtered_file_exists(output_paths):
    """Test that filtered_survey.csv is created."""
    _, filtered_path = output_paths
    assert filtered_path.exists(), f"Filtered file {filtered_path} does not exist."

def test_raw_schema_compliance(output_paths):
    """Test that raw file passes schema validation."""
    raw_path, _ = output_paths
    df = pd.read_csv(raw_path)
    
    # Load schema
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Validate
    errors = validate_dataset_schema(df, schema)
    assert len(errors) == 0, f"Schema validation failed for raw data: {errors}"

def test_filtered_schema_compliance(output_paths):
    """Test that filtered file passes schema validation."""
    _, filtered_path = output_paths
    df = pd.read_csv(filtered_path)
    
    # Load schema
    with open(SCHEMA_PATH, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Validate
    errors = validate_dataset_schema(df, schema)
    assert len(errors) == 0, f"Schema validation failed for filtered data: {errors}"

def test_coordinates_not_null(output_paths):
    """Test that filtered file has no null coordinates."""
    _, filtered_path = output_paths
    df = pd.read_csv(filtered_path)
    
    assert df['latitude'].notna().all(), "Filtered data contains null latitudes."
    assert df['longitude'].notna().all(), "Filtered data contains null longitudes."

def test_required_columns_present(output_paths):
    """Test that all required columns are present."""
    raw_path, filtered_path = output_paths
    required_cols = [
        'household_id', 'latitude', 'longitude', 'land_size', 'education_level', 
        'finance_access', 'practice_mixed_farming', 'practice_terracing', 
        'practice_conservation_tillage', 'practice_agroforestry', 'extension_visits', 
        'hlias', 'CSA_Index', 'Stability_Score', 'village_id'
    ]
    
    for path in [raw_path, filtered_path]:
        df = pd.read_csv(path)
        missing = set(required_cols) - set(df.columns)
        assert len(missing) == 0, f"Missing columns in {path}: {missing}"
