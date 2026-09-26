"""
Unit tests for the aggregate_results functionality.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.train.aggregate_results import load_run_metrics, aggregate_results

@pytest.fixture
def mock_run_dir(tmp_path):
    """Create a mock run directory structure with metrics files."""
    runs_dir = tmp_path / "models" / "runs"
    runs_dir.mkdir(parents=True)
    
    # Create 5 seed runs with metrics
    for i in range(5):
        seed_dir = runs_dir / f"seed_{i}"
        seed_dir.mkdir()
        
        metrics = {
            'models': {
                'cnn': {'mae': 0.15 + i * 0.01, 'r2': 0.85 - i * 0.01},
                'linear': {'mae': 0.25 + i * 0.01, 'r2': 0.75 - i * 0.01},
                'random_forest': {'mae': 0.20 + i * 0.01, 'r2': 0.80 - i * 0.01}
            }
        }
        
        with open(seed_dir / "metrics.json", 'w') as f:
            json.dump(metrics, f)
    
    return runs_dir

def test_load_run_metrics(mock_run_dir):
    """Test loading metrics from a single run directory."""
    run_dir = str(mock_run_dir / "seed_0")
    metrics = load_run_metrics(run_dir)
    
    assert 'models' in metrics
    assert 'cnn' in metrics['models']
    assert 'linear' in metrics['models']
    assert 'random_forest' in metrics['models']
    assert 'mae' in metrics['models']['cnn']
    assert 'r2' in metrics['models']['cnn']

def test_load_run_metrics_missing_file():
    """Test that missing metrics file raises FileNotFoundError."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(FileNotFoundError):
            load_run_metrics(tmp_dir)

def test_aggregate_results(mock_run_dir, tmp_path):
    """Test aggregation of multiple run results."""
    output_path = str(tmp_path / "results" / "metrics.json")
    
    result = aggregate_results(
        runs_dir=str(mock_run_dir),
        output_path=output_path,
        num_seeds=5
    )
    
    # Check structure
    assert 'n_runs' in result
    assert 'mae_distribution' in result
    assert 'r2_distribution' in result
    assert 'wilcoxon_p_value' in result
    
    # Check distributions
    assert len(result['mae_distribution']['cnn']) == 5
    assert len(result['mae_distribution']['linear']) == 5
    assert len(result['mae_distribution']['random_forest']) == 5
    
    # Check that values are collected correctly
    assert result['mae_distribution']['cnn'][0] == 0.15
    assert result['mae_distribution']['linear'][0] == 0.25
    
    # Check Wilcoxon test was performed (we have 5 samples)
    assert result['wilcoxon_p_value'] is not None
    assert isinstance(result['wilcoxon_p_value'], float)
    
    # Check output file was created
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        saved_result = json.load(f)
    assert saved_result == result

def test_aggregate_results_missing_runs(mock_run_dir, tmp_path):
    """Test aggregation when some run directories are missing."""
    output_path = str(tmp_path / "results" / "metrics.json")
    
    # Request 10 runs but only 5 exist
    result = aggregate_results(
        runs_dir=str(mock_run_dir),
        output_path=output_path,
        num_seeds=10
    )
    
    # Should only aggregate the 5 existing runs
    assert len(result['mae_distribution']['cnn']) == 5
    assert result['n_runs'] == 10  # Requested number

def test_aggregate_results_insufficient_data_for_wilcoxon(tmp_path):
    """Test aggregation with insufficient data for Wilcoxon test."""
    runs_dir = tmp_path / "models" / "runs"
    runs_dir.mkdir(parents=True)
    
    # Create only 1 seed run
    seed_dir = runs_dir / "seed_0"
    seed_dir.mkdir()
    
    metrics = {
        'models': {
            'cnn': {'mae': 0.15, 'r2': 0.85},
            'linear': {'mae': 0.25, 'r2': 0.75},
            'random_forest': {'mae': 0.20, 'r2': 0.80}
        }
    }
    
    with open(seed_dir / "metrics.json", 'w') as f:
        json.dump(metrics, f)
    
    output_path = str(tmp_path / "results" / "metrics.json")
    
    result = aggregate_results(
        runs_dir=str(runs_dir),
        output_path=output_path,
        num_seeds=1
    )
    
    # Wilcoxon test should not be performed with only 1 sample
    assert result['wilcoxon_p_value'] is None
    assert len(result['mae_distribution']['cnn']) == 1
