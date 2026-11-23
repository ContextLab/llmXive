"""
Tests for the export energy results functionality.

Tests the classification logic, CSV export, and report generation.
"""
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.export_energy_results import (
    classify_instance,
    export_results_to_csv,
    generate_final_report,
    DECAY_THRESHOLD,
    R_SQUARED_THRESHOLD,
    RESONANT_DECAY_TOLERANCE
)

@pytest.fixture
def sample_results():
    """Sample simulation results for testing."""
    return [
        {
            'graph_id': 'graph_001',
            'class': 'random',
            'N': 100,
            'decay_rate': 0.05,
            'r_squared': 0.98,
            'fit_status': 'success',
            'driving_frequency': 1.0,
            'damping_coefficient': 0.1
        },
        {
            'graph_id': 'graph_002',
            'class': 'scale_free',
            'N': 150,
            'decay_rate': -0.02,  # Negative decay (resonance)
            'r_squared': 0.96,
            'fit_status': 'success',
            'driving_frequency': 1.0,
            'damping_coefficient': 0.1
        },
        {
            'graph_id': 'graph_003',
            'class': 'small_world',
            'N': 120,
            'decay_rate': 0.0,  # Near-zero decay (resonance)
            'r_squared': 0.97,
            'fit_status': 'success',
            'driving_frequency': 1.0,
            'damping_coefficient': 0.1
        },
        {
            'graph_id': 'graph_004',
            'class': 'lattice',
            'N': 100,
            'decay_rate': 0.03,
            'r_squared': 0.92,  # Below threshold (resonance)
            'fit_status': 'success',
            'driving_frequency': 1.0,
            'damping_coefficient': 0.1
        },
        {
            'graph_id': 'graph_005',
            'class': 'star',
            'N': 110,
            'decay_rate': 0.04,
            'r_squared': 0.99,
            'fit_status': 'failed',  # Fit failure (resonance)
            'driving_frequency': 1.0,
            'damping_coefficient': 0.1
        }
    ]

def test_classify_dissipative():
    """Test classification of a dissipative instance."""
    status = classify_instance(0.05, 0.98, 'success')
    assert status == 'dissipative'

def test_classify_negative_decay():
    """Test classification of negative decay (resonance)."""
    status = classify_instance(-0.02, 0.96, 'success')
    assert status == 'resonant'

def test_classify_zero_decay():
    """Test classification of near-zero decay (resonance)."""
    status = classify_instance(0.0, 0.97, 'success')
    assert status == 'resonant'

def test_classify_low_r_squared():
    """Test classification of low R² (resonance)."""
    status = classify_instance(0.03, 0.92, 'success')
    assert status == 'resonant'

def test_classify_fit_failure():
    """Test classification of fit failure (resonance)."""
    status = classify_instance(0.04, 0.99, 'failed')
    assert status == 'resonant'

def test_classify_very_small_decay():
    """Test classification of very small positive decay (resonance)."""
    status = classify_instance(1e-7, 0.98, 'success')
    assert status == 'resonant'

def test_export_results_to_csv(sample_results, tmp_path):
    """Test export of results to CSV with correct classification."""
    output_path = str(tmp_path / 'energy_decay.csv')
    report_path = str(tmp_path / 'exclusion_report.json')

    df, counts = export_results_to_csv(sample_results, output_path)

    # Verify file exists
    assert os.path.exists(output_path)

    # Verify DataFrame structure
    assert len(df) == 5
    assert 'graph_id' in df.columns
    assert 'status' in df.columns

    # Verify classifications
    assert df.loc[df['graph_id'] == 'graph_001', 'status'].values[0] == 'dissipative'
    assert df.loc[df['graph_id'] == 'graph_002', 'status'].values[0] == 'resonant'
    assert df.loc[df['graph_id'] == 'graph_003', 'status'].values[0] == 'resonant'
    assert df.loc[df['graph_id'] == 'graph_004', 'status'].values[0] == 'resonant'
    assert df.loc[df['graph_id'] == 'graph_005', 'status'].values[0] == 'resonant'

    # Verify counts
    assert counts['total'] == 5
    assert counts['dissipative'] == 1
    assert counts['resonant'] == 4

def test_export_results_empty():
    """Test export with empty results raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'energy_decay.csv')
        with pytest.raises(ValueError, match="No simulation results to export"):
            export_results_to_csv([], output_path)

def test_generate_final_report(tmp_path):
    """Test generation of exclusion report."""
    report_path = str(tmp_path / 'exclusion_report.json')
    counts = {'total': 50, 'dissipative': 48, 'resonant': 2}

    generate_final_report(counts, report_path)

    assert os.path.exists(report_path)

    with open(report_path, 'r') as f:
        data = json.load(f)

    assert data['total_simulations'] == 50
    assert data['dissipative_count'] == 48
    assert data['resonant_count'] == 2
    assert data['exclusion_rate'] == 0.04
    assert 'timestamp' in data

def test_csv_columns_order(sample_results, tmp_path):
    """Test that CSV columns are in the correct order."""
    output_path = str(tmp_path / 'energy_decay.csv')
    df, _ = export_results_to_csv(sample_results, output_path)

    expected_columns = [
        'graph_id', 'class', 'N', 'decay_rate', 'r_squared',
        'fit_status', 'driving_frequency', 'damping_coefficient', 'status'
    ]

    assert list(df.columns) == expected_columns

def test_csv_data_types(sample_results, tmp_path):
    """Test that CSV data types are correct."""
    output_path = str(tmp_path / 'energy_decay.csv')
    df, _ = export_results_to_csv(sample_results, output_path)

    # Check numeric columns
    assert pd.api.types.is_numeric_dtype(df['N'])
    assert pd.api.types.is_numeric_dtype(df['decay_rate'])
    assert pd.api.types.is_numeric_dtype(df['r_squared'])

    # Check string columns
    assert pd.api.types.is_string_dtype(df['graph_id'])
    assert pd.api.types.is_string_dtype(df['class'])
    assert pd.api.types.is_string_dtype(df['status'])
