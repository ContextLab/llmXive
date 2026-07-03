"""
Test suite for T015: save_baseline_results functionality.

Tests that baseline results are correctly saved to JSON files with proper
naming convention and structure.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import pandas as pd

# Import the module under test
from save_baseline_results import save_baseline_results, DISCLAIMER_TEXT, TYPE_I_THRESHOLD


@pytest.fixture
def mock_dataset():
    """Create a mock dataset for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 10
    
    # Create features
    X = np.random.randn(n_samples, n_features)
    
    # Create target with some class imbalance
    y = np.random.choice([0, 1], size=n_samples, p=[0.6, 0.4])
    
    # Create DataFrame
    df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(n_features)])
    df['target'] = y
    
    return df


@pytest.fixture
def mock_simulation_results():
    """Create mock simulation results for testing."""
    n_iterations = 100
    p_values_null = np.random.uniform(0, 1, n_iterations)
    p_values_alt = np.random.beta(2, 5, n_iterations)  # Shifted towards 0
    
    return {
        'iterations': [
            {
                'p_value': pv_null,
                'p_value_alt': pv_alt,
                'rejection_null': pv_null < 0.05,
                'rejection_alt': pv_alt < 0.05
            }
            for pv_null, pv_alt in zip(p_values_null, p_values_alt)
        ],
        'metadata': {
            'n_iterations': n_iterations,
            'seed': 42
        }
    }


def test_save_baseline_results_creates_files(tmp_path, mock_dataset, mock_simulation_results):
    """Test that save_baseline_results creates the expected output files."""
    results_dir = tmp_path / 'results'
    data_dir = tmp_path / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Save mock dataset
    dataset_path = data_dir / 'test_dataset.csv'
    mock_dataset.to_csv(dataset_path, index=False)
    
    # Mock the simulation functions
    with patch('save_baseline_results.load_dataset', return_value=mock_dataset), \
         patch('save_baseline_results.run_full_simulation', return_value=mock_simulation_results), \
         patch('save_baseline_results.analyze_baseline_results', return_value={
             'type_i_error_rate': 0.05,
             'type_i_error_ci': [0.03, 0.07],
             'p_values': list(mock_simulation_results['iterations'][0].keys()),
             'type_ii_error_rate': 0.20,
             'type_ii_error_ci': [0.15, 0.25],
             'p_values_alt': list(mock_simulation_results['iterations'][0].keys()),
             'power_samples': [0.8] * 100
         }):
        
        result = save_baseline_results(
            dataset_name='test_dataset',
            sample_size=15,
            results_dir=results_dir,
            data_dir=data_dir,
            n_iterations=100,
            n_bootstrap=100,
            seed=42
        )
        
        assert result is not None
        assert 'null_path' in result
        assert 'alt_path' in result
        
        # Check files exist
        assert os.path.exists(result['null_path'])
        assert os.path.exists(result['alt_path'])
        
        # Check naming convention
        assert 'test_dataset_15_baseline_null.json' in result['null_path']
        assert 'test_dataset_15_baseline_alt.json' in result['alt_path']


def test_save_baseline_results_json_structure(tmp_path, mock_dataset, mock_simulation_results):
    """Test that saved JSON files have the correct structure."""
    results_dir = tmp_path / 'results'
    data_dir = tmp_path / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    dataset_path = data_dir / 'test_dataset.csv'
    mock_dataset.to_csv(dataset_path, index=False)
    
    mock_analysis = {
        'type_i_error_rate': 0.05,
        'type_i_error_ci': [0.03, 0.07],
        'p_values': [0.1, 0.2, 0.3] * 33 + [0.4],
        'type_ii_error_rate': 0.20,
        'type_ii_error_ci': [0.15, 0.25],
        'p_values_alt': [0.01, 0.02, 0.03] * 33 + [0.04],
        'power_samples': [0.8] * 100
    }
    
    with patch('save_baseline_results.load_dataset', return_value=mock_dataset), \
         patch('save_baseline_results.run_full_simulation', return_value=mock_simulation_results), \
         patch('save_baseline_results.analyze_baseline_results', return_value=mock_analysis):
        
        result = save_baseline_results(
            dataset_name='test_dataset',
            sample_size=15,
            results_dir=results_dir,
            data_dir=data_dir,
            n_iterations=100,
            n_bootstrap=100,
            seed=42
        )
        
        # Load and validate null results
        with open(result['null_path'], 'r') as f:
            null_data = json.load(f)
        
        assert null_data['type'] == 'null'
        assert null_data['dataset'] == 'test_dataset'
        assert null_data['sample_size'] == 15
        assert null_data['n_iterations'] == 100
        assert 'error_rate' in null_data
        assert 'error_rate_ci' in null_data
        assert 'metadata' in null_data
        assert 'disclaimer' in null_data['metadata']
        assert DISCLAIMER_TEXT in null_data['metadata']['disclaimer']
        
        # Load and validate alt results
        with open(result['alt_path'], 'r') as f:
            alt_data = json.load(f)
        
        assert alt_data['type'] == 'alt'
        assert alt_data['dataset'] == 'test_dataset'
        assert alt_data['sample_size'] == 15
        assert 'power' in alt_data
        assert 'error_rate' in alt_data
        assert 'metadata' in alt_data
        assert 'disclaimer' in alt_data['metadata']
        assert DISCLAIMER_TEXT in alt_data['metadata']['disclaimer']


def test_save_baseline_results_disclaimer_injection(tmp_path, mock_dataset, mock_simulation_results):
    """Test that disclaimer is injected into both null and alt results."""
    results_dir = tmp_path / 'results'
    data_dir = tmp_path / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    dataset_path = data_dir / 'test_dataset.csv'
    mock_dataset.to_csv(dataset_path, index=False)
    
    mock_analysis = {
        'type_i_error_rate': 0.05,
        'type_i_error_ci': [0.03, 0.07],
        'p_values': [0.1, 0.2, 0.3],
        'type_ii_error_rate': 0.20,
        'type_ii_error_ci': [0.15, 0.25],
        'p_values_alt': [0.01, 0.02, 0.03],
        'power_samples': [0.8] * 100
    }
    
    with patch('save_baseline_results.load_dataset', return_value=mock_dataset), \
         patch('save_baseline_results.run_full_simulation', return_value=mock_simulation_results), \
         patch('save_baseline_results.analyze_baseline_results', return_value=mock_analysis):
        
        result = save_baseline_results(
            dataset_name='test_dataset',
            sample_size=15,
            results_dir=results_dir,
            data_dir=data_dir,
            n_iterations=100,
            n_bootstrap=100,
            seed=42
        )
        
        # Check both files for disclaimer
        for file_path in [result['null_path'], result['alt_path']]:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            assert 'metadata' in data
            assert 'disclaimer' in data['metadata']
            assert DISCLAIMER_TEXT in data['metadata']['disclaimer']


def test_save_baseline_results_naming_convention(tmp_path, mock_dataset, mock_simulation_results):
    """Test that file naming follows the required convention."""
    results_dir = tmp_path / 'results'
    data_dir = tmp_path / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    dataset_path = data_dir / 'breast_cancer.csv'
    mock_dataset.to_csv(dataset_path, index=False)
    
    mock_analysis = {
        'type_i_error_rate': 0.05,
        'type_i_error_ci': [0.03, 0.07],
        'p_values': [0.1, 0.2, 0.3],
        'type_ii_error_rate': 0.20,
        'type_ii_error_ci': [0.15, 0.25],
        'p_values_alt': [0.01, 0.02, 0.03],
        'power_samples': [0.8] * 100
    }
    
    with patch('save_baseline_results.load_dataset', return_value=mock_dataset), \
         patch('save_baseline_results.run_full_simulation', return_value=mock_simulation_results), \
         patch('save_baseline_results.analyze_baseline_results', return_value=mock_analysis):
        
        result = save_baseline_results(
            dataset_name='breast_cancer',
            sample_size=25,
            results_dir=results_dir,
            data_dir=data_dir,
            n_iterations=100,
            n_bootstrap=100,
            seed=42
        )
        
        # Verify naming convention
        null_filename = os.path.basename(result['null_path'])
        alt_filename = os.path.basename(result['alt_path'])
        
        assert null_filename == 'breast_cancer_25_baseline_null.json'
        assert alt_filename == 'breast_cancer_25_baseline_alt.json'