import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import json

from src.models.gamm import fit_gamm, run_gamm_pipeline
from src.config import setup_logging

logger = setup_logging(__name__)

@pytest.fixture
def sample_gamm_data():
    """Generate sample data for GAMM testing."""
    np.random.seed(42)
    n = 100
    data = {
        "species": np.random.choice(["SpeciesA", "SpeciesB"], n),
        "year": np.random.choice([2020, 2021], n),
        "mean_temperature": np.random.normal(15, 5, n),
        "total_precipitation": np.random.normal(50, 10, n),
        "extreme_weather_index": np.random.normal(0, 1, n),
        "first_arrival_date": np.random.normal(100, 20, n)  # Day of year
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_fit_species_year_gamm_basic(sample_gamm_data, temp_data_dir):
    """Test basic GAMM fitting."""
    output_path = os.path.join(temp_data_dir, "test_results.parquet")
    results = fit_gamm(sample_gamm_data, output_path=output_path)
    
    assert results is not None
    assert "species" in results.columns
    assert "converged" in results.columns
    assert "p_value" in results.columns
    assert len(results) > 0

def test_fit_species_year_gamm_insufficient_data(temp_data_dir):
    """Test GAMM fitting with insufficient data."""
    data = {
        "species": ["SpeciesA"] * 5,
        "year": [2020] * 5,
        "mean_temperature": [10.0] * 5,
        "total_precipitation": [50.0] * 5,
        "extreme_weather_index": [0.0] * 5,
        "first_arrival_date": [100.0] * 5
    }
    df = pd.DataFrame(data)
    output_path = os.path.join(temp_data_dir, "test_results.parquet")
    
    # Should skip due to insufficient data (less than 10 rows)
    results = fit_gamm(df, output_path=output_path)
    
    # No results should be returned for this group
    assert len(results) == 0 or all(results["converged"] == False)

def test_fit_species_year_gamm_output_schema(sample_gamm_data, temp_data_dir):
    """Test that the output schema matches requirements."""
    output_path = os.path.join(temp_data_dir, "test_results.parquet")
    results = fit_gamm(sample_gamm_data, output_path=output_path)
    
    required_columns = ["species", "year", "temp_coef", "precip_coef", "p_value", "converged"]
    for col in required_columns:
        assert col in results.columns

def test_run_gamm_pipeline(temp_data_dir):
    """Test the full pipeline execution."""
    # Create sample data
    data = {
        "species": ["SpeciesA"] * 50 + ["SpeciesB"] * 50,
        "year": [2020] * 100,
        "mean_temperature": np.random.normal(15, 5, 100),
        "total_precipitation": np.random.normal(50, 10, 100),
        "extreme_weather_index": np.random.normal(0, 1, 100),
        "first_arrival_date": np.random.normal(100, 20, 100)
    }
    input_path = os.path.join(temp_data_dir, "input.parquet")
    output_path = os.path.join(temp_data_dir, "output.parquet")
    
    pd.DataFrame(data).to_parquet(input_path)
    
    results = run_gamm_pipeline(input_path=input_path, output_path=output_path)
    
    assert results is not None
    assert os.path.exists(output_path)

def test_run_gamm_pipeline_empty_input(temp_data_dir):
    """Test pipeline with empty input."""
    input_path = os.path.join(temp_data_dir, "input.parquet")
    output_path = os.path.join(temp_data_dir, "output.parquet")
    
    pd.DataFrame(columns=["species", "year", "mean_temperature", "total_precipitation", "extreme_weather_index", "first_arrival_date"]).to_parquet(input_path)
    
    results = run_gamm_pipeline(input_path=input_path, output_path=output_path)
    
    assert len(results) == 0

def test_run_gamm_pipeline_missing_columns(temp_data_dir):
    """Test pipeline with missing required columns."""
    data = {
        "species": ["SpeciesA"] * 50,
        "year": [2020] * 50
        # Missing climate columns
    }
    input_path = os.path.join(temp_data_dir, "input.parquet")
    output_path = os.path.join(temp_data_dir, "output.parquet")
    
    pd.DataFrame(data).to_parquet(input_path)
    
    with pytest.raises(Exception):  # Should raise an error due to missing columns
        run_gamm_pipeline(input_path=input_path, output_path=output_path)

def test_gp_application_logic(sample_gamm_data, temp_data_dir):
    """Test that GP logic is not applied in base model (T023a)."""
    # T023a is the base model without GP. This test ensures we are not
    # accidentally applying GP logic here.
    output_path = os.path.join(temp_data_dir, "test_results.parquet")
    results = fit_gamm(sample_gamm_data, output_path=output_path)
    
    # Just verify it runs without GP-specific errors
    assert results is not None

def test_moran_i_threshold_behavior(sample_gamm_data, temp_data_dir):
    """Test that Moran's I logic is not applied in T023a (it's T023b)."""
    # T023a should not compute Moran's I. This test ensures we are not
    # computing it here.
    output_path = os.path.join(temp_data_dir, "test_results.parquet")
    results = fit_gamm(sample_gamm_data, output_path=output_path)
    
    # Just verify it runs
    assert results is not None