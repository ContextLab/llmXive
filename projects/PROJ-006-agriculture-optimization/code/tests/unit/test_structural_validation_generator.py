"""
Unit tests for structural_validation_generator.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the generator class
from src.data.generators.structural_validation_generator import StructuralValidationGenerator

@pytest.fixture
def generator():
    return StructuralValidationGenerator(seed=42)

@pytest.fixture
def temp_output_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test_output.csv")
        yield path

def test_generate_shape(generator):
    """Test that the generated dataframe has the correct shape."""
    df = generator.generate(num_records=100)
    assert df.shape[0] == 100
    assert df.shape[1] == 15 # Expected columns

def test_generate_columns(generator):
    """Test that all required columns exist."""
    df = generator.generate(num_records=10)
    required_columns = [
        'household_id', 'latitude', 'longitude', 'land_size', 'education_level',
        'finance_access', 'practice_mixed_farming', 'practice_terracing',
        'practice_conservation_tillage', 'practice_agroforestry', 'extension_visits',
        'hlias', 'CSA_Index', 'Stability_Score', 'village_id'
    ]
    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"

def test_csa_index_calculation(generator):
    """Test that CSA_Index is the sum of practice columns."""
    df = generator.generate(num_records=10)
    expected_csa = (
        df['practice_mixed_farming'] + 
        df['practice_terracing'] + 
        df['practice_conservation_tillage'] + 
        df['practice_agroforestry']
    )
    pd.testing.assert_series_equal(df['CSA_Index'], expected_csa, check_names=False)

def test_stability_score_range(generator):
    """Test that Stability_Score is within expected range (0-100)."""
    df = generator.generate(num_records=100)
    assert df['Stability_Score'].min() >= 0
    assert df['Stability_Score'].max() <= 100

def test_village_id_format(generator):
    """Test that village_id is derived correctly from coordinates."""
    df = generator.generate(num_records=10)
    for _, row in df.iterrows():
        parts = row['village_id'].split('_')
        assert len(parts) == 2
        # Check if they are numeric (floats)
        try:
            float(parts[0])
            float(parts[1])
        except ValueError:
            pytest.fail(f"Invalid village_id format: {row['village_id']}")

def test_save_function(generator, temp_output_path):
    """Test that the save function writes a valid CSV."""
    df = generator.generate(num_records=10)
    generator.save(df, temp_output_path)
    assert os.path.exists(temp_output_path)
    loaded_df = pd.read_csv(temp_output_path)
    assert loaded_df.shape == df.shape
    assert list(loaded_df.columns) == list(df.columns)

def test_deterministic_seed():
    """Test that the same seed produces the same data."""
    gen1 = StructuralValidationGenerator(seed=123)
    gen2 = StructuralValidationGenerator(seed=123)
    
    df1 = gen1.generate(num_records=5)
    df2 = gen2.generate(num_records=5)
    
    pd.testing.assert_frame_equal(df1, df2)