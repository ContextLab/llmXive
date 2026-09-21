"""
Unit tests for the statistical power calculation module (T021a).
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
from src.analysis.power import (
    load_dependencies_data,
    calculate_effect_size,
    calculate_power,
    run_power_analysis
)

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with correlation."""
    np.random.seed(42)
    n = 100
    x = np.random.normal(0, 1, n)
    # Create a moderate positive correlation (r ~ 0.3)
    y = 0.3 * x + np.random.normal(0, 1, n)
    return pd.DataFrame({
        'age_in_days': x,
        'vulnerability_count': y
    })

@pytest.fixture
def temp_csv(sample_df):
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_df.to_csv(f, index=False)
        path = f.name
    yield path
    Path(path).unlink()

def test_load_dependencies_data(temp_csv):
    """Test loading data from CSV."""
    df = load_dependencies_data(temp_csv)
    assert len(df) == 100
    assert 'age_in_days' in df.columns
    assert 'vulnerability_count' in df.columns

def test_load_dependencies_data_missing_file():
    """Test loading from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_dependencies_data("non_existent_file.csv")

def test_calculate_effect_size(sample_df):
    """Test effect size calculation."""
    effect_size = calculate_effect_size(sample_df)
    assert isinstance(effect_size, float)
    assert -1.0 <= effect_size <= 1.0
    # With seed 42 and the specific construction, r should be around 0.2-0.4
    assert 0.1 < effect_size < 0.5

def test_calculate_effect_size_missing_data(sample_df):
    """Test effect size calculation with missing data."""
    sample_df_with_nan = sample_df.copy()
    sample_df_with_nan.loc[0, 'age_in_days'] = np.nan
    effect_size = calculate_effect_size(sample_df_with_nan)
    assert isinstance(effect_size, float)

def test_calculate_power():
    """Test power calculation logic."""
    # High effect size, large sample -> high power
    power = calculate_power(effect_size=0.5, sample_size=200)
    assert power > 0.9
    
    # Low effect size, small sample -> low power
    power = calculate_power(effect_size=0.1, sample_size=20)
    assert power < 0.5
    
    # Perfect correlation -> power 1.0
    power = calculate_power(effect_size=0.99, sample_size=50)
    assert power == 1.0

def test_run_power_analysis(temp_csv):
    """Test the full analysis pipeline."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        output_path = f.name
    
    try:
        results = run_power_analysis(input_path=temp_csv, output_path=output_path)
        
        # Verify structure
        assert 'effect_size' in results
        assert 'alpha' in results
        assert 'sample_size' in results
        assert 'actual_power' in results
        assert 'methodology_notes' in results
        
        # Verify types
        assert isinstance(results['effect_size'], float)
        assert isinstance(results['sample_size'], int)
        assert isinstance(results['actual_power'], float)
        
        # Verify JSON file was written
        with open(output_path, 'r') as f:
            loaded_results = json.load(f)
            assert loaded_results == results
    finally:
        Path(output_path).unlink()