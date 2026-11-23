"""
Tests for comparative analysis logic (T027).
"""
import os
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Import the module under test
from code.compare_results import (
    load_all_results,
    categorize_results,
    calculate_error_rate_difference,
    generate_comparative_analysis,
    save_comparative_analysis
)

@pytest.fixture
def mock_results_dir(tmp_path):
    """Create a temporary directory with mock result JSON files."""
    # Create directory structure
    results_dir = tmp_path / 'results'
    results_dir.mkdir()
    
    # Mock baseline null
    baseline_null = {
        'metadata': {'dataset': 'test_ds', 'size': 25, 'condition': 'null', 'method': 'baseline'},
        'error_rates': {'type_i_error_rate': 0.05, 'type_ii_error_rate': 0.20}
    }
    with open(results_dir / 'test_ds_25_baseline_null.json', 'w') as f:
        json.dump(baseline_null, f)
    
    # Mock baseline alt
    baseline_alt = {
        'metadata': {'dataset': 'test_ds', 'size': 25, 'condition': 'alt', 'method': 'baseline'},
        'error_rates': {'type_i_error_rate': 0.05, 'type_ii_error_rate': 0.20}
    }
    with open(results_dir / 'test_ds_25_baseline_alt.json', 'w') as f:
        json.dump(baseline_alt, f)
    
    # Mock gaussian null
    gaussian_null = {
        'metadata': {'dataset': 'test_ds', 'size': 25, 'condition': 'null', 'method': 'gaussian'},
        'error_rates': {'type_i_error_rate': 0.08, 'type_ii_error_rate': 0.18}
    }
    with open(results_dir / 'test_ds_25_gaussian_null.json', 'w') as f:
        json.dump(gaussian_null, f)
    
    # Mock gaussian alt
    gaussian_alt = {
        'metadata': {'dataset': 'test_ds', 'size': 25, 'condition': 'alt', 'method': 'gaussian'},
        'error_rates': {'type_i_error_rate': 0.08, 'type_ii_error_rate': 0.15}
    }
    with open(results_dir / 'test_ds_25_gaussian_alt.json', 'w') as f:
        json.dump(gaussian_alt, f)
    
    # Mock smote null (missing baseline to test skipping)
    smote_null = {
        'metadata': {'dataset': 'other_ds', 'size': 25, 'condition': 'null', 'method': 'smote'},
        'error_rates': {'type_i_error_rate': 0.06, 'type_ii_error_rate': 0.19}
    }
    with open(results_dir / 'other_ds_25_smote_null.json', 'w') as f:
        json.dump(smote_null, f)

    return results_dir

def test_load_all_results(mock_results_dir):
    """Test loading all results from directory."""
    results = load_all_results(mock_results_dir)
    assert len(results) == 5
    assert any('baseline_null' in k for k in results.keys())
    assert any('gaussian_null' in k for k in results.keys())

def test_categorize_results(mock_results_dir):
    """Test categorizing results by dataset, size, condition, method."""
    results = load_all_results(mock_results_dir)
    categorized = categorize_results(results)
    
    assert 'test_ds' in categorized
    assert '25' in categorized['test_ds']
    assert 'null' in categorized['test_ds']['25']
    assert 'alt' in categorized['test_ds']['25']
    assert 'baseline' in categorized['test_ds']['25']['null']
    assert 'gaussian' in categorized['test_ds']['25']['null']
    
    # other_ds should exist but have no baseline, so it might be skipped in later steps
    assert 'other_ds' in categorized
    
def test_calculate_error_rate_difference():
    """Test calculation of error rate differences."""
    baseline = {'error_rates': {'type_i_error_rate': 0.05, 'type_ii_error_rate': 0.20}}
    augmented = {'error_rates': {'type_i_error_rate': 0.08, 'type_ii_error_rate': 0.15}}
    
    # Test Type I
    result_i = calculate_error_rate_difference(baseline, augmented, 'null', 'type_i_error_rate')
    assert result_i['status'] == 'calculated'
    assert result_i['baseline_rate'] == 0.05
    assert result_i['augmented_rate'] == 0.08
    assert result_i['difference'] == 0.03
    
    # Test Type II
    result_ii = calculate_error_rate_difference(baseline, augmented, 'alt', 'type_ii_error_rate')
    assert result_ii['status'] == 'calculated'
    assert result_ii['baseline_rate'] == 0.20
    assert result_ii['augmented_rate'] == 0.15
    assert result_ii['difference'] == -0.05
    
    # Test missing data
    bad_augmented = {'error_rates': {'type_i_error_rate': 0.08}}
    result_missing = calculate_error_rate_difference(baseline, bad_augmented, 'null', 'type_ii_error_rate')
    assert result_missing['status'] == 'missing_data'

def test_generate_comparative_analysis(mock_results_dir):
    """Test generating the comparative analysis DataFrame."""
    results = load_all_results(mock_results_dir)
    categorized = categorize_results(results)
    df = generate_comparative_analysis(categorized)
    
    assert not df.empty
    assert 'dataset' in df.columns
    assert 'difference' in df.columns
    
    # Check specific values
    gaussian_null_row = df[(df['method'] == 'gaussian') & (df['condition'] == 'null') & (df['metric'] == 'type_i_error_rate')]
    assert not gaussian_null_row.empty
    assert gaussian_null_row['difference'].values[0] == 0.03
    
def test_save_comparative_analysis(mock_results_dir, tmp_path):
    """Test saving the comparative analysis to CSV."""
    results = load_all_results(mock_results_dir)
    categorized = categorize_results(results)
    df = generate_comparative_analysis(categorized)
    
    output_path = tmp_path / 'test_analysis.csv'
    save_comparative_analysis(df, output_path)
    
    assert output_path.exists()
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == len(df)
    assert 'dataset' in saved_df.columns