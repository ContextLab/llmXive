"""
Unit tests for power-law model fitting (T016).
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path

# Import the module under test
from analysis.fitting import (
    fit_power_law_model,
    run_fitting_for_subject,
    generate_fitting_report,
    load_avalanche_sizes_from_store
)

@pytest.fixture
def sample_avalanche_sizes():
    """Generate synthetic data that approximates a power-law distribution."""
    # Using a Pareto distribution as a proxy for power-law
    alpha_true = 2.5
    size_min = 1.0
    # Generate 1000 samples
    data = np.random.pareto(alpha_true, 1000) + size_min
    # Round to integers to simulate discrete avalanche sizes
    return list(np.round(data).astype(int))

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking the project data layout."""
    avalanche_dir = tmp_path / "processed" / "avalanches"
    avalanche_dir.mkdir(parents=True)
    return tmp_path

def test_fit_power_law_model_success(sample_avalanche_sizes):
    """Test that fitting a power-law model returns expected keys."""
    result = fit_power_law_model(sample_avalanche_sizes)
    
    assert 'fit_successful' in result
    assert result['fit_successful'] is True
    assert 'alpha' in result
    assert 'xmin' in result
    assert 'comparison' in result
    assert 'vs_exponential' in result['comparison']
    assert 'vs_lognormal' in result['comparison']
    assert 'best_model' in result
    assert result['alpha'] > 0.0
    assert result['xmin'] > 0.0

def test_fit_power_law_model_insufficient_data():
    """Test fitting with too few data points."""
    result = fit_power_law_model([1, 2])
    assert 'error' in result or not result.get('fit_successful', False)

def test_fit_power_law_model_empty_input():
    """Test fitting with empty input."""
    result = fit_power_law_model([])
    assert 'error' in result or not result.get('fit_successful', False)

def test_run_fitting_for_subject(sample_avalanche_sizes):
    """Test the subject-level runner."""
    result = run_fitting_for_subject("sub-001", sample_avalanche_sizes)
    
    assert result['subject_id'] == "sub-001"
    assert result['n_avalanches'] == len(sample_avalanche_sizes)
    assert result['fit_successful'] is True
    assert 'alpha' in result

def test_generate_fitting_report(tmp_path, sample_avalanche_sizes):
    """Test report generation."""
    results = [
        run_fitting_for_subject("sub-001", sample_avalanche_sizes),
        run_fitting_for_subject("sub-002", sample_avalanche_sizes)
    ]
    
    output_path = tmp_path / "fitting_report.csv"
    generate_fitting_report(results, output_path)
    
    assert output_path.exists()
    
    # Verify CSV content
    df = pd.read_csv(output_path)
    assert len(df) == 2
    assert 'subject_id' in df.columns
    assert 'alpha' in df.columns
    assert 'best_model' in df.columns
    assert df['subject_id'].iloc[0] == "sub-001"

def test_load_avalanche_sizes_from_store(temp_data_dir):
    """Test loading data from the simulated store."""
    # Create a mock CSV file
    csv_path = temp_data_dir / "processed" / "avalanches" / "sub-001_avalanches.csv"
    df = pd.DataFrame({'size': [1, 2, 3, 4, 5, 10, 20]})
    df.to_csv(csv_path, index=False)
    
    loaded = load_avalanche_sizes_from_store(temp_data_dir)
    
    assert 'sub-001' in loaded
    assert loaded['sub-001'] == [1, 2, 3, 4, 5, 10, 20]

def test_load_avalanche_sizes_from_store_missing_file(temp_data_dir):
    """Test loading when no files exist."""
    loaded = load_avalanche_sizes_from_store(temp_data_dir)
    assert loaded == {}