import os
import json
import csv
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add the code directory to the path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.aggregation import (
    load_bias_summary_results,
    load_null_model_baseline,
    load_sensitivity_results,
    filter_valid_realizations,
    generate_aggregation_report,
    save_aggregation_report,
    run_aggregation_pipeline
)
from config import DATA_RESULTS_DIR, MIN_REALIZATIONS

@pytest.fixture
def temp_results_dir():
    """Create a temporary directory for test results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create the necessary subdirectories
        os.makedirs(os.path.join(tmpdir, 'data', 'results'), exist_ok=True)
        
        # Patch the config to use our temp directory
        with patch('analysis.aggregation.DATA_RESULTS_DIR', os.path.join(tmpdir, 'data', 'results')):
            yield os.path.join(tmpdir, 'data', 'results')

@pytest.fixture
def sample_bias_data(temp_results_dir):
    """Create sample bias summary CSV data."""
    bias_path = os.path.join(temp_results_dir, 'bias_summary.csv')
    
    # Create sample data
    sample_data = [
        {
            'realization_id': 'sim_001',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.02,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_002',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.05,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_003',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.03,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_004',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.04,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_005',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.06,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_006',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.025,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_007',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.035,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_008',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.045,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_009',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.028,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_010',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.032,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_011',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.048,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_012',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.027,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_013',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.033,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_014',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.047,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_015',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.026,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_016',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.031,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_017',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.049,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_018',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.024,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_019',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.034,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_020',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.046,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_021',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.029,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_022',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.036,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_023',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.051,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_024',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.023,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_025',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.037,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_026',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.052,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_027',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.022,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_028',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.038,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_029',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.053,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_030',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.021,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_031',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.039,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_032',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.054,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_033',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.020,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_034',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.040,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_035',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.055,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_036',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.019,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_037',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.041,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_038',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.056,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_039',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.018,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_040',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.042,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_041',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.057,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_042',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.017,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_043',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.043,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_044',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.058,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_045',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.016,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_046',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.044,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_047',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.059,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_048',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': 0.015,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_049',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.045,
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_050',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.060,
            'passed_null_test': True
        },
        # Add some invalid entries
        {
            'realization_id': 'sim_051',
            'algorithm': 'iterative_synthesis',
            'gap_fraction': 0.15,
            'morphology': 'point_source',
            'bias_magnitude': float('nan'),  # NaN value
            'passed_null_test': True
        },
        {
            'realization_id': 'sim_052',
            'algorithm': 'harmonic_interp',
            'gap_fraction': 0.05,
            'morphology': 'random',
            'bias_magnitude': 0.046,
            'passed_null_test': False  # Failed null test
        },
        {
            'realization_id': 'sim_053',
            'algorithm': 'wiener_filter',
            'gap_fraction': 0.10,
            'morphology': 'clustered',
            'bias_magnitude': 0.061,
            'passed_null_test': True
        }
    ]
    
    with open(bias_path, 'w', newline='') as csvfile:
        fieldnames = ['realization_id', 'algorithm', 'gap_fraction', 'morphology', 
                    'bias_magnitude', 'passed_null_test']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_data)
    
    return temp_results_dir

def test_load_bias_summary_results(sample_bias_data):
    """Test loading bias summary results from CSV."""
    results = load_bias_summary_results()
    assert len(results) == 53, f"Expected 53 results, got {len(results)}"
    
    # Check that numeric fields are properly converted
    assert isinstance(results[0]['bias_magnitude'], float)
    assert isinstance(results[0]['gap_fraction'], float)
    
    # Check that NaN values are handled
    nan_entries = [r for r in results if r['bias_magnitude'] != r['bias_magnitude']]
    assert len(nan_entries) == 1, f"Expected 1 NaN entry, got {len(nan_entries)}"

def test_filter_valid_realizations(sample_bias_data):
    """Test filtering of valid realizations."""
    bias_results = load_bias_summary_results()
    valid, excluded = filter_valid_realizations(bias_results, min_realizations=30)
    
    # Should have at least 30 valid realizations
    assert len(valid) >= 30, f"Expected at least 30 valid realizations, got {len(valid)}"
    
    # Should have excluded the NaN and failed null test entries
    assert len(excluded) >= 2, f"Expected at least 2 excluded realizations, got {len(excluded)}"
    
    # Check exclusion reasons
    excluded_ids = [e['realization_id'] for e in excluded]
    assert 'sim_051' in excluded_ids, "sim_051 (NaN) should be excluded"
    assert 'sim_052' in excluded_ids, "sim_052 (failed null test) should be excluded"

def test_generate_aggregation_report(sample_bias_data):
    """Test generation of aggregation report."""
    bias_results = load_bias_summary_results()
    valid, excluded = filter_valid_realizations(bias_results)
    
    report = generate_aggregation_report(valid, excluded, None, None)
    
    # Check report structure
    assert 'summary' in report
    assert 'statistics' in report
    assert 'excluded_realizations' in report
    
    # Check summary
    assert report['summary']['valid_count'] == len(valid)
    assert report['summary']['excluded_count'] == len(excluded)
    assert report['summary']['min_realizations_met'] is True
    
    # Check statistics
    assert 'mean_bias' in report['statistics']
    assert 'std_bias' in report['statistics']
    assert 'median_bias' in report['statistics']
    
    # Verify statistics are reasonable
    assert report['statistics']['mean_bias'] > 0
    assert report['statistics']['std_bias'] >= 0

def test_save_aggregation_report(sample_bias_data, temp_results_dir):
    """Test saving aggregation report to file."""
    bias_results = load_bias_summary_results()
    valid, excluded = filter_valid_realizations(bias_results)
    report = generate_aggregation_report(valid, excluded, None, None)
    
    output_path = os.path.join(temp_results_dir, 'test_report.json')
    saved_path = save_aggregation_report(report, output_path)
    
    assert saved_path == output_path
    assert os.path.exists(output_path)
    
    # Verify file contents
    with open(output_path, 'r') as f:
        loaded_report = json.load(f)
    
    assert loaded_report['summary']['valid_count'] == report['summary']['valid_count']

def test_run_aggregation_pipeline(sample_bias_data, temp_results_dir):
    """Test the full aggregation pipeline."""
    report = run_aggregation_pipeline()
    
    assert report is not None
    assert 'summary' in report
    assert 'statistics' in report
    
    # Check that the report was saved
    report_path = os.path.join(temp_results_dir, 'aggregation_report.json')
    assert os.path.exists(report_path)