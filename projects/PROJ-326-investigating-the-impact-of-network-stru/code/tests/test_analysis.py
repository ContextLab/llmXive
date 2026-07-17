"""
Tests for analysis modules including sensitivity sweep.
"""
import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from code.src.analysis.sensitivity import (
    SensitivityError,
    load_simulation_data,
    filter_by_clustering_threshold,
    compute_sensitivity_metrics,
    run_sensitivity_sweep,
    verify_sensitivity_results
)
from code.src.analysis.regression import fit_linear_regression

@pytest.fixture
def sample_simulation_data(tmp_path):
    """Create sample simulation data for testing."""
    data = {
        'clustering_coefficient': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        'diffusion_rate': [0.05, 0.08, 0.12, 0.15, 0.18, 0.22, 0.25, 0.28, 0.32, 0.35],
        'topology_class': ['erdos_renyi'] * 10
    }
    df = pd.DataFrame(data)
    output_file = tmp_path / "simulation_results.json"
    with open(output_file, 'w') as f:
        json.dump(data, f)
    return df, tmp_path

def test_filter_by_clustering_threshold_ge(sample_simulation_data):
    """Test filtering with >= operator."""
    df, _ = sample_simulation_data
    filtered = filter_by_clustering_threshold(df, 0.5, '>=' )
    assert len(filtered) == 6  # 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
    assert all(filtered['clustering_coefficient'] >= 0.5)

def test_filter_by_clustering_threshold_le(sample_simulation_data):
    """Test filtering with <= operator."""
    df, _ = sample_simulation_data
    filtered = filter_by_clustering_threshold(df, 0.3, '<=')
    assert len(filtered) == 4  # 0.1, 0.2, 0.3
    assert all(filtered['clustering_coefficient'] <= 0.3)

def test_filter_by_clustering_threshold_invalid_threshold(sample_simulation_data):
    """Test that invalid threshold raises SensitivityError."""
    df, _ = sample_simulation_data
    with pytest.raises(SensitivityError):
        filter_by_clustering_threshold(df, 1.5)
    
    with pytest.raises(SensitivityError):
        filter_by_clustering_threshold(df, -0.1)

def test_filter_by_clustering_threshold_invalid_operator(sample_simulation_data):
    """Test that invalid operator raises SensitivityError."""
    df, _ = sample_simulation_data
    with pytest.raises(SensitivityError):
        filter_by_clustering_threshold(df, 0.5, 'invalid_op')

def test_compute_sensitivity_metrics(sample_simulation_data):
    """Test computation of sensitivity metrics."""
    df, _ = sample_simulation_data
    metrics = compute_sensitivity_metrics(df, 0.5)
    
    assert metrics['threshold'] == 0.5
    assert metrics['sample_size'] == 6
    assert 'mean_diffusion_rate' in metrics
    assert 'std_diffusion_rate' in metrics
    assert metrics['regression'] is not None
    assert 'slope' in metrics['regression']
    assert 'r_squared' in metrics['regression']

def test_run_sensitivity_sweep(sample_simulation_data):
    """Test running a sensitivity sweep."""
    df, _ = sample_simulation_data
    thresholds = [0.3, 0.5, 0.7]
    results = run_sensitivity_sweep(df, thresholds)
    
    assert len(results) == 3
    for r in results:
        assert 'threshold' in r
        assert 'sample_size' in r
        assert 'mean_diffusion_rate' in r

def test_verify_sensitivity_results(sample_simulation_data):
    """Test verification of sensitivity results."""
    df, tmp_path = sample_simulation_data
    thresholds = [0.3, 0.5, 0.7]
    results = run_sensitivity_sweep(df, thresholds)
    
    config = {'sensitivity': {'thresholds': thresholds}}
    assert verify_sensitivity_results(results, config) is True

def test_verify_sensitivity_results_missing_threshold(sample_simulation_data):
    """Test verification fails when a threshold is missing."""
    df, tmp_path = sample_simulation_data
    thresholds = [0.3, 0.5, 0.7]
    # Run sweep with only 2 thresholds
    results = run_sensitivity_sweep(df, [0.3, 0.5])
    
    config = {'sensitivity': {'thresholds': thresholds}}
    with pytest.raises(SensitivityError):
        verify_sensitivity_results(results, config)

def test_threshold_validation_in_sensitivity_sweep(sample_simulation_data):
    """Test that distinct thresholds are validated correctly."""
    df, tmp_path = sample_simulation_data
    # Test with distinct thresholds
    thresholds = [0.0, 0.25, 0.5, 0.75, 1.0]
    results = run_sensitivity_sweep(df, thresholds)
    
    # Verify all distinct thresholds are present
    result_thresholds = [r['threshold'] for r in results if 'error' not in r]
    for t in thresholds:
        assert t in result_thresholds, f"Threshold {t} missing from results"

def test_regression_in_sensitivity_metrics(sample_simulation_data):
    """Test that regression is computed correctly in sensitivity metrics."""
    df, _ = sample_simulation_data
    metrics = compute_sensitivity_metrics(df, 0.5)
    
    # Check regression results
    assert metrics['regression'] is not None
    assert isinstance(metrics['regression']['slope'], float)
    assert isinstance(metrics['regression']['r_squared'], float)
    # For this data, we expect a positive correlation
    assert metrics['regression']['slope'] > 0
    assert metrics['regression']['r_squared'] > 0.9  # High R-squared for this data

def test_sensitivity_sweep_thresholds(sample_simulation_data):
    """
    Unit test for sensitivity sweep thresholds (SC-005 requirement).
    Verifies that the sweep uses at least 5 distinct cutoffs and reports
    how diffusion rates vary across the sweep.
    """
    df, tmp_path = sample_simulation_data
    
    # Test with exactly 5 thresholds (minimum per SC-005)
    thresholds = [0.0, 0.25, 0.5, 0.75, 1.0]
    results = run_sensitivity_sweep(df, thresholds)
    
    # Verify we have results for all 5 thresholds
    assert len(results) == 5
    
    # Verify each result has the required fields
    for r in results:
        assert 'threshold' in r
        assert 'sample_size' in r
        assert 'mean_diffusion_rate' in r
        assert 'regression' in r
        
        # Verify regression reports how diffusion varies
        if r['regression'] is not None:
            assert 'slope' in r['regression']
            assert 'r_squared' in r['regression']
    
    # Verify the diffusion rates vary across thresholds
    diffusion_rates = [r['mean_diffusion_rate'] for r in results if r['mean_diffusion_rate'] is not None]
    assert len(diffusion_rates) > 1
    
    # Check that there is variation (not all same value)
    assert len(set(diffusion_rates)) > 1 or len(diffusion_rates) == 1
    
    # Verify the slope indicates relationship between clustering and diffusion
    slopes = [r['regression']['slope'] for r in results if r['regression'] and r['regression']['slope'] is not None]
    if slopes:
        # At least some thresholds should show a relationship
        assert any(abs(s) > 0.001 for s in slopes)

def test_sensitivity_sweep_with_real_data_structure(tmp_path):
    """Test sensitivity sweep with data structure matching real simulation output."""
    # Create data matching real simulation_results.json schema
    real_data = {
        'network_id': ['net_001', 'net_002', 'net_003', 'net_004', 'net_005'],
        'clustering_coefficient': [0.15, 0.35, 0.55, 0.75, 0.95],
        'diffusion_rate': [0.08, 0.14, 0.21, 0.28, 0.33],
        'topology_class': ['scale_free', 'small_world', 'erdos_renyi', 'small_world', 'scale_free'],
        'seed': [42, 43, 44, 45, 46],
        'steps_run': [100, 100, 100, 100, 100],
        'status': ['COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED']
    }
    
    output_file = tmp_path / "simulation_results.json"
    with open(output_file, 'w') as f:
        json.dump(real_data, f)
    
    df = pd.DataFrame(real_data)
    
    # Run sweep with 5 thresholds
    thresholds = [0.0, 0.25, 0.5, 0.75, 1.0]
    results = run_sensitivity_sweep(df, thresholds)
    
    # Verify results
    assert len(results) == 5
    for i, r in enumerate(results):
        assert r['threshold'] == thresholds[i]
        assert 'sample_size' in r
        assert 'mean_diffusion_rate' in r
        assert r['regression'] is not None
        assert 'slope' in r['regression']
        assert 'r_squared' in r['regression']