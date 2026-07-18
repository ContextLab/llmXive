"""
Tests for Sensitivity Analysis Module (T022a).

These tests verify that the sensitivity analysis module:
1. Correctly loads real data (or handles missing data gracefully).
2. Produces valid bootstrap statistics.
3. Generates the expected output file.
"""
import os
import sys
import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.sensitivity_analysis import (
    bootstrap_correlation,
    run_sensitivity_analysis,
    get_data_path,
    load_processed_data
)

@pytest.fixture
def mock_processed_data(tmp_path):
    """Create a mock processed data file for testing."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    filepath = data_dir / "merged_drugs.csv"
    # Create a small realistic dataset
    np.random.seed(42)
    n = 50
    tpsa = np.random.uniform(30, 150, n)
    # Create a weak negative correlation
    half_life = 100 - 0.5 * tpsa + np.random.normal(0, 5, n)
    
    df = pd.DataFrame({
        'smiles': ['CC(=O)OC1=CC=CC=C1C(=O)O'] * n, # Dummy SMILES
        'TPSA': tpsa,
        'half_life_hours': half_life
    })
    df.to_csv(filepath, index=False)
    return filepath

def test_get_data_path():
    """Test that get_data_path constructs the correct path."""
    path = get_data_path("test.csv")
    assert isinstance(path, Path)
    assert path.name == "test.csv"
    # Check it's in the processed directory
    assert "processed" in str(path)

def test_load_processed_data_missing_file(tmp_path):
    """Test that load_processed_data raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_processed_data(tmp_path / "nonexistent.csv")

def test_load_processed_data_valid(mock_processed_data):
    """Test loading valid processed data."""
    df = load_processed_data(mock_processed_data)
    assert len(df) == 50
    assert 'TPSA' in df.columns
    assert 'half_life_hours' in df.columns

def test_bootstrap_correlation(mock_processed_data):
    """Test bootstrap correlation calculation."""
    df = load_processed_data(mock_processed_data)
    
    # Run with fewer iterations for speed
    results = bootstrap_correlation(df, n_iterations=50, random_seed=42)
    
    # Verify structure
    assert 'mean_correlation' in results
    assert 'std_correlation' in results
    assert 'ci_95_lower' in results
    assert 'ci_95_upper' in results
    assert 'is_significant' in results
    
    # Verify types
    assert isinstance(results['mean_correlation'], float)
    assert isinstance(results['std_correlation'], float)
    assert isinstance(results['is_significant'], bool)
    
    # Verify logical consistency
    assert results['ci_95_lower'] <= results['mean_correlation'] <= results['ci_95_upper']
    assert results['std_correlation'] >= 0

def test_run_sensitivity_analysis(mock_processed_data, tmp_path):
    """Test the full sensitivity analysis run."""
    output_dir = tmp_path / "output"
    
    results = run_sensitivity_analysis(
        data_path=mock_processed_data,
        output_dir=output_dir,
        n_iterations=50
    )
    
    # Verify results structure
    assert 'mean_correlation' in results
    assert 'metadata' in results
    assert results['status'] != 'failed'
    
    # Verify output file creation
    output_file = output_dir / "sensitivity_analysis_results.json"
    assert output_file.exists()
    
    # Verify JSON content
    with open(output_file) as f:
        saved_results = json.load(f)
    
    assert saved_results['mean_correlation'] == results['mean_correlation']
    assert 'software' in saved_results['metadata']

def test_bootstrap_correlation_stability():
    """Test that bootstrap produces consistent results with same seed."""
    # Create simple synthetic data for this specific test
    np.random.seed(123)
    n = 100
    x = np.random.normal(0, 1, n)
    y = 2 * x + np.random.normal(0, 0.5, n)
    df = pd.DataFrame({'x': x, 'y': y})
    
    # Run twice with same seed
    res1 = bootstrap_correlation(df, x_col='x', y_col='y', n_iterations=10, random_seed=999)
    res2 = bootstrap_correlation(df, x_col='x', y_col='y', n_iterations=10, random_seed=999)
    
    # Results should be identical
    assert res1['mean_correlation'] == res2['mean_correlation']
    assert res1['ci_95_lower'] == res2['ci_95_lower']
