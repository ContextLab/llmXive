import pytest
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from analysis import run_regression, apply_fdr_correction, run_sensitivity

@pytest.fixture
def sample_metrics_csv(tmp_path):
    """Create a sample metrics CSV for testing."""
    data = {
        'repo_id': [f'repo_{i}' for i in range(20)],
        'readability': np.random.uniform(50, 90, 20),
        'sentiment': np.random.uniform(-1, 1, 20),
        'density': np.random.uniform(0.05, 0.3, 20),
        'churn': np.random.uniform(10, 100, 20),
        'age': np.random.randint(1, 10, 20),
        'complexity': np.random.uniform(1.0, 5.0, 20),
        'loc': np.random.randint(100, 1000, 20)
    }
    csv_path = tmp_path / "metrics.csv"
    pd.DataFrame(data).to_csv(csv_path, index=False)
    return str(csv_path)

def test_run_regression_creates_output(sample_metrics_csv, tmp_path):
    """Test that run_regression creates the output JSON file."""
    output_path = str(tmp_path / "analysis_results.json")
    
    results = run_regression(sample_metrics_csv, output_path)
    
    assert os.path.exists(output_path)
    assert 'model_type' in results
    assert 'r_squared' in results
    assert 'p_values' in results
    assert 'is_significant' in results
    assert results['sample_size'] == 20

def test_apply_fdr_correction():
    """Test FDR correction on a known set of p-values."""
    p_values = [0.01, 0.04, 0.03, 0.06, 0.02]
    corrected, significant = apply_fdr_correction(p_values, alpha=0.05)
    
    assert len(corrected) == len(p_values)
    assert len(significant) == len(p_values)
    # At least one should be significant given the low p-values
    assert any(significant)

def test_run_regression_missing_columns(tmp_path):
    """Test that run_regression raises ValueError for missing columns."""
    data = {
        'repo_id': ['repo_1'],
        'readability': [50.0]
        # Missing required columns
    }
    csv_path = tmp_path / "bad_metrics.csv"
    pd.DataFrame(data).to_csv(csv_path, index=False)
    
    output_path = str(tmp_path / "bad_results.json")
    
    with pytest.raises(ValueError):
        run_regression(str(csv_path), output_path)

def test_run_regression_insufficient_data(tmp_path):
    """Test that run_regression raises ValueError for too few samples."""
    data = {
        'repo_id': ['repo_1', 'repo_2'],
        'readability': [50.0, 60.0],
        'sentiment': [0.1, 0.2],
        'density': [0.1, 0.1],
        'churn': [10, 20],
        'age': [1, 2],
        'complexity': [1.0, 2.0],
        'loc': [100, 200]
    }
    csv_path = tmp_path / "tiny_metrics.csv"
    pd.DataFrame(data).to_csv(csv_path, index=False)
    
    output_path = str(tmp_path / "tiny_results.json")
    
    with pytest.raises(ValueError):
        run_regression(str(csv_path), output_path)