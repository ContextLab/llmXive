"""
Integration tests for report generation (T026).

Tests the full pipeline of report generation including:
- Loading model metrics
- Computing adjusted p-values
- Generating comparison tables
- Evaluating scientific success criterion
- Writing JSON output
"""

import os
import json
import tempfile
import pickle
from pathlib import Path
import pytest
import numpy as np

# Import functions to test
from report_generator import (
    generate_full_report,
    compute_scientific_success_criterion,
    generate_comparison_table,
    load_model_metrics
)
from model import compute_bonferroni_pvalue, compute_benjamini_hochberg_pvalues


@pytest.fixture
def temp_model_dir():
    """Create a temporary directory with mock model files."""
    temp_dir = tempfile.mkdtemp()
    
    # Create mock Ridge model metrics for logS
    logS_metrics = {
        'metrics': {
            'rmse': 0.85,
            'r2': 0.72,
            'pearson_r': 0.85,
            'p_value': 0.001,
            'alpha': 1.0
        }
    }
    
    # Create mock Ridge model metrics for logP
    logP_metrics = {
        'metrics': {
            'rmse': 0.65,
            'r2': 0.68,
            'pearson_r': 0.82,
            'p_value': 0.003,
            'alpha': 1.0
        }
    }
    
    # Save mock models
    with open(os.path.join(temp_dir, 'ridge_logS.pkl'), 'wb') as f:
        pickle.dump(logS_metrics, f)
    
    with open(os.path.join(temp_dir, 'ridge_logP.pkl'), 'wb') as f:
        pickle.dump(logP_metrics, f)
    
    return temp_dir


@pytest.fixture
def temp_baseline_dir():
    """Create a temporary directory with mock baseline results."""
    temp_dir = tempfile.mkdtemp()
    
    baseline_results = {
        'logS': {
            'rmse': 1.10,
            'r2': 0.45,
            'model_type': 'size_baseline'
        },
        'logP': {
            'rmse': 0.90,
            'r2': 0.50,
            'model_type': 'size_baseline'
        }
    }
    
    baseline_path = os.path.join(temp_dir, 'baseline_metrics.json')
    with open(baseline_path, 'w') as f:
        json.dump(baseline_results, f)
    
    return temp_dir


def test_load_model_metrics(temp_model_dir):
    """Test loading metrics from a model pickle file."""
    model_path = os.path.join(temp_model_dir, 'ridge_logS.pkl')
    metrics = load_model_metrics(model_path)
    
    assert 'rmse' in metrics
    assert metrics['rmse'] == 0.85
    assert metrics['r2'] == 0.72
    assert metrics['pearson_r'] == 0.85


def test_load_model_metrics_file_not_found():
    """Test that FileNotFoundError is raised for missing model."""
    with pytest.raises(FileNotFoundError):
        load_model_metrics('/nonexistent/path/model.pkl')


def test_compute_scientific_success_criterion():
    """Test the scientific success criterion evaluation."""
    # Case 1: Entropy outperforms size baseline
    result = compute_scientific_success_criterion(0.85, 1.10)
    assert result['criterion_met'] is True
    assert result['improvement_percentage'] > 0
    
    # Case 2: Entropy does not outperform size baseline
    result = compute_scientific_success_criterion(1.20, 1.10)
    assert result['criterion_met'] is False
    assert result['improvement_percentage'] < 0
    
    # Case 3: Equal performance
    result = compute_scientific_success_criterion(1.0, 1.0)
    assert result['criterion_met'] is False
    assert result['improvement_percentage'] == 0.0


def test_generate_comparison_table():
    """Test generation of entropy-vs-size comparison table."""
    entropy_metrics = {
        'logS_entropy_rmse': 0.85,
        'logS_entropy_r2': 0.72,
        'logP_entropy_rmse': 0.65,
        'logP_entropy_r2': 0.68
    }
    
    baseline_metrics = {
        'logS_size_baseline_rmse': 1.10,
        'logS_size_baseline_r2': 0.45,
        'logP_size_baseline_rmse': 0.90,
        'logP_size_baseline_r2': 0.50
    }
    
    table = generate_comparison_table(entropy_metrics, baseline_metrics)
    
    assert len(table) == 4  # 2 properties * 2 metrics each
    
    # Check RMSE entries
    rmse_logS = next(row for row in table if row['property'] == 'logS' and row['metric'] == 'RMSE')
    assert rmse_logS['entropy_model'] == 0.85
    assert rmse_logS['size_baseline'] == 1.10
    assert rmse_logS['difference'] == -0.25  # 0.85 - 1.10


def test_generate_full_report(temp_model_dir, temp_baseline_dir, tmp_path):
    """Test full report generation with all components."""
    output_path = str(tmp_path / 'metrics.json')
    
    report = generate_full_report(temp_model_dir, temp_baseline_dir, output_path)
    
    # Verify report structure
    assert 'report_type' in report
    assert 'models' in report
    assert 'comparison' in report
    assert 'scientific_success_criterion' in report
    assert 'p_value_adjustments' in report
    
    # Verify model metrics
    assert 'logS' in report['models']
    assert 'logP' in report['models']
    assert report['models']['logS']['rmse'] == 0.85
    assert report['models']['logP']['rmse'] == 0.65
    
    # Verify adjusted p-values
    assert 'bonferroni_adjusted_p' in report['models']['logS']
    assert 'benjamini_hochberg_adjusted_p' in report['models']['logS']
    
    # Verify comparison table
    assert 'entropy_vs_size_table' in report['comparison']
    assert len(report['comparison']['entropy_vs_size_table']) == 4
    
    # Verify scientific success criterion
    assert 'logS' in report['scientific_success_criterion']
    assert report['scientific_success_criterion']['logS']['criterion_met'] is True
    
    # Verify output file was created
    assert os.path.exists(output_path)
    
    # Verify JSON is valid
    with open(output_path, 'r') as f:
        loaded_report = json.load(f)
    assert loaded_report == report


def test_p_value_adjustments():
    """Test Bonferroni and Benjamini-Hochberg p-value adjustments."""
    # Test Bonferroni
    raw_p = 0.01
    bonf_p = compute_bonferroni_pvalue(raw_p, num_tests=5)
    assert bonf_p == 0.05  # 0.01 * 5
    
    # Test Benjamini-Hochberg
    p_values = [0.01, 0.03, 0.05, 0.10]
    adjusted_p = compute_benjamini_hochberg_pvalues(p_values)
    assert len(adjusted_p) == 4
    # BH adjustment should result in non-decreasing adjusted p-values
    assert all(adjusted_p[i] <= adjusted_p[i+1] for i in range(len(adjusted_p)-1))


def test_report_with_missing_models(tmp_path):
    """Test report generation when some model files are missing."""
    temp_model_dir = tempfile.mkdtemp()
    temp_baseline_dir = tempfile.mkdtemp()
    
    # Only create logS model
    logS_metrics = {'metrics': {'rmse': 0.85, 'r2': 0.72, 'pearson_r': 0.85, 'p_value': 0.001}}
    with open(os.path.join(temp_model_dir, 'ridge_logS.pkl'), 'wb') as f:
        pickle.dump(logS_metrics, f)
    
    baseline_results = {
        'logS': {'rmse': 1.10, 'r2': 0.45},
        'logP': {'rmse': 0.90, 'r2': 0.50}
    }
    with open(os.path.join(temp_baseline_dir, 'baseline_metrics.json'), 'w') as f:
        json.dump(baseline_results, f)
    
    output_path = str(tmp_path / 'metrics_partial.json')
    report = generate_full_report(temp_model_dir, temp_baseline_dir, output_path)
    
    # Only logS should be in models
    assert 'logS' in report['models']
    assert 'logP' not in report['models']
    
    # Scientific success criterion should only have logS
    assert 'logS' in report['scientific_success_criterion']
    assert 'logP' not in report['scientific_success_criterion']