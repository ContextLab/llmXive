"""
Tests for the synthetic data generator (T008).
"""

import os
import tempfile
import pandas as pd
import pytest

# Import the function to test
from code.synthetic_data import generate_synthetic_data, _generate_personality_scores, _generate_demographics, _generate_listening_data

REQUIRED_COLUMNS = [
    "age", "gender", "country",
    "extraversion", "agreeableness", "conscientiousness",
    "emotional_stability", "open_mindedness",
    "user_id", "raw_genres", "listening_minutes"
]

def test_generation_creates_file():
    """Test that the generator creates a file at the specified path."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Override default output path for test
        df = generate_synthetic_data(output_path=tmp_path)
        
        assert os.path.exists(tmp_path), "Output file was not created"
        loaded_df = pd.read_csv(tmp_path)
        
        # Check shape
        assert loaded_df.shape[0] > 0, "Dataset is empty"
        assert loaded_df.shape[1] == len(REQUIRED_COLUMNS), f"Expected {len(REQUIRED_COLUMNS)} columns, got {loaded_df.shape[1]}"
        
        # Check columns
        for col in REQUIRED_COLUMNS:
            assert col in loaded_df.columns, f"Missing required column: {col}"
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_deterministic_seed():
    """Test that running with the same seed produces identical results."""
    # We test the internal helper functions for determinism since
    # the main function uses a global seed constant
    df1 = _generate_personality_scores(10, seed=42)
    df2 = _generate_personality_scores(10, seed=42)
    
    pd.testing.assert_frame_equal(df1, df2)

def test_data_ranges():
    """Test that generated data falls within expected ranges."""
    df = _generate_personality_scores(100, seed=42)
    
    for col in df.columns:
        assert df[col].min() >= 1, f"Min value for {col} is < 1"
        assert df[col].max() <= 5, f"Max value for {col} is > 5"

def test_demographics_valid_values():
    """Test that demographics contain valid values."""
    df = _generate_demographics(100, seed=42)
    
    assert all(df["age"] >= 18), "Age should be >= 18"
    assert all(df["age"] <= 70), "Age should be <= 70"
    
    valid_genders = {"M", "F", "NB", "Other"}
    assert df["gender"].isin(valid_genders).all(), "Invalid gender value found"
    
    valid_countries = {"US", "UK", "DE", "FR", "JP", "BR", "IN", "CA", "AU", "KR"}
    assert df["country"].isin(valid_countries).all(), "Invalid country value found"
