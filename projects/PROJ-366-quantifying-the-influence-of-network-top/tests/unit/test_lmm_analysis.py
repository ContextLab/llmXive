"""
Unit tests for Linear Mixed-Effects Model (LMM) analysis module.

Tests cover:
- Data loading and validation
- Feature extraction
- LMM model fitting (with mocked data for N=2 case)
- Result interpretation
- Output file generation
"""

import json
import os
import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import pandas as pd

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.lmm_analysis import (
    load_conductivity_samples,
    extract_topological_features,
    run_lmm_analysis,
    interpret_results,
    save_results,
    main
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        # Create directory structure
        (base / "conductivities").mkdir(parents=True)
        yield base


@pytest.fixture
def sample_thermal_data(temp_data_dir):
    """Create mock thermal sample data files."""
    samples = []
    
    # Sample 1: High variance, low conductivity
    sample1 = {
        'sample_id': 'sample_001',
        'conductivity': 45.2,
        'metadata': {'converged': True},
        'graph_metrics': {
            'mean_degree': 4.2,
            'mean_clustering': 0.15,
            'mean_shortest_path': 3.5,
            'degree_variance': 0.8,
            'node_count': 100
        }
    }
    
    # Sample 2: Low variance, high conductivity
    sample2 = {
        'sample_id': 'sample_002',
        'conductivity': 82.1,
        'metadata': {'converged': True},
        'graph_metrics': {
            'mean_degree': 4.1,
            'mean_clustering': 0.18,
            'mean_shortest_path': 3.2,
            'degree_variance': 0.2,
            'node_count': 100
        }
    }
    
    for i, sample in enumerate([sample1, sample2], 1):
        filepath = temp_data_dir / "conductivities" / f"sample_{i:03d}.pkl"
        with open(filepath, 'wb') as f:
            pickle.dump(sample, f)
        samples.append(sample)
    
    return samples


def test_load_conductivity_samples_empty(temp_data_dir):
    """Test loading from empty directory."""
    samples = load_conductivity_samples(temp_data_dir)
    assert len(samples) == 0


def test_load_conductivity_samples_valid(sample_thermal_data, temp_data_dir):
    """Test loading valid thermal samples."""
    samples = load_conductivity_samples(temp_data_dir)
    assert len(samples) == 2
    assert samples[0]['sample_id'] == 'sample_001'
    assert samples[1]['conductivity'] == 82.1


def test_load_conductivity_samples_invalid_file(temp_data_dir):
    """Test handling of invalid pickle files."""
    # Create a non-pickle file
    bad_file = temp_data_dir / "conductivities" / "bad.txt"
    bad_file.write_text("not a pickle")
    
    # Create a valid one too
    valid = {
        'sample_id': 'valid',
        'conductivity': 50.0,
        'graph_metrics': {'degree_variance': 0.5}
    }
    valid_file = temp_data_dir / "conductivities" / "valid.pkl"
    with open(valid_file, 'wb') as f:
        pickle.dump(valid, f)
    
    samples = load_conductivity_samples(temp_data_dir)
    assert len(samples) == 1  # Only valid one loaded
    assert samples[0]['sample_id'] == 'valid'


def test_extract_topological_features(sample_thermal_data, temp_data_dir):
    """Test feature extraction from samples."""
    samples = load_conductivity_samples(temp_data_dir)
    df = extract_topological_features(samples)
    
    assert len(df) == 2
    assert 'sample_id' in df.columns
    assert 'conductivity' in df.columns
    assert 'degree_variance' in df.columns
    assert 'mean_clustering' in df.columns
    
    # Check values
    assert df.iloc[0]['degree_variance'] == 0.8
    assert df.iloc[1]['conductivity'] == 82.1


def test_run_lmm_analysis_insufficient_data():
    """Test LMM with insufficient data."""
    empty_df = pd.DataFrame(columns=['sample_id', 'conductivity', 'degree_variance'])
    results = run_lmm_analysis(empty_df)
    
    assert results['status'] == 'insufficient_data'
    assert 'Less than 2 samples' in results['warnings'][0]


def test_run_lmm_analysis_with_data(sample_thermal_data, temp_data_dir):
    """Test LMM fitting with valid data."""
    samples = load_conductivity_samples(temp_data_dir)
    df = extract_topological_features(samples)
    results = run_lmm_analysis(df)
    
    assert results['status'] == 'completed'
    assert 'coefficients' in results
    assert 'intercept' in results['coefficients']
    assert 'degree_variance_coef' in results['coefficients']
    assert 'r_squared' in results['coefficients']
    assert 'p_value_degree_variance' in results['coefficients']
    
    # Check that coefficients are numeric
    assert isinstance(results['coefficients']['intercept'], float)
    assert isinstance(results['coefficients']['degree_variance_coef'], float)


def test_interpret_results_completed():
    """Test result interpretation for completed analysis."""
    results = {
        'status': 'completed',
        'coefficients': {
            'r_squared': 0.85,
            'p_value_degree_variance': 0.01,
            'degree_variance_coef': -15.5
        }
    }
    
    interpretation = interpret_results(results)
    
    assert "Significant" in interpretation
    assert "negative" in interpretation
    assert "0.85" in interpretation


def test_interpret_results_insufficient_data():
    """Test interpretation for incomplete analysis."""
    results = {
        'status': 'insufficient_data',
        'warnings': ['Need more data']
    }
    
    interpretation = interpret_results(results)
    
    assert "incomplete" in interpretation


def test_save_results(temp_data_dir):
    """Test saving results to JSON."""
    output_dir = temp_data_dir / "outputs"
    output_dir.mkdir()
    
    results = {
        'status': 'completed',
        'coefficients': {'r_squared': 0.5, 'degree_variance_coef': 1.0}
    }
    interpretation = "Test interpretation"
    
    output_path = save_results(results, interpretation, output_dir)
    
    assert output_path.exists()
    assert output_path.name == "lmm_analysis_results.json"
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert data['analysis_type'] == 'Linear Mixed-Effects Model (LMM)'
    assert data['interpretation'] == interpretation
    assert data['results']['status'] == 'completed'


def test_main_integration(sample_thermal_data, temp_data_dir):
    """Test main function integration."""
    # Mock get_config and get_paths
    mock_config = {}
    mock_paths = {
        'data': temp_data_dir,
        'model_outputs': temp_data_dir / "outputs"
    }
    
    with patch('analysis.lmm_analysis.get_config', return_value=mock_config), \
         patch('analysis.lmm_analysis.get_paths', return_value=mock_paths):
        
        # Run main
        result = main()
        
        # Verify output file created
        output_file = temp_data_dir / "outputs" / "lmm_analysis_results.json"
        assert output_file.exists()
        
        # Verify result structure
        assert result['status'] == 'completed'
        assert 'coefficients' in result