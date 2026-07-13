"""
Unit tests for preprocessing module.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import json

from collect.preprocess import (
    parse_timestamp,
    compute_resolution_time,
    is_valid_issue,
    preprocess_issues
)

class TestParseTimestamp:
    def test_iso_format_with_z(self):
        ts = parse_timestamp("2023-01-01T12:00:00Z")
        assert ts is not None
        assert ts.year == 2023
        assert ts.month == 1
        assert ts.day == 1
    
    def test_iso_format_with_offset(self):
        ts = parse_timestamp("2023-01-01T12:00:00+00:00")
        assert ts is not None
        assert ts.year == 2023
    
    def test_none_value(self):
        assert parse_timestamp(None) is None
    
    def test_nan_value(self):
        assert parse_timestamp(pd.NA) is None
        assert parse_timestamp(np.nan) is None
    
    def test_invalid_format(self):
        assert parse_timestamp("not a date") is None

class TestComputeResolutionTime:
    def test_valid_resolution(self):
        created = "2023-01-01T00:00:00Z"
        closed = "2023-01-01T05:00:00Z"
        hours = compute_resolution_time(created, closed)
        assert hours == 5.0
    
    def test_missing_created(self):
        created = None
        closed = "2023-01-01T05:00:00Z"
        hours = compute_resolution_time(created, closed)
        assert hours is None
    
    def test_missing_closed(self):
        created = "2023-01-01T00:00:00Z"
        closed = None
        hours = compute_resolution_time(created, closed)
        assert hours is None
    
    def test_negative_resolution(self):
        created = "2023-01-02T00:00:00Z"
        closed = "2023-01-01T00:00:00Z"
        hours = compute_resolution_time(created, closed)
        assert hours == -24.0  # Negative but computed

class TestIsValidIssue:
    def test_valid_issue(self):
        row = {
            'id': 123,
            'created_at': '2023-01-01T00:00:00Z',
            'closed_at': '2023-01-01T05:00:00Z',
            'repository_name': 'test/repo'
        }
        is_valid, reason = is_valid_issue(row)
        assert is_valid is True
        assert reason is None
    
    def test_missing_created_at(self):
        row = {
            'id': 123,
            'created_at': None,
            'closed_at': '2023-01-01T05:00:00Z',
            'repository_name': 'test/repo'
        }
        is_valid, reason = is_valid_issue(row)
        assert is_valid is False
        assert reason == "missing_created_at"
    
    def test_missing_closed_at(self):
        row = {
            'id': 123,
            'created_at': '2023-01-01T00:00:00Z',
            'closed_at': None,
            'repository_name': 'test/repo'
        }
        is_valid, reason = is_valid_issue(row)
        assert is_valid is False
        assert reason == "missing_closed_at"
    
    def test_negative_resolution_time(self):
        row = {
            'id': 123,
            'created_at': '2023-01-02T00:00:00Z',
            'closed_at': '2023-01-01T00:00:00Z',
            'repository_name': 'test/repo'
        }
        is_valid, reason = is_valid_issue(row)
        assert is_valid is False
        assert reason == "negative_resolution_time"
    
    def test_exceeds_one_year(self):
        row = {
            'id': 123,
            'created_at': '2020-01-01T00:00:00Z',
            'closed_at': '2023-01-01T00:00:00Z',
            'repository_name': 'test/repo'
        }
        is_valid, reason = is_valid_issue(row)
        assert is_valid is False
        assert reason == "exceeds_one_year"

class TestPreprocessIssues:
    def test_preprocess_with_valid_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_path = tmpdir / "input.csv"
            output_path = tmpdir / "output.csv"
            log_path = tmpdir / "logs" / "preprocessing.log"
            
            # Create test data
            data = {
                'id': [1, 2, 3, 4],
                'created_at': [
                    '2023-01-01T00:00:00Z',
                    '2023-01-01T00:00:00Z',
                    None,
                    '2023-01-03T00:00:00Z'
                ],
                'closed_at': [
                    '2023-01-01T05:00:00Z',
                    None,
                    '2023-01-01T05:00:00Z',
                    '2023-01-02T00:00:00Z'
                ],
                'repository_name': ['r1', 'r2', 'r3', 'r4']
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            # Run preprocessing
            stats = preprocess_issues(input_path, output_path, log_path)
            
            # Verify results
            assert stats['total_input_rows'] == 4
            assert stats['valid_rows'] == 2  # Only rows 1 and 4 are valid
            assert stats['excluded_rows'] == 2
            assert stats['completeness_rate'] == 0.5
            
            # Verify output file
            assert output_path.exists()
            output_df = pd.read_csv(output_path)
            assert len(output_df) == 2
            assert 'resolution_time_hours' in output_df.columns
            
            # Verify resolution times
            assert output_df.iloc[0]['resolution_time_hours'] == 5.0
            assert output_df.iloc[1]['resolution_time_hours'] == 24.0
            
            # Verify log file
            assert log_path.exists()
            with open(log_path, 'r') as f:
                lines = f.readlines()
            assert len(lines) == 2  # Two exclusions logged

    def test_preprocess_empty_result(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_path = tmpdir / "input.csv"
            output_path = tmpdir / "output.csv"
            log_path = tmpdir / "logs" / "preprocessing.log"
            
            # Create data with all invalid rows
            data = {
                'id': [1, 2],
                'created_at': [None, None],
                'closed_at': ['2023-01-01T05:00:00Z', '2023-01-01T05:00:00Z'],
                'repository_name': ['r1', 'r2']
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            # Run preprocessing
            stats = preprocess_issues(input_path, output_path, log_path)
            
            assert stats['valid_rows'] == 0
            assert stats['excluded_rows'] == 2
            assert output_path.exists()