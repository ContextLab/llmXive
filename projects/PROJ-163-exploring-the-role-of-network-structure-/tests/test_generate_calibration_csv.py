"""
Tests for generate_calibration_csv.py (Task T017a).
"""
import os
import json
import csv
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import pytest

# We will mock the fetcher functions to avoid needing real API data
# and to ensure we test the CSV generation logic correctly.
from unittest.mock import patch, MagicMock

# Import the module under test
import generate_calibration_csv as gc_csv

@pytest.fixture
def mock_snapshots():
    """Create mock raw snapshots for testing."""
    return [
        {
            'device_id': 'ibm_test_device_1',
            'timestamp': '2024-05-20T12:00:00Z',
            'properties': {
                'qubits': [
                    {'name': 'T1', 'value': 100.0, 'unit': 'us'},
                    {'name': 'T2', 'value': 200.0, 'unit': 'us'},
                ],
                'gates': [
                    {'qubits': [0, 1], 'name': 'cx', 'value': 0.01},
                    {'qubits': [1, 2], 'name': 'cx', 'value': 0.02},
                ],
                'readout': [
                    {'name': 'readout_error', 'value': 0.05},
                ]
            }
        },
        {
            'device_id': 'ibm_test_device_2',
            'timestamp': '2024-05-20T13:00:00Z',
            'properties': {
                'qubits': [
                    {'name': 'T1', 'value': 150.0, 'unit': 'us'},
                    {'name': 'T2', 'value': 250.0, 'unit': 'us'},
                ],
                'gates': [
                    {'qubits': [0, 1], 'name': 'cx', 'value': 0.015},
                ],
                'readout': [
                    {'name': 'readout_error', 'value': 0.06},
                ]
            }
        }
    ]

@pytest.fixture
def temp_data_dir(mock_snapshots):
    """Create a temporary directory structure with mock raw data."""
    temp_dir = tempfile.mkdtemp()
    raw_dir = Path(temp_dir) / "data" / "raw"
    raw_dir.mkdir(parents=True)
    
    # Write mock snapshots
    for i, snapshot in enumerate(mock_snapshots):
        file_path = raw_dir / f"device_{i}.json"
        with open(file_path, 'w') as f:
            json.dump(snapshot, f)
    
    # Store original paths to restore later
    orig_raw = gc_csv.DATA_RAW_DIR
    orig_out_dir = gc_csv.DATA_PROCESSED_DIR
    orig_output = gc_csv.OUTPUT_FILE

    # Patch paths
    gc_csv.DATA_RAW_DIR = raw_dir
    gc_csv.DATA_PROCESSED_DIR = Path(temp_dir) / "data" / "processed"
    gc_csv.OUTPUT_FILE = gc_csv.DATA_PROCESSED_DIR / "performance_metrics.csv"

    yield temp_dir

    # Restore original paths
    gc_csv.DATA_RAW_DIR = orig_raw
    gc_csv.DATA_PROCESSED_DIR = orig_out_dir
    gc_csv.OUTPUT_FILE = orig_output
    shutil.rmtree(temp_dir)

@patch('generate_calibration_csv.extract_performance_metrics')
@patch('generate_calibration_csv.extract_chip_family')
def test_load_raw_snapshots(mock_chip_family, mock_perf_metrics, temp_data_dir, mock_snapshots):
    """Test that load_raw_snapshots correctly loads JSON files."""
    # Setup mocks
    mock_perf_metrics.return_value = {
        't1_mean': 125.0,
        't2_mean': 225.0,
        'cx_error_mean': 0.015,
        'readout_error_mean': 0.055
    }
    mock_chip_family.return_value = "Falcon"

    snapshots = gc_csv.load_raw_snapshots()
    assert len(snapshots) == 2
    assert snapshots[0]['device_id'] == 'ibm_test_device_1'
    assert snapshots[1]['device_id'] == 'ibm_test_device_2'

@patch('generate_calibration_csv.extract_performance_metrics')
@patch('generate_calibration_csv.extract_chip_family')
def test_extract_device_metrics(mock_chip_family, mock_perf_metrics):
    """Test extracting metrics from a single snapshot."""
    snapshot = {
        'device_id': 'ibm_test_device',
        'timestamp': '2024-05-20T12:00:00Z',
        'properties': {'dummy': 'data'}
    }
    
    mock_perf_metrics.return_value = {
        't1_mean': 100.0,
        't2_mean': 200.0,
        'cx_error_mean': 0.01,
        'readout_error_mean': 0.05
    }
    mock_chip_family.return_value = "Hummingbird"

    result = gc_csv.extract_device_metrics(snapshot)

    assert result is not None
    assert result['device_id'] == 'ibm_test_device'
    assert result['timestamp'] == '2024-05-20T12:00:00Z'
    assert result['t1_mean'] == 100.0
    assert result['t2_mean'] == 200.0
    assert result['cx_error_mean'] == 0.01
    assert result['readout_error_mean'] == 0.05
    assert result['chip_family'] == "Hummingbird"

@patch('generate_calibration_csv.extract_performance_metrics')
@patch('generate_calibration_csv.extract_chip_family')
def test_main_generates_csv(mock_chip_family, mock_perf_metrics, temp_data_dir, mock_snapshots):
    """Test that main() generates the CSV file with correct columns."""
    # Setup mocks
    mock_perf_metrics.return_value = {
        't1_mean': 125.0,
        't2_mean': 225.0,
        'cx_error_mean': 0.015,
        'readout_error_mean': 0.055
    }
    mock_chip_family.return_value = "Falcon"

    # Run main
    gc_csv.main()

    # Verify file exists
    assert gc_csv.OUTPUT_FILE.exists()

    # Verify content
    with open(gc_csv.OUTPUT_FILE, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 2
        
        # Check headers
        expected_headers = [
            'device_id', 'timestamp', 't1_mean', 't2_mean', 
            'cx_error_mean', 'readout_error_mean', 'chip_family'
        ]
        assert reader.fieldnames == expected_headers

        # Check data
        assert rows[0]['device_id'] == 'ibm_test_device_1'
        assert rows[0]['chip_family'] == 'Falcon'
        assert float(rows[0]['t1_mean']) == 125.0
        
        assert rows[1]['device_id'] == 'ibm_test_device_2'
        assert float(rows[1]['t2_mean']) == 225.0

@patch('generate_calibration_csv.extract_performance_metrics')
@patch('generate_calibration_csv.extract_chip_family')
def test_main_empty_directory(mock_chip_family, mock_perf_metrics, temp_data_dir):
    """Test behavior when no snapshots are found."""
    # Clear the temp raw directory
    raw_dir = gc_csv.DATA_RAW_DIR
    for f in raw_dir.glob("*"):
        f.unlink()

    # Setup mocks (should not be called if no data)
    mock_perf_metrics.return_value = {'t1_mean': 0}
    mock_chip_family.return_value = "Test"

    gc_csv.main()

    # Verify file exists (empty with headers)
    assert gc_csv.OUTPUT_FILE.exists()
    with open(gc_csv.OUTPUT_FILE, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert headers == [
            'device_id', 'timestamp', 't1_mean', 't2_mean', 
            'cx_error_mean', 'readout_error_mean', 'chip_family'
        ]
        # Check no data rows
        remaining = list(reader)
        assert len(remaining) == 0
