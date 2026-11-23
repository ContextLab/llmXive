import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
from data_cleaning import (
    load_raw_data,
    apply_schema_validation,
    apply_independence_filter,
    apply_monolithic_filter,
    normalize_units,
    apply_major_element_filter,
    apply_ilr_transformation,
    run_cleaning_pipeline
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return {
        'poisson_ratio': [0.33, 0.34, 0.35, 0.36, 0.37],
        'young_modulus': [70, 72, 74, 76, 78],
        'Cu': [1.0, 2.0, 3.0, 4.0, 5.0],
        'Mg': [2.0, 3.0, 4.0, 5.0, 6.0],
        'Si': [1.0, 1.5, 2.0, 2.5, 3.0],
        'Zn': [0.5, 1.0, 1.5, 2.0, 2.5],
        'Mn': [0.5, 1.0, 1.5, 2.0, 2.5],
        'measurement_method': ['Ultrasonic', 'Independent', 'Direct Measurement', 'Ultrasonic', 'Independent']
    }

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_raw_data_json(temp_dir):
    """Test loading raw data from JSON."""
    # Create sample JSON file
    data = {
        'poisson_ratio': [0.33, 0.34],
        'young_modulus': [70, 72],
        'Cu': [1.0, 2.0],
        'Mg': [2.0, 3.0],
        'Si': [1.0, 1.5],
        'Zn': [0.5, 1.0],
        'Mn': [0.5, 1.0],
        'measurement_method': ['Ultrasonic', 'Independent']
    }
    
    input_path = temp_dir / "test_data.json"
    with open(input_path, 'w') as f:
        json.dump(data, f)
    
    # Load data
    df = load_raw_data(input_path)
    
    # Verify
    assert len(df) == 2
    assert 'poisson_ratio' in df.columns
    assert df['poisson_ratio'].iloc[0] == 0.33

def test_apply_schema_validation(sample_data):
    """Test schema validation."""
    df = pd.DataFrame(sample_data)
    
    # Valid data should pass
    result = apply_schema_validation(df)
    assert len(result) == 5
    
    # Missing field should raise error
    invalid_data = sample_data.copy()
    del invalid_data['Cu']
    df_invalid = pd.DataFrame(invalid_data)
    
    with pytest.raises(ValueError):
        apply_schema_validation(df_invalid)

def test_apply_independence_filter(sample_data):
    """Test independence filtering."""
    df = pd.DataFrame(sample_data)
    
    # Add a derived measurement
    df.loc[0, 'measurement_method'] = 'Derived'
    
    result = apply_independence_filter(df)
    
    # Should exclude the derived measurement
    assert len(result) == 4
    assert 'Derived' not in result['measurement_method'].values

def test_apply_monolithic_filter(sample_data):
    """Test monolithic filtering."""
    df = pd.DataFrame(sample_data)
    
    # Add a record with missing composition
    df.loc[5] = [0.33, 70, np.nan, 2.0, 1.0, 0.5, 0.5, 'Ultrasonic']
    
    result = apply_monolithic_filter(df)
    
    # Should exclude the record with missing composition
    assert len(result) == 5

def test_normalize_units(sample_data):
    """Test unit normalization."""
    df = pd.DataFrame(sample_data)
    
    # Set high Young's modulus to simulate Pa
    df['young_modulus'] = 70e9  # 70 GPa in Pa
    
    result = normalize_units(df)
    
    # Should convert to GPa
    assert result['young_modulus'].iloc[0] == 70.0
    
    # Check atomic fractions sum to 1
    composition_cols = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    for idx, row in result.iterrows():
        total = row[composition_cols].sum()
        assert abs(total - 1.0) < 0.01

def test_apply_major_element_filter(sample_data):
    """Test major element filtering."""
    df = pd.DataFrame(sample_data)
    
    # Normalize to atomic fractions first
    composition_cols = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    total = df[composition_cols].sum(axis=1)
    for col in composition_cols:
        df[col] = df[col] / total
    
    # Set a record with low major element sum
    df.loc[0, composition_cols] = [0.1, 0.1, 0.1, 0.1, 0.1]  # Sum = 0.5
    
    result = apply_major_element_filter(df)
    
    # Should exclude the record with low major element sum
    assert len(result) == 4

def test_apply_ilr_transformation(sample_data):
    """Test ILR transformation."""
    df = pd.DataFrame(sample_data)
    
    # Normalize to atomic fractions
    composition_cols = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    total = df[composition_cols].sum(axis=1)
    for col in composition_cols:
        df[col] = df[col] / total
    
    result = apply_ilr_transformation(df)
    
    # Check that ILR features are created
    ilr_cols = [f'ilr_{col}' for col in composition_cols[:-1]]
    for col in ilr_cols:
        assert col in result.columns
    
    # Check that ILR features have reasonable values
    for col in ilr_cols:
        assert not result[col].isnull().any()

def test_run_cleaning_pipeline(sample_data, temp_dir):
    """Test the full cleaning pipeline."""
    # Create input file
    input_path = temp_dir / "input.json"
    with open(input_path, 'w') as f:
        json.dump(sample_data, f)
    
    output_path = temp_dir / "output.csv"
    
    # Run pipeline
    result = run_cleaning_pipeline(input_path, output_path)
    
    # Verify output file exists
    assert output_path.exists()
    
    # Verify result
    assert len(result) == 5
    assert 'ilr_Cu' in result.columns
    assert 'ilr_Mg' in result.columns
    assert 'ilr_Si' in result.columns
    assert 'ilr_Zn' in result.columns