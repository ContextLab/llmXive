import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path for imports
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)

from sensitivity_analysis import (
    load_json_file,
    save_json_file,
    load_model_coefficients,
    extract_lmm_coefficients,
    compare_against_literature,
    calculate_sensitivity_metrics,
    run_sensitivity_analysis
)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test artifacts."""
    return tmp_path

@pytest.fixture
def mock_model_metrics():
    """Mock model metrics data."""
    return {
        'lmm': {
            'coefficients': {
                'phosphorus': 0.25,
                'nitrogen': 0.18,
                'intercept': 1.2
            },
            'adjusted_r_squared': 0.72,
            'p_values': {
                'phosphorus': 0.001,
                'nitrogen': 0.003
            }
        },
        'random_forest': {
            'r_squared': 0.68,
            'rmse': 0.15
        }
    }

@pytest.fixture
def mock_literature_ranges():
    """Mock literature ranges data."""
    return {
        'phosphorus': {
            'min': 0.15,
            'max': 0.35,
            'mean': 0.25
        },
        'nitrogen': {
            'min': 0.10,
            'max': 0.25,
            'mean': 0.175
        }
    }

def test_load_json_file(tmp_path):
    """Test loading a JSON file."""
    test_data = {'key': 'value', 'number': 42}
    file_path = tmp_path / 'test.json'
    
    with open(file_path, 'w') as f:
        json.dump(test_data, f)
    
    loaded = load_json_file(file_path)
    assert loaded == test_data

def test_load_json_file_not_found():
    """Test that load_json_file raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_json_file(Path('/nonexistent/file.json'))

def test_save_json_file(tmp_path):
    """Test saving a JSON file."""
    test_data = {'key': 'value', 'number': 42}
    file_path = tmp_path / 'output.json'
    
    save_json_file(file_path, test_data)
    
    assert file_path.exists()
    with open(file_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == test_data

def test_extract_lmm_coefficients(mock_model_metrics):
    """Test extracting LMM coefficients from model metrics."""
    coeffs = extract_lmm_coefficients(mock_model_metrics)
    
    assert 'phosphorus' in coeffs
    assert 'nitrogen' in coeffs
    assert abs(coeffs['phosphorus'] - 0.25) < 1e-6
    assert abs(coeffs['nitrogen'] - 0.18) < 1e-6

def test_extract_lmm_coefficients_missing_data():
    """Test that extract_lmm_coefficients raises error for missing data."""
    incomplete_metrics = {'lmm': {}}
    
    with pytest.raises(ValueError):
        extract_lmm_coefficients(incomplete_metrics)

def test_compare_against_literature(mock_model_metrics, mock_literature_ranges):
    """Test comparing coefficients against literature ranges."""
    coeffs = extract_lmm_coefficients(mock_model_metrics)
    comparison = compare_against_literature(coeffs, mock_literature_ranges)
    
    assert 'phosphorus' in comparison
    assert 'nitrogen' in comparison
    
    # Check phosphorus
    assert abs(comparison['phosphorus']['observed'] - 0.25) < 1e-6
    assert abs(comparison['phosphorus']['literature_mean'] - 0.25) < 1e-6
    assert comparison['phosphorus']['literature_overlap'] is True  # 0.25 is within [0.15, 0.35]
    
    # Check nitrogen
    assert abs(comparison['nitrogen']['observed'] - 0.18) < 1e-6
    assert abs(comparison['nitrogen']['literature_mean'] - 0.175) < 1e-6
    assert comparison['nitrogen']['literature_overlap'] is True  # 0.18 is within [0.10, 0.25]

def test_compare_against_literature_no_overlap(mock_model_metrics, mock_literature_ranges):
    """Test comparison when coefficient is outside literature range."""
    # Create mock with coefficient outside range
    mock_metrics_outside = {
        'lmm': {
            'coefficients': {
                'phosphorus': 0.50,  # Outside [0.15, 0.35]
                'nitrogen': 0.18
            }
        }
    }
    
    coeffs = extract_lmm_coefficients(mock_metrics_outside)
    comparison = compare_against_literature(coeffs, mock_literature_ranges)
    
    assert comparison['phosphorus']['literature_overlap'] is False
    assert comparison['nitrogen']['literature_overlap'] is True

def test_calculate_sensitivity_metrics(mock_model_metrics, mock_literature_ranges):
    """Test calculating sensitivity metrics."""
    coeffs = extract_lmm_coefficients(mock_model_metrics)
    sensitivity = calculate_sensitivity_metrics(coeffs, mock_literature_ranges)
    
    assert 'phosphorus' in sensitivity
    assert 'nitrogen' in sensitivity
    
    # Check required keys
    for nutrient, metrics in sensitivity.items():
        assert 'percent_deviation' in metrics
        assert 'literature_mean' in metrics
        assert 'observed_coefficient' in metrics
        assert 'confidence_interval' in metrics
        assert 'literature_overlap' in metrics
        
        # Check confidence interval is a list of 2 floats
        assert isinstance(metrics['confidence_interval'], list)
        assert len(metrics['confidence_interval']) == 2
        assert all(isinstance(x, float) for x in metrics['confidence_interval'])

def test_calculate_sensitivity_metrics_with_perturbation(mock_model_metrics, mock_literature_ranges):
    """Test sensitivity calculation with different perturbation percentages."""
    coeffs = extract_lmm_coefficients(mock_model_metrics)
    
    # Default 10% perturbation
    sensitivity_10 = calculate_sensitivity_metrics(coeffs, mock_literature_ranges, perturbation_percent=10.0)
    
    # 5% perturbation
    sensitivity_5 = calculate_sensitivity_metrics(coeffs, mock_literature_ranges, perturbation_percent=5.0)
    
    # Confidence interval should be narrower with 5% perturbation
    p_ci_10 = sensitivity_10['phosphorus']['confidence_interval']
    p_ci_5 = sensitivity_5['phosphorus']['confidence_interval']
    
    range_10 = p_ci_10[1] - p_ci_10[0]
    range_5 = p_ci_5[1] - p_ci_5[0]
    
    assert range_5 < range_10  # 5% perturbation should give narrower CI

def test_run_sensitivity_analysis_integration(tmp_path, mock_model_metrics, mock_literature_ranges):
    """Test the full sensitivity analysis pipeline."""
    # Create necessary directories and files
    artifacts_dir = tmp_path / 'artifacts'
    reports_dir = artifacts_dir / 'reports'
    sensitivity_dir = artifacts_dir / 'sensitivity'
    
    reports_dir.mkdir(parents=True)
    sensitivity_dir.mkdir(parents=True)
    
    # Write mock model metrics
    metrics_path = reports_dir / 'model_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(mock_model_metrics, f)
    
    # Write mock literature ranges
    lit_path = artifacts_dir / 'literature_ranges.json'
    with open(lit_path, 'w') as f:
        json.dump(mock_literature_ranges, f)
    
    # Mock config
    config = {
        'ARTIFACTS_DIR': str(artifacts_dir)
    }
    
    # Run sensitivity analysis
    results = run_sensitivity_analysis(config)
    
    # Verify output file was created
    output_path = sensitivity_dir / 'sensitivity_analysis.json'
    assert output_path.exists()
    
    # Verify results structure
    assert 'results' in results
    assert 'phosphorus' in results['results']
    assert 'nitrogen' in results['results']
    
    # Verify required keys in output
    for nutrient, metrics in results['results'].items():
        assert 'percent_deviation' in metrics
        assert 'literature_mean' in metrics
        assert 'observed_coefficient' in metrics
        assert 'confidence_interval' in metrics
        assert 'literature_overlap' in metrics