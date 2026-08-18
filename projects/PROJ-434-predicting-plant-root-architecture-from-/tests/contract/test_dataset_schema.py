"""
Contract test for the merged dataset schema.
"""
import pytest
import pandas as pd
from pathlib import Path

def test_merged_dataset_schema():
    """Verify that the merged dataset has the required columns and types."""
    data_path = Path("data/processed/merged_dataset.csv")
    if not data_path.exists():
        pytest.skip("Dataset not generated yet")
    
    df = pd.read_csv(data_path)
    
    required_columns = ['species_name', 'latitude', 'longitude', 'root_depth', 'soil_n', 'soil_p', 'soil_k', 'soil_ph']
    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"
    
    # Check for non-null values in critical columns
    assert df['root_depth'].notnull().all(), "root_depth contains null values"
    assert df['soil_n'].notnull().all(), "soil_n contains null values"
    assert df['soil_p'].notnull().all(), "soil_p contains null values"
    assert df['soil_k'].notnull().all(), "soil_k contains null values"
    assert df['soil_ph'].notnull().all(), "soil_ph contains null values"

def test_excluded_species_summary_schema():
    """Verify the schema of the excluded species summary."""
    data_path = Path("data/processed/excluded_species_summary.csv")
    if not data_path.exists():
        pytest.skip("Excluded species summary not generated yet")
    
    df = pd.read_csv(data_path)
    assert 'species_name' in df.columns
    assert 'observation_count' in df.columns
    assert 'reason' in df.columns
