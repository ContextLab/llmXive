"""
Unit tests for the results_writer module.
"""
import pytest
import csv
import os
import tempfile
from pathlib import Path

from src.results_writer import write_dipole_timeseries

def test_write_empty_rows():
    """Test that an empty list creates a CSV with headers only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.csv"
        result = write_dipole_timeseries([], output_path)
        
        assert os.path.exists(result)
        with open(result, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0
            assert reader.fieldnames == ["interval_start", "dipole_amp", "dipole_phase", "quad_amp", "partial_interval"]

def test_write_single_row():
    """Test writing a single row with correct data types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.csv"
        rows = [
            {
                "interval_start": "2020-01-01T00:00:00Z",
                "dipole_amp": 0.5,
                "dipole_phase": 1.57,
                "quad_amp": 0.1,
                "partial_interval": True
            }
        ]
        result = write_dipole_timeseries(rows, output_path)
        
        assert os.path.exists(result)
        with open(result, "r") as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
            assert len(csv_rows) == 1
            row = csv_rows[0]
            assert row["interval_start"] == "2020-01-01T00:00:00Z"
            assert row["dipole_amp"] == "0.5"
            assert row["partial_interval"] == "1"  # Boolean converted to 1

def test_write_multiple_rows():
    """Test writing multiple rows."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.csv"
        rows = [
            {
                "interval_start": "2020-01-01T00:00:00Z",
                "dipole_amp": 0.5,
                "dipole_phase": 1.57,
                "quad_amp": 0.1,
                "partial_interval": False
            },
            {
                "interval_start": "2020-01-28T00:00:00Z",
                "dipole_amp": 0.6,
                "dipole_phase": 1.60,
                "quad_amp": 0.12,
                "partial_interval": True
            }
        ]
        result = write_dipole_timeseries(rows, output_path)
        
        assert os.path.exists(result)
        with open(result, "r") as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
            assert len(csv_rows) == 2
            assert csv_rows[1]["partial_interval"] == "1"

def test_missing_keys_default():
    """Test that missing keys get default values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.csv"
        # Row missing 'quad_amp' and 'partial_interval'
        rows = [
            {
                "interval_start": "2020-01-01T00:00:00Z",
                "dipole_amp": 0.5,
                "dipole_phase": 1.57
            }
        ]
        result = write_dipole_timeseries(rows, output_path)
        
        assert os.path.exists(result)
        with open(result, "r") as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
            assert len(csv_rows) == 1
            row = csv_rows[0]
            assert row["quad_amp"] == "0.0"
            assert row["partial_interval"] == "0"  # Default for missing boolean
