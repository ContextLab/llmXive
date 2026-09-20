"""
Unit tests for SC-001 failure measurement.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from sc001_failure_measure import measure_original_sc001_failure, write_metrics_report

class TestMeasureOriginalSC001Failure:
    """Tests for measure_original_sc001_failure function."""

    def test_returns_zero_rate(self):
        """Test that the function returns a rate of 0.0."""
        result = measure_original_sc001_failure()
        assert result["sc001_original_merge_rate"] == 0.0

    def test_returns_reason(self):
        """Test that the function returns the correct reason."""
        result = measure_original_sc001_failure()
        assert "reason" in result
        assert "ISRIC source unavailable" in result["reason"]
        assert "FR-002 excluded" in result["reason"]

    def test_returns_dict(self):
        """Test that the function returns a dictionary."""
        result = measure_original_sc001_failure()
        assert isinstance(result, dict)

class TestWriteMetricsReport:
    """Tests for write_metrics_report function."""

    @patch("sc001_failure_measure.Path.exists")
    @patch("sc001_failure_measure.Path.open")
    @patch("sc001_failure_measure.Path.mkdir")
    def test_creates_directory(self, mock_mkdir, mock_open, mock_exists):
        """Test that the function creates the output directory if it doesn't exist."""
        mock_exists.return_value = False
        mock_open.return_value.__enter__ = MagicMock()
        mock_open.return_value.__exit__ = MagicMock()
        
        config = {
            "paths": {
                "artifacts": "/tmp/test_artifacts"
            }
        }
        
        metrics = {"test_metric": 0.0}
        write_metrics_report(metrics, config)
        
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("sc001_failure_measure.Path.exists")
    @patch("sc001_failure_measure.Path.open")
    @patch("sc001_failure_measure.Path.mkdir")
    def test_writes_json(self, mock_mkdir, mock_open, mock_exists):
        """Test that the function writes valid JSON."""
        mock_exists.return_value = False
        mock_open.return_value.__enter__ = MagicMock()
        mock_open.return_value.__exit__ = MagicMock()
        
        config = {
            "paths": {
                "artifacts": "/tmp/test_artifacts"
            }
        }
        
        metrics = {"test_metric": 0.0}
        write_metrics_report(metrics, config)
        
        # Verify that open was called with 'w' mode
        call_args = mock_open.call_args
        assert call_args[0][1] == 'w'