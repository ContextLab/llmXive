import pytest
import pandas as pd
import os
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def test_data_schema():
    """Test that analysis_data.csv contains exactly the required columns."""
    data_path = DATA_PROCESSED_DIR / "analysis_data.csv"
    
    assert data_path.exists(), f"Data file not found: {data_path}"
    
    df = pd.read_csv(data_path)
    
    required_columns = [
        'participant_id', 'openness', 'conscientiousness', 'extraversion',
        'agreeableness', 'neuroticism', 'receptivity_score', 'anxiety_level',
        'behavioral_intention', 'source_type'
    ]
    
    # Check that all required columns exist
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check that no extra columns exist
    extra_columns = set(df.columns) - set(required_columns)
    assert not extra_columns, f"Unexpected columns found: {extra_columns}"
    
    # Check source_type values
    assert df['source_type'].isin(['real', 'synthetic']).all(), \
        "source_type must be either 'real' or 'synthetic'"
    
    # Check for null values in required columns
    for col in required_columns:
        assert not df[col].isnull().any(), f"Null values found in column: {col}"
    
    # Check sample size
    assert len(df) >= 50, f"Sample size N={len(df)} is less than 50"

def test_source_type_distribution():
    """Test that source_type is consistently set."""
    data_path = DATA_PROCESSED_DIR / "analysis_data.csv"
    
    if not data_path.exists():
        pytest.skip("Data file not found, skipping source type test")
    
    df = pd.read_csv(data_path)
    source_types = df['source_type'].unique()
    
    assert len(source_types) == 1, f"Expected single source type, found: {source_types}"
    assert source_types[0] in ['real', 'synthetic'], f"Invalid source type: {source_types[0]}"