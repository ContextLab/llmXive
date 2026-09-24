"""
Unit tests for runtime enforcement and gate logic in main.py.
"""

import os
import sys
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from main import (
    check_runtime_gate,
    write_runtime_report,
    check_matching_gate,
    check_sensitivity_gate,
    check_pii_gate,
    MAX_RUNTIME_SECONDS
)
from utils.config import RUNTIME_REPORT_PATH


class TestRuntimeGate:
    """Tests for runtime enforcement logic."""

    def test_check_runtime_gate_within_limit(self):
        """Test that gate passes when runtime is within limit."""
        # Mock start time to be 1 hour ago (3600 seconds)
        start_time = time.time() - 3600
        
        with patch('main.PIPELINE_START_TIME', start_time):
            result = check_runtime_gate()
            assert result is True

    def test_check_runtime_gate_exceeds_limit(self):
        """Test that gate fails when runtime exceeds limit."""
        # Mock start time to be 7 hours ago (25200 seconds)
        start_time = time.time() - 25200
        
        with patch('main.PIPELINE_START_TIME', start_time):
            result = check_runtime_gate()
            assert result is False

    def test_check_runtime_gate_no_start_time(self):
        """Test that gate fails if start time is not set."""
        with patch('main.PIPELINE_START_TIME', None):
            result = check_runtime_gate()
            assert result is False

    def test_write_runtime_report_creates_file(self):
        """Test that write_runtime_report creates the JSON file."""
        elapsed = 1000.5
        
        # Ensure directory exists
        report_path = Path(RUNTIME_REPORT_PATH)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        write_runtime_report(elapsed)
        
        assert report_path.exists()
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        assert data['elapsed_seconds'] == elapsed
        assert data['max_allowed_seconds'] == MAX_RUNTIME_SECONDS
        assert data['status'] == 'passed'

    def test_write_runtime_report_status_failed(self):
        """Test that status is 'failed' when limit exceeded."""
        elapsed = MAX_RUNTIME_SECONDS + 100
        
        report_path = Path(RUNTIME_REPORT_PATH)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        write_runtime_report(elapsed)
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        assert data['status'] == 'failed'

class TestOtherGates:
    """Tests for other gate functions."""

    def test_check_matching_gate_no_report(self):
        """Test matching gate passes if no failure report exists."""
        # Mock non-existent report
        with patch('main.Path.exists', return_value=False):
            result = check_matching_gate()
            assert result is True

    def test_check_matching_gate_failed_report(self):
        """Test matching gate fails if failure report indicates failure."""
        mock_report = {'status': 'failed'}
        
        with patch('main.Path.exists', return_value=True):
            with patch('builtins.open', MagicMock(return_value=MagicMock(read=MagicMock(return_value=json.dumps(mock_report))))):
                result = check_matching_gate()
                assert result is False

    def test_check_sensitivity_gate_missing_file(self):
        """Test sensitivity gate fails if summary file is missing."""
        with patch('main.Path.exists', return_value=False):
            result = check_sensitivity_gate()
            assert result is False

    def test_check_sensitivity_gate_inconsistent(self):
        """Test sensitivity gate fails if consistency is False."""
        mock_summary = {'consistent': False}
        
        with patch('main.Path.exists', return_value=True):
            with patch('builtins.open', MagicMock(return_value=MagicMock(read=MagicMock(return_value=json.dumps(mock_summary))))):
                result = check_sensitivity_gate()
                assert result is False

    def test_check_sensitivity_gate_consistent(self):
        """Test sensitivity gate passes if consistent is True."""
        mock_summary = {'consistent': True}
        
        with patch('main.Path.exists', return_value=True):
            with patch('builtins.open', MagicMock(return_value=MagicMock(read=MagicMock(return_value=json.dumps(mock_summary))))):
                result = check_sensitivity_gate()
                assert result is True

    def test_check_pii_gate_no_report(self):
        """Test PII gate passes if no report exists."""
        with patch('main.Path.exists', return_value=False):
            result = check_pii_gate()
            assert result is True

    def test_check_pii_gate_pii_found(self):
        """Test PII gate fails if PII was found."""
        mock_report = {'pii_found': True}
        
        with patch('main.Path.exists', return_value=True):
            with patch('builtins.open', MagicMock(return_value=MagicMock(read=MagicMock(return_value=json.dumps(mock_report))))):
                result = check_pii_gate()
                assert result is False

    def test_check_pii_gate_no_pii(self):
        """Test PII gate passes if no PII was found."""
        mock_report = {'pii_found': False}
        
        with patch('main.Path.exists', return_value=True):
            with patch('builtins.open', MagicMock(return_value=MagicMock(read=MagicMock(return_value=json.dumps(mock_report))))):
                result = check_pii_gate()
                assert result is True
