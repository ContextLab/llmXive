import pytest
import csv
from pathlib import Path
import sys
import os

# Add code to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.metrics_writer import write_metrics_csv, load_metrics_csv, METRICS_COLUMNS

class TestMetricsSchema:
    """
    Unit tests for T028: metrics.csv schema and writer.
    """

    @pytest.fixture
    def temp_csv_path(self, tmp_path):
        """Create a temporary CSV path for testing."""
        return tmp_path / "test_metrics.csv"

    def test_schema_columns_defined(self):
        """Verify that the schema columns match the specification."""
        expected = [
            'trajectory_id',
            'model',
            'mae_position',
            'mae_rotation',
            'convergence',
            'sfm_failure_reason'
        ]
        assert METRICS_COLUMNS == expected, "Schema columns do not match specification."

    def test_write_csv_creates_file(self, temp_csv_path):
        """Test that writing a row creates the file with headers."""
        rows = [{
            'trajectory_id': 't1',
            'model': 'M1',
            'mae_position': 1.0,
            'mae_rotation': 0.5,
            'convergence': True,
            'sfm_failure_reason': ''
        }]
        write_metrics_csv(rows, temp_csv_path, overwrite=True)
        assert temp_csv_path.exists(), "CSV file was not created."

    def test_write_csv_headers(self, temp_csv_path):
        """Test that the CSV file has the correct header row."""
        rows = [{
            'trajectory_id': 't1',
            'model': 'M1',
            'mae_position': 1.0,
            'mae_rotation': 0.5,
            'convergence': True,
            'sfm_failure_reason': ''
        }]
        write_metrics_csv(rows, temp_csv_path, overwrite=True)
        
        with open(temp_csv_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == METRICS_COLUMNS, f"Header mismatch: {header} vs {METRICS_COLUMNS}"

    def test_null_handling_position(self, temp_csv_path):
        """Test that None values for mae_position are handled correctly (empty string in CSV)."""
        rows = [{
            'trajectory_id': 't1',
            'model': 'M1',
            'mae_position': None,
            'mae_rotation': 0.5,
            'convergence': False,
            'sfm_failure_reason': 'test_error'
        }]
        write_metrics_csv(rows, temp_csv_path, overwrite=True)
        
        loaded = load_metrics_csv(temp_csv_path)
        assert len(loaded) == 1
        assert loaded[0]['mae_position'] is None, "None value not preserved on load."

    def test_null_handling_rotation(self, temp_csv_path):
        """Test that None values for mae_rotation are handled correctly."""
        rows = [{
            'trajectory_id': 't1',
            'model': 'M1',
            'mae_position': 1.0,
            'mae_rotation': None,
            'convergence': False,
            'sfm_failure_reason': 'test_error'
        }]
        write_metrics_csv(rows, temp_csv_path, overwrite=True)
        
        loaded = load_metrics_csv(temp_csv_path)
        assert loaded[0]['mae_rotation'] is None, "None value for rotation not preserved."

    def test_convergence_boolean(self, temp_csv_path):
        """Test that boolean convergence is written and read correctly."""
        rows = [{
            'trajectory_id': 't1',
            'model': 'M1',
            'mae_position': 1.0,
            'mae_rotation': 0.5,
            'convergence': True,
            'sfm_failure_reason': ''
        }, {
            'trajectory_id': 't2',
            'model': 'M1',
            'mae_position': 2.0,
            'mae_rotation': 0.8,
            'convergence': False,
            'sfm_failure_reason': ''
        }]
        write_metrics_csv(rows, temp_csv_path, overwrite=True)
        
        loaded = load_metrics_csv(temp_csv_path)
        assert loaded[0]['convergence'] is True
        assert loaded[1]['convergence'] is False

    def test_sfm_failure_reason_empty_on_success(self, temp_csv_path):
        """Test that sfm_failure_reason is empty string when convergence is True."""
        rows = [{
            'trajectory_id': 't1',
            'model': 'M1',
            'mae_position': 1.0,
            'mae_rotation': 0.5,
            'convergence': True,
            'sfm_failure_reason': ''
        }]
        write_metrics_csv(rows, temp_csv_path, overwrite=True)
        
        loaded = load_metrics_csv(temp_csv_path)
        assert loaded[0]['sfm_failure_reason'] == ''

    def test_sfm_failure_reason_populated_on_failure(self, temp_csv_path):
        """Test that sfm_failure_reason captures the error string."""
        rows = [{
            'trajectory_id': 't1',
            'model': 'M1',
            'mae_position': None,
            'mae_rotation': None,
            'convergence': False,
            'sfm_failure_reason': 'insufficient_features'
        }]
        write_metrics_csv(rows, temp_csv_path, overwrite=True)
        
        loaded = load_metrics_csv(temp_csv_path)
        assert loaded[0]['sfm_failure_reason'] == 'insufficient_features'

    def test_append_mode(self, temp_csv_path):
        """Test that appending rows works correctly."""
        rows1 = [{
            'trajectory_id': 't1',
            'model': 'M1',
            'mae_position': 1.0,
            'mae_rotation': 0.5,
            'convergence': True,
            'sfm_failure_reason': ''
        }]
        write_metrics_csv(rows1, temp_csv_path, overwrite=True)
        
        rows2 = [{
            'trajectory_id': 't2',
            'model': 'M1',
            'mae_position': 2.0,
            'mae_rotation': 0.8,
            'convergence': True,
            'sfm_failure_reason': ''
        }]
        write_metrics_csv(rows2, temp_csv_path, overwrite=False)
        
        loaded = load_metrics_csv(temp_csv_path)
        assert len(loaded) == 2
        assert loaded[0]['trajectory_id'] == 't1'
        assert loaded[1]['trajectory_id'] == 't2'
