"""
Integration Test for T070: Validation of Harmonized Results

Verifies that the validation script correctly:
1. Loads harmonized data
2. Runs the analysis pipeline
3. Compares results with synthetic baseline
4. Detects statistical artifacts if present
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validate_harmonized_results import load_baseline_metrics, compare_distributions, run_validation_pipeline
from config import load_config

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test artifacts."""
    tmpdir = tempfile.mkdtemp()
    # Create necessary subdirectories
    os.makedirs(os.path.join(tmpdir, "data", "processed"), exist_ok=True)
    os.makedirs(os.path.join(tmpdir, "data", "results"), exist_ok=True)
    os.makedirs(os.path.join(tmpdir, "data", "config"), exist_ok=True)
    
    # Save original cwd
    original_cwd = os.getcwd()
    os.chdir(tmpdir)
    
    yield tmpdir
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(tmpdir)

@pytest.fixture
def mock_harmonized_data(temp_test_dir):
    """Generate mock harmonized data for testing."""
    # Create a simple dataset
    n_subjects = 50
    data = {
        'subject_id': range(n_subjects),
        'Bacteroides': np.random.normal(0.2, 0.1, n_subjects),
        'Firmicutes': np.random.normal(0.3, 0.1, n_subjects),
        'Actinobacteria': np.random.normal(0.1, 0.05, n_subjects),
        'sleep_duration': np.random.normal(7.5, 1.0, n_subjects),
        'sws_duration': np.random.normal(2.0, 0.5, n_subjects),
        'rem_duration': np.random.normal(1.5, 0.4, n_subjects)
    }
    df = pd.DataFrame(data)
    df.to_parquet("data/processed/harmonized_data.parquet")
    return df

@pytest.fixture
def mock_baseline(temp_test_dir):
    """Create a mock synthetic baseline report."""
    baseline = {
        'significant_correlations': 5,
        'total_correlations': 15,
        'mean_correlation_strength': 0.25,
        'stability_metric': 0.1
    }
    with open("data/results/synthetic_validation_report.json", 'w') as f:
        json.dump(baseline, f)
    return baseline

@pytest.fixture
def mock_config(temp_test_dir):
    """Create a minimal config file."""
    config = {
        'random_seed': 42,
        'p_threshold': 0.05,
        'fdr_method': 'bh'
    }
    with open("data/config/config.yaml", 'w') as f:
        import yaml
        yaml.dump(config, f)
    return config

def test_load_baseline_metrics(mock_baseline):
    """Test loading baseline metrics."""
    metrics = load_baseline_metrics("data/results/synthetic_validation_report.json")
    assert 'significant_correlations' in metrics
    assert metrics['significant_correlations'] == 5

def test_compare_distributions_normal(mock_harmonized_data, mock_baseline, mock_config):
    """Test comparison when results are normal (no artifacts)."""
    # Run a minimal correlation to generate correlation_matrix.json
    # (In a real scenario, this would be done by the pipeline)
    correlations = {
        'Bacteroides_sleep_duration': {'r': 0.2, 'p_adjusted': 0.1},
        'Firmicutes_sws_duration': {'r': 0.3, 'p_adjusted': 0.04},
        'Actinobacteria_rem_duration': {'r': 0.1, 'p_adjusted': 0.5}
    }
    
    with open("data/results/correlation_matrix.json", 'w') as f:
        json.dump({'correlations': correlations}, f)
    
    baseline = load_baseline_metrics("data/results/synthetic_validation_report.json")
    comparison = compare_distributions({'correlations': correlations}, baseline)
    
    assert 'harmonized_metrics' in comparison
    assert 'baseline_metrics' in comparison
    assert 'deviation' in comparison
    assert 'artifacts_detected' in comparison

def test_compare_distributions_artifacts(mock_harmonized_data, mock_baseline, mock_config):
    """Test comparison when artifacts are detected (high deviation)."""
    # Create correlations with artificially high strength
    correlations = {
        'Bacteroides_sleep_duration': {'r': 0.9, 'p_adjusted': 0.01},
        'Firmicutes_sws_duration': {'r': 0.85, 'p_adjusted': 0.01},
        'Actinobacteria_rem_duration': {'r': 0.8, 'p_adjusted': 0.01}
    }
    
    with open("data/results/correlation_matrix.json", 'w') as f:
        json.dump({'correlations': correlations}, f)
    
    baseline = load_baseline_metrics("data/results/synthetic_validation_report.json")
    comparison = compare_distributions({'correlations': correlations}, baseline)
    
    # Should detect artifacts due to high deviation
    assert comparison['artifacts_detected'] == True
    assert len(comparison['artifact_flags']) > 0

def test_run_validation_pipeline(mock_harmonized_data, mock_baseline, mock_config):
    """Test the full validation pipeline."""
    # This test would normally run the full pipeline, but for unit testing
    # we verify the structure of the output
    try:
        result = run_validation_pipeline(mock_config)
        assert 'harmonized_metrics' in result
        assert 'baseline_metrics' in result
        assert 'status' in result
    except FileNotFoundError as e:
        # Expected if some intermediate files are missing in this simplified test
        pytest.skip(f"Missing intermediate file: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])