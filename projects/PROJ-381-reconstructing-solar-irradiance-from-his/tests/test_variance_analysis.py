"""
Tests for the Variance Analysis Generation (T023).
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

from code.analysis.generate_variance_analysis import (
    calculate_period_statistics,
    run_variance_analysis,
    HISTORICAL_PERIODS
)
from code.analysis.stats import load_reconstruction_data, filter_by_period

@pytest.fixture
def mock_reconstruction_data():
    """Create a mock reconstruction dataset for testing."""
    # Generate synthetic but realistic data for the years 1600-2024
    years = np.arange(1600, 2025)
    # Simulate TSI with some noise and a slight trend
    tsi_base = 1361.0
    noise = np.random.normal(0, 0.5, len(years))
    # Add a fake cycle effect
    cycles = np.sin(2 * np.pi * years / 11) * 0.8
    tsi_values = tsi_base + cycles + noise

    df = pd.DataFrame({
        'year': years,
        'tsi': tsi_values
    })
    return df

@pytest.fixture
def temp_output_dir(mock_reconstruction_data):
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Write mock data
        data_file = tmp_path / "reconstruction_1610_2002.parquet"
        mock_reconstruction_data.to_parquet(data_file)
        
        # Return paths
        yield {
            "data": data_file,
            "output": tmp_path / "variance_analysis.json",
            "temp_dir": tmp_path
        }

def test_calculate_period_statistics_valid(mock_reconstruction_data):
    """Test statistics calculation for a valid period."""
    period_name = "Maunder_Minimum"
    period_range = HISTORICAL_PERIODS[period_name]
    
    stats = calculate_period_statistics(
        mock_reconstruction_data,
        period_name,
        period_range,
        n_bootstrap=100, # Reduced for speed
        random_seed=42
    )
    
    assert stats["period"] == period_name
    assert stats["n_samples"] > 0
    assert stats["mean_tsi"] is not None
    assert stats["std_tsi"] is not None
    assert stats["variance_tsi"] is not None
    assert stats["ci_lower"] is not None
    assert stats["ci_upper"] is not None
    assert stats["ci_lower"] <= stats["mean_tsi"] <= stats["ci_upper"]
    assert stats["bootstrap_results"]["n_iterations"] == 100

def test_calculate_period_statistics_empty_period(mock_reconstruction_data):
    """Test statistics calculation for a period with no data."""
    # Define a period far outside the data range
    future_period = {"start": 3000, "end": 3010}
    
    stats = calculate_period_statistics(
        mock_reconstruction_data,
        "Future_Test",
        future_period,
        n_bootstrap=10
    )
    
    assert stats["n_samples"] == 0
    assert stats["mean_tsi"] is None
    assert stats["std_tsi"] is None
    assert stats["variance_tsi"] is None

def test_run_variance_analysis_integration(temp_output_dir):
    """Test the full variance analysis pipeline."""
    result = run_variance_analysis(
        reconstruction_path=str(temp_output_dir["data"]),
        output_path=str(temp_output_dir["output"]),
        n_bootstrap=100, # Reduced for speed
        random_seed=42
    )
    
    # Check return value structure
    assert "metadata" in result
    assert "periods" in result
    assert result["metadata"]["n_bootstrap_iterations"] == 100
    
    # Check file creation
    assert os.path.exists(temp_output_dir["output"])
    
    # Verify JSON content
    with open(temp_output_dir["output"], 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report == result
    assert "Maunder_Minimum" in saved_report["periods"]
    assert "Dalton_Minimum" in saved_report["periods"]
    
    # Verify specific period stats exist
    maunder_stats = saved_report["periods"]["Maunder_Minimum"]
    assert maunder_stats["n_samples"] > 0
    assert "bootstrap_results" in maunder_stats

def test_run_variance_analysis_missing_file():
    """Test that the function raises an error if input file is missing."""
    with pytest.raises(FileNotFoundError, match="Reconstruction file not found"):
        run_variance_analysis(
            reconstruction_path="nonexistent_file.parquet",
            output_path="dummy.json"
        )