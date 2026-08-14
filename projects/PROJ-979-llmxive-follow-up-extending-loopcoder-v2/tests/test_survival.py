"""
Tests for survival analysis module.
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
from src.survival import (
    load_entropy_results,
    load_convergence_results,
    prepare_survival_data,
    fit_kaplan_meier,
    fit_cox_model,
    run_survival_analysis
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_entropy_data(temp_dir):
    """Create sample entropy data CSV."""
    data = [
        {'task_id': 'task_1', 'entropy': 0.5},
        {'task_id': 'task_2', 'entropy': 1.2},
        {'task_id': 'task_3', 'entropy': 0.8},
        {'task_id': 'task_4', 'entropy': 1.5},
        {'task_id': 'task_5', 'entropy': 0.3},
    ]
    path = os.path.join(temp_dir, 'entropy_results.csv')
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def sample_convergence_data(temp_dir):
    """Create sample convergence data CSV."""
    data = [
        {'task_id': 'task_1', 'k': 1, 'is_correct': True, 'converged': True, 'first_correct_step': 1, 'censored': False},
        {'task_id': 'task_2', 'k': 1, 'is_correct': False, 'converged': False, 'first_correct_step': None, 'censored': False},
        {'task_id': 'task_2', 'k': 2, 'is_correct': True, 'converged': True, 'first_correct_step': 2, 'censored': False},
        {'task_id': 'task_3', 'k': 1, 'is_correct': False, 'converged': False, 'first_correct_step': None, 'censored': False},
        {'task_id': 'task_3', 'k': 2, 'is_correct': False, 'converged': False, 'first_correct_step': None, 'censored': False},
        {'task_id': 'task_3', 'k': 3, 'is_correct': False, 'converged': False, 'first_correct_step': None, 'censored': True},
        {'task_id': 'task_4', 'k': 1, 'is_correct': False, 'converged': False, 'first_correct_step': None, 'censored': False},
        {'task_id': 'task_4', 'k': 2, 'is_correct': True, 'converged': True, 'first_correct_step': 2, 'censored': False},
        {'task_id': 'task_5', 'k': 1, 'is_correct': True, 'converged': True, 'first_correct_step': 1, 'censored': False},
    ]
    path = os.path.join(temp_dir, 'convergence_results_core.csv')
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    return path

def test_load_entropy_results(sample_entropy_data):
    """Test loading entropy results."""
    df = load_entropy_results(sample_entropy_data)
    assert 'task_id' in df.columns
    assert 'entropy' in df.columns
    assert len(df) == 5

def test_load_convergence_results(sample_convergence_data):
    """Test loading convergence results."""
    df = load_convergence_results(sample_convergence_data)
    assert 'task_id' in df.columns
    assert 'k' in df.columns
    assert 'converged' in df.columns
    assert len(df) == 9  # Multiple rows per task

def test_prepare_survival_data(sample_entropy_data, sample_convergence_data):
    """Test preparing survival data from merged inputs."""
    entropy_df = load_entropy_results(sample_entropy_data)
    conv_df = load_convergence_results(sample_convergence_data)
    
    survival_df = prepare_survival_data(entropy_df, conv_df)
    
    assert 'task_id' in survival_df.columns
    assert 'time' in survival_df.columns
    assert 'event' in survival_df.columns
    assert 'entropy' in survival_df.columns
    
    # Should have 5 rows (one per task)
    assert len(survival_df) == 5
    
    # Check that task_3 is censored (event=0)
    task_3_row = survival_df[survival_df['task_id'] == 'task_3']
    assert len(task_3_row) == 1
    assert task_3_row['event'].iloc[0] == 0

def test_fit_kaplan_meier(sample_entropy_data, sample_convergence_data, temp_dir):
    """Test Kaplan-Meier fitting."""
    entropy_df = load_entropy_results(sample_entropy_data)
    conv_df = load_convergence_results(sample_convergence_data)
    survival_df = prepare_survival_data(entropy_df, conv_df)
    
    median_time, kmf = fit_kaplan_meier(survival_df)
    
    assert isinstance(median_time, float)
    assert median_time > 0
    assert kmf is not None

def test_fit_cox_model(sample_entropy_data, sample_convergence_data, temp_dir):
    """Test Cox PH model fitting."""
    entropy_df = load_entropy_results(sample_entropy_data)
    conv_df = load_convergence_results(sample_convergence_data)
    survival_df = prepare_survival_data(entropy_df, conv_df)
    
    hr, p_val, cph = fit_cox_model(survival_df)
    
    assert isinstance(hr, float)
    assert hr > 0
    assert isinstance(p_val, float)
    assert 0 <= p_val <= 1
    assert cph is not None

def test_run_survival_analysis(sample_entropy_data, sample_convergence_data, temp_dir):
    """Test full survival analysis pipeline."""
    output_path = os.path.join(temp_dir, 'correlation_results.json')
    
    results = run_survival_analysis(sample_entropy_data, sample_convergence_data, output_path)
    
    # Verify output file exists
    assert os.path.exists(output_path)
    
    # Verify results structure
    assert 'hazard_ratio' in results
    assert 'p_value' in results
    assert 'median_survival_time' in results
    assert 'power_analysis' in results
    
    # Verify power analysis structure
    assert 'mdes' in results['power_analysis']
    assert 'power' in results['power_analysis']
    
    # Verify values are reasonable
    assert results['hazard_ratio'] > 0
    assert 0 <= results['p_value'] <= 1
    assert results['median_survival_time'] > 0

def test_missing_entropy_file(temp_dir):
    """Test error handling for missing entropy file."""
    with pytest.raises(FileNotFoundError):
        load_entropy_results(os.path.join(temp_dir, 'nonexistent.csv'))

def test_missing_convergence_file(temp_dir):
    """Test error handling for missing convergence file."""
    with pytest.raises(FileNotFoundError):
        load_convergence_results(os.path.join(temp_dir, 'nonexistent.csv'))

def test_invalid_entropy_columns(temp_dir):
    """Test error handling for invalid entropy columns."""
    path = os.path.join(temp_dir, 'bad_entropy.csv')
    df = pd.DataFrame({'wrong_col': [1, 2, 3]})
    df.to_csv(path, index=False)
    
    with pytest.raises(ValueError):
        load_entropy_results(path)

def test_invalid_convergence_columns(temp_dir):
    """Test error handling for invalid convergence columns."""
    path = os.path.join(temp_dir, 'bad_conv.csv')
    df = pd.DataFrame({'wrong_col': [1, 2, 3]})
    df.to_csv(path, index=False)
    
    with pytest.raises(ValueError):
        load_convergence_results(path)