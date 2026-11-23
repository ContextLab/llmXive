"""
Unit tests for code/analysis/kinetic_metrics.py

Tests the aggregation logic, outlier filtering, and CSV writing.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path if not already there
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.kinetic_metrics import (
    load_kinetic_results,
    load_outlier_flags,
    aggregate_metrics,
    write_metrics_csv,
    aggregate_metrics
)
from config import get_processed_data_path

# Fixtures
@pytest.fixture
def mock_kinetic_results():
    """Sample kinetic results data."""
    return [
        {"run_id": "run_001", "solvent": "cyclohexane", "lifetime_ns": 10.5, "fit_error": 0.01},
        {"run_id": "run_002", "solvent": "cyclohexane", "lifetime_ns": 10.8, "fit_error": 0.02},
        {"run_id": "run_003", "solvent": "cyclohexane", "lifetime_ns": 10.6, "fit_error": 0.01},
        {"run_id": "run_004", "solvent": "ethanol", "lifetime_ns": 5.2, "fit_error": 0.03},
        {"run_id": "run_005", "solvent": "ethanol", "lifetime_ns": 5.4, "fit_error": 0.02},
        {"run_id": "run_006", "solvent": "acetonitrile", "lifetime_ns": 2.1, "fit_error": 0.05},
        # Outlier to be tested
        {"run_id": "run_007", "solvent": "ethanol", "lifetime_ns": 15.0, "fit_error": 0.9},
    ]

@pytest.fixture
def mock_outlier_flags():
    """Sample outlier flags."""
    return {
        "run_007": True
    }

@pytest.fixture
def temp_processed_dir():
    """Create a temporary directory for processed files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir)
        # Patch the config to use this temp dir
        with patch('analysis.kinetic_metrics.get_processed_data_path', return_value=processed_dir):
            with patch('config.get_processed_data_path', return_value=processed_dir):
                yield processed_dir

def test_aggregate_metrics_basic(mock_kinetic_results):
    """Test basic aggregation without outliers."""
    outlier_flags = {}
    result = aggregate_metrics(mock_kinetic_results, outlier_flags)

    assert len(result) == 3  # 3 solvents

    # Check cyclohexane stats (mean of 10.5, 10.8, 10.6)
    cyclohexane = next(r for r in result if r['solvent'] == 'cyclohexane')
    assert np.isclose(cyclohexane['mean_lifetime_ns'], 10.6333, atol=0.01)
    assert cyclohexane['n_replicates'] == 3
    assert cyclohexane['std_lifetime_ns'] > 0

    # Check ethanol stats (mean of 5.2, 5.4)
    ethanol = next(r for r in result if r['solvent'] == 'ethanol')
    assert np.isclose(ethanol['mean_lifetime_ns'], 5.3, atol=0.01)
    assert ethanol['n_replicates'] == 2

def test_aggregate_metrics_with_outliers(mock_kinetic_results, mock_outlier_flags):
    """Test that outliers are filtered out."""
    result = aggregate_metrics(mock_kinetic_results, mock_outlier_flags)

    assert len(result) == 3

    # Ethanol should now have n=2 (run_007 filtered out)
    ethanol = next(r for r in result if r['solvent'] == 'ethanol')
    assert ethanol['n_replicates'] == 2
    assert np.isclose(ethanol['mean_lifetime_ns'], 5.3, atol=0.01)

    # Verify the outlier value (15.0) is NOT in the stats
    # If it were included, mean would be (5.2+5.4+15.0)/3 = 8.53
    assert ethanol['max_lifetime_ns'] < 6.0

def test_aggregate_metrics_single_replicate(mock_kinetic_results):
    """Test handling of single replicate (CI should be point estimate)."""
    # Filter to just one acetonitrile run
    single_run = [r for r in mock_kinetic_results if r['solvent'] == 'acetonitrile']
    result = aggregate_metrics(single_run, {})

    assert len(result) == 1
    acn = result[0]
    assert acn['n_replicates'] == 1
    # For n=1, CI lower and upper should equal the mean
    assert acn['ci_95_lower_ns'] == acn['mean_lifetime_ns']
    assert acn['ci_95_upper_ns'] == acn['mean_lifetime_ns']

def test_write_metrics_csv(temp_processed_dir, mock_kinetic_results):
    """Test writing the CSV file."""
    result = aggregate_metrics(mock_kinetic_results, {})
    output_path = write_metrics_csv(result)

    assert output_path.exists()
    assert output_path.name == "kinetic_metrics.csv"

    # Verify content
    df = result  # We already have the list, but let's check the file
    import pandas as pd
    df_file = pd.read_csv(output_path)

    assert len(df_file) == 3
    assert 'solvent' in df_file.columns
    assert 'mean_lifetime_ns' in df_file.columns
    assert 'ci_95_lower_ns' in df_file.columns
    assert 'ci_95_upper_ns' in df_file.columns

def test_load_kinetic_results_missing_file(temp_processed_dir):
    """Test error handling when results file is missing."""
    with pytest.raises(FileNotFoundError):
        load_kinetic_results()

def test_load_outlier_flags_missing_file(temp_processed_dir):
    """Test that missing outlier flags returns empty dict."""
    flags = load_outlier_flags()
    assert flags == {}
