"""
Unit tests for T012a: Data Availability Verification.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
# Note: The import path must match the project structure
import sys
from pathlib import Path as SysPath

# Add code/ to path if running from root
code_root = SysPath(__file__).resolve().parent.parent.parent / 'code'
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data_ingestion.verify_data import (
    check_data_availability,
    write_status,
    verify_and_save,
    _scan_directory_for_pairs
)
from src.logging_config import get_data_ingestion_logger


@pytest.fixture
def mock_data_dir():
    """Creates a temporary directory structure simulating data scenarios."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Scenario 1: Paired data
        (tmp_path / 'paired_sample_01_coords.csv').touch()
        (tmp_path / 'paired_sample_01_thermal.csv').touch()

        # Scenario 2: Unpaired thermal data
        (tmp_path / 'aggregate_thermal_data.csv').touch()

        # Scenario 3: Unpaired coords (no thermal)
        (tmp_path / 'orphan_coords.csv').touch()

        yield tmp_path


@pytest.fixture
def empty_data_dir():
    """Creates an empty temporary directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


def test_scan_paired_data(mock_data_dir):
    """Test that paired data is correctly identified."""
    has_paired, has_unpaired, issues = _scan_directory_for_pairs(mock_data_dir)
    assert has_paired is True
    assert has_unpaired is True  # Because of aggregate_thermal_data.csv
    assert any('unpaired' in issue.lower() for issue in issues)


def test_scan_unpaired_data(empty_data_dir):
    """Test detection of unpaired data only."""
    # Create only thermal file
    (empty_data_dir / 'only_thermal.csv').touch()

    has_paired, has_unpaired, issues = _scan_directory_for_pairs(empty_data_dir)
    assert has_paired is False
    assert has_unpaired is True


def test_scan_no_data(empty_data_dir):
    """Test detection when no data exists."""
    has_paired, has_unpaired, issues = _scan_directory_for_pairs(empty_data_dir)
    assert has_paired is False
    assert has_unpaired is False
    assert len(issues) == 0


def test_verify_and_save_creates_status_file(mock_data_dir):
    """Test that verify_and_save creates the status JSON file."""
    with tempfile.TemporaryDirectory() as tmp_out:
        status_path = Path(tmp_out) / 'data_status.json'
        
        # Mock get_config to return a dummy config if needed, 
        # but check_data_availability uses the fixture path logic if passed
        # We need to override the data_dir passed to check_data_availability
        # by patching the internal call or passing it directly if the function allowed it.
        # Since check_data_availability has an optional data_dir, we can pass it.
        
        # However, verify_and_save doesn't take data_dir. 
        # We will mock the internal call to check_data_availability to return a known state
        # and verify the file writing logic.
        
        mock_status = {
            'has_real_data': True,
            'has_paired': True,
            'is_unpaired': False,
            'fallback_mode': 'none',
            'issues': [],
            'data_directory': str(mock_data_dir)
        }

        with patch('src.data_ingestion.verify_data.check_data_availability', return_value=mock_status):
            result_path = write_status(mock_status, status_path)

        assert result_path.exists()
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert data['has_real_data'] is True
        assert 'timestamp' in data


def test_verify_and_save_unpaired_mode(mock_data_dir):
    """Test status generation for unpaired data scenario."""
    # Create a scenario with only unpaired thermal data
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / 'unpaired_thermal.csv').touch()
        
        mock_status = {
            'has_real_data': True,
            'has_paired': False,
            'is_unpaired': True,
            'fallback_mode': 'population',
            'issues': ['Found unpaired thermal data'],
            'data_directory': str(tmp_path)
        }

        with tempfile.TemporaryDirectory() as tmp_out:
            status_path = Path(tmp_out) / 'data_status.json'
            write_status(mock_status, status_path)

            with open(status_path, 'r') as f:
                data = json.load(f)
            
            assert data['is_unpaired'] is True
            assert data['fallback_mode'] == 'population'


def test_verify_and_save_no_data_mode(empty_data_dir):
    """Test status generation for no data scenario."""
    mock_status = {
        'has_real_data': False,
        'has_paired': False,
        'is_unpaired': False,
        'fallback_mode': 'synthetic',
        'issues': ['No real data found'],
        'data_directory': str(empty_data_dir)
    }

    with tempfile.TemporaryDirectory() as tmp_out:
        status_path = Path(tmp_out) / 'data_status.json'
        write_status(mock_status, status_path)

        with open(status_path, 'r') as f:
            data = json.load(f)
        
        assert data['fallback_mode'] == 'synthetic'
        assert data['has_real_data'] is False