"""
Unit tests for session_validation_metrics module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to mock the load_validation_state function since it depends on file system state
# which might not be populated in a unit test environment.
from session_validation_metrics import calculate_pass_rate, write_metrics, main


class TestCalculatePassRate:
    def test_calculate_pass_rate_100_percent(self):
        assert calculate_pass_rate(50, 50) == 100.0

    def test_calculate_pass_rate_50_percent(self):
        assert calculate_pass_rate(25, 50) == 50.0

    def test_calculate_pass_rate_zero_total(self):
        assert calculate_pass_rate(0, 0) == 0.0

    def test_calculate_pass_rate_zero_valid(self):
        assert calculate_pass_rate(0, 50) == 0.0


class TestWriteMetrics:
    def test_write_metrics_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metrics.json"
            metrics = {"test": 123}
            
            write_metrics(metrics, output_path)
            
            assert output_path.exists()
            with open(output_path) as f:
                data = json.load(f)
            assert data == metrics

    def test_write_metrics_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "metrics.json"
            metrics = {"test": 123}
            
            write_metrics(metrics, output_path)
            
            assert output_path.exists()
            assert output_path.parent.exists()


class TestMain:
    @patch('session_validation_metrics.load_validation_state')
    def test_main_success(self, mock_load_state):
        mock_load_state.return_value = {
            'total_subjects': 50,
            'valid_subjects': 48,
            'excluded_subjects': ['sub-01', 'sub-02']
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the output path to be in temp dir to avoid cluttering data/
            with patch('session_validation_metrics.Path') as mock_path:
                mock_path.return_value = Path(tmpdir) / "session_validation_metrics.json"
                
                result = main()
                
                assert result == 0
                assert mock_path.return_value.exists()
                
                with open(mock_path.return_value) as f:
                    data = json.load(f)
                
                assert data['total_subjects'] == 50
                assert data['valid_subjects'] == 48
                assert abs(data['pass_rate_percentage'] - 96.0) < 0.01

    @patch('session_validation_metrics.load_validation_state')
    def test_main_no_state(self, mock_load_state):
        mock_load_state.return_value = None
        
        result = main()
        assert result == 1

    @patch('session_validation_metrics.load_validation_state')
    def test_main_zero_total(self, mock_load_state):
        mock_load_state.return_value = {
            'total_subjects': 0,
            'valid_subjects': 0,
            'excluded_subjects': []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('session_validation_metrics.Path') as mock_path:
                mock_path.return_value = Path(tmpdir) / "session_validation_metrics.json"
                
                result = main()
                
                assert result == 0
                with open(mock_path.return_value) as f:
                    data = json.load(f)
                assert data['pass_rate_percentage'] == 0.0