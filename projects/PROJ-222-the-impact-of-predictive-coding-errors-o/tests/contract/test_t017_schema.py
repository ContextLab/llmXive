import os
import pytest
import pandas as pd
from pathlib import Path

from config import get_processed_dir

def test_t017_output_exists():
    """Test that T017 output file exists."""
    processed_dir = get_processed_dir()
    output_path = processed_dir / "standardized.csv"
    assert output_path.exists(), f"Output file {output_path} does not exist."

def test_t017_output_schema():
    """Test that T017 output has the correct schema."""
    processed_dir = get_processed_dir()
    output_path = processed_dir / "standardized.csv"
    
    if not output_path.exists():
        pytest.skip(f"Output file {output_path} does not exist.")
    
    df = pd.read_csv(output_path)
    
    required_columns = [
        'duration_estimate',
        'stimulus_sequence',
        'participant_id',
        'surprisal'
    ]
    
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check row count
    assert len(df) >= 100, f"Output file has {len(df)} rows, expected at least 100."

def test_t017_output_data_types():
    """Test that T017 output has correct data types."""
    processed_dir = get_processed_dir()
    output_path = processed_dir / "standardized.csv"
    
    if not output_path.exists():
        pytest.skip(f"Output file {output_path} does not exist.")
    
    df = pd.read_csv(output_path)
    
    # Check data types
    assert pd.api.types.is_numeric_dtype(df['duration_estimate']), \
        "duration_estimate must be numeric"
    assert pd.api.types.is_numeric_dtype(df['surprisal']), \
        "surprisal must be numeric"
    assert df['stimulus_sequence'].dtype == 'object' or df['stimulus_sequence'].dtype.name.startswith('category'), \
        "stimulus_sequence must be string or category"
    assert df['participant_id'].dtype == 'object' or df['participant_id'].dtype.name.startswith('category'), \
        "participant_id must be string or category"