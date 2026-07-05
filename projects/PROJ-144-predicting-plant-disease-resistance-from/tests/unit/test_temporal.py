"""
Unit tests for temporal validation module.
Tests validate_temporal_consistency from code/data/validate_temporal.py
"""
import os
import tempfile
import json
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
sys_path = str(Path(__file__).parent.parent.parent)
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

from code.data.validate_temporal import validate_temporal_consistency, _process_file, _parse_time
from code.utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR


class TestTemporalValidation:
    """Tests for temporal validation functionality."""

    def test_parse_time_numeric(self):
        """Test parsing numeric timestamps."""
        assert _parse_time(123456) == 123456.0
        assert _parse_time(123.456) == 123.456
        assert _parse_time(0) == 0.0

    def test_parse_time_string_numeric(self):
        """Test parsing string numeric values."""
        assert _parse_time("123456") == 123456.0
        assert _parse_time("123.456") == 123.456

    def test_parse_time_date_string(self):
        """Test parsing date strings."""
        # Test various formats
        assert _parse_time("2023-01-15") is not None
        assert _parse_time("2023/01/15") is not None
        assert _parse_time("15-01-2023") is not None

    def test_parse_time_invalid(self):
        """Test parsing invalid values."""
        assert _parse_time(None) is None
        assert _parse_time("") is None
        assert _parse_time("invalid") is None
        assert _parse_time(float('nan')) is None

    def test_process_file_valid(self):
        """Test processing a file with valid temporal data."""
        df = pd.DataFrame({
            "sample_time": [100, 200, 300],
            "challenge_time": [150, 250, 350],
            "other_col": ["a", "b", "c"]
        })
        
        result = _process_file(df, "test.csv")
        
        assert result["valid"] is True
        assert result["violation_count"] == 0
        assert result["valid_rows"] == 3
        assert result["total_rows"] == 3

    def test_process_file_violations(self):
        """Test processing a file with temporal violations."""
        df = pd.DataFrame({
            "sample_time": [100, 200, 300],  # 300 >= 250 is a violation
            "challenge_time": [150, 250, 250],
            "other_col": ["a", "b", "c"]
        })
        
        result = _process_file(df, "test.csv")
        
        assert result["valid"] is False
        assert result["violation_count"] == 1
        assert result["valid_rows"] == 3

    def test_process_file_missing_columns(self):
        """Test processing a file missing time columns."""
        df = pd.DataFrame({
            "other_col": ["a", "b", "c"],
            "another_col": [1, 2, 3]
        })
        
        result = _process_file(df, "test.csv")
        
        assert result["sample_time_col"] is None
        assert result["challenge_time_col"] is None

    def test_process_file_nan_values(self):
        """Test processing a file with NaN time values."""
        df = pd.DataFrame({
            "sample_time": [100, None, 300],
            "challenge_time": [150, 250, None],
            "other_col": ["a", "b", "c"]
        })
        
        result = _process_file(df, "test.csv")
        
        # Only 1 row should be valid (index 0)
        assert result["valid_rows"] == 1
        assert result["total_rows"] == 3

    def test_validate_temporal_with_placeholder(self, monkeypatch, tmp_path):
        """Test validation with placeholder file."""
        # Create a temporary directory structure
        raw_dir = tmp_path / "raw"
        processed_dir = tmp_path / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        
        # Create a valid placeholder file
        placeholder = raw_dir / "placeholder_phenotypes.csv"
        df_valid = pd.DataFrame({
            "sample_time": [100, 200, 300],
            "challenge_time": [150, 250, 350],
            "sample_id": ["s1", "s2", "s3"]
        })
        df_valid.to_csv(placeholder, index=False)
        
        # Monkeypatch constants
        monkeypatch.setattr("code.data.validate_temporal.DATA_RAW_DIR", str(raw_dir))
        monkeypatch.setattr("code.data.validate_temporal.DATA_PROCESSED_DIR", str(processed_dir))
        
        # Run validation
        result = validate_temporal_consistency()
        
        assert result is True
        
        # Check report was written
        report_path = processed_dir / "temporal_validation_report.json"
        assert report_path.exists()
        
        with open(report_path) as f:
            report = json.load(f)
        
        assert report["success"] is True
        assert report["summary"]["violation_count"] == 0

    def test_validate_temporal_with_violations(self, monkeypatch, tmp_path):
        """Test validation detecting violations."""
        # Create a temporary directory structure
        raw_dir = tmp_path / "raw"
        processed_dir = tmp_path / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        
        # Create a placeholder file with violations
        placeholder = raw_dir / "placeholder_phenotypes.csv"
        df_invalid = pd.DataFrame({
            "sample_time": [100, 300, 400],  # 300 >= 250, 400 >= 350
            "challenge_time": [150, 250, 350],
            "sample_id": ["s1", "s2", "s3"]
        })
        df_invalid.to_csv(placeholder, index=False)
        
        # Monkeypatch constants
        monkeypatch.setattr("code.data.validate_temporal.DATA_RAW_DIR", str(raw_dir))
        monkeypatch.setattr("code.data.validate_temporal.DATA_PROCESSED_DIR", str(processed_dir))
        
        # Run validation
        result = validate_temporal_consistency()
        
        assert result is False
        
        # Check report was written
        report_path = processed_dir / "temporal_validation_report.json"
        assert report_path.exists()
        
        with open(report_path) as f:
            report = json.load(f)
        
        assert report["success"] is False
        assert report["summary"]["violation_count"] == 2

    def test_validate_temporal_no_files(self, monkeypatch, tmp_path):
        """Test validation when no files exist."""
        # Create empty directories
        raw_dir = tmp_path / "raw"
        processed_dir = tmp_path / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        
        # Monkeypatch constants
        monkeypatch.setattr("code.data.validate_temporal.DATA_RAW_DIR", str(raw_dir))
        monkeypatch.setattr("code.data.validate_temporal.DATA_PROCESSED_DIR", str(processed_dir))
        
        # Run validation
        result = validate_temporal_consistency()
        
        assert result is False
        
        # Check report was written with error
        report_path = processed_dir / "temporal_validation_report.json"
        assert report_path.exists()
        
        with open(report_path) as f:
            report = json.load(f)
        
        assert report["success"] is False
        assert report["summary"]["total_files"] == 0

    def test_validate_temporal_date_formats(self, monkeypatch, tmp_path):
        """Test validation with various date formats."""
        # Create a temporary directory structure
        raw_dir = tmp_path / "raw"
        processed_dir = tmp_path / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        
        # Create a file with date strings
        placeholder = raw_dir / "placeholder_phenotypes.csv"
        df_dates = pd.DataFrame({
            "sample_time": ["2023-01-01", "2023-02-01", "2023-03-01"],
            "challenge_time": ["2023-01-15", "2023-02-15", "2023-03-15"],
            "sample_id": ["s1", "s2", "s3"]
        })
        df_dates.to_csv(placeholder, index=False)
        
        # Monkeypatch constants
        monkeypatch.setattr("code.data.validate_temporal.DATA_RAW_DIR", str(raw_dir))
        monkeypatch.setattr("code.data.validate_temporal.DATA_PROCESSED_DIR", str(processed_dir))
        
        # Run validation
        result = validate_temporal_consistency()
        
        assert result is True

    def test_validate_temporal_alternative_column_names(self, monkeypatch, tmp_path):
        """Test validation with alternative column names."""
        # Create a temporary directory structure
        raw_dir = tmp_path / "raw"
        processed_dir = tmp_path / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        
        # Create a file with alternative column names
        placeholder = raw_dir / "placeholder_phenotypes.csv"
        df_alt = pd.DataFrame({
            "time_sample": [100, 200, 300],
            "time_challenge": [150, 250, 350],
            "sample_id": ["s1", "s2", "s3"]
        })
        df_alt.to_csv(placeholder, index=False)
        
        # Monkeypatch constants
        monkeypatch.setattr("code.data.validate_temporal.DATA_RAW_DIR", str(raw_dir))
        monkeypatch.setattr("code.data.validate_temporal.DATA_PROCESSED_DIR", str(processed_dir))
        
        # Run validation
        result = validate_temporal_consistency()
        
        assert result is True
