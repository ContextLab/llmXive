"""
Unit tests for T014b: Verify Quality.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Mock the config and logging to avoid side effects in tests
import sys
from unittest.mock import patch, MagicMock

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from data.verify_quality import calculate_mean_fd_from_processed_data, verify_quality

class TestCalculateMeanFd:
    def test_mean_fd_below_threshold(self, tmp_path):
        """Test calculation when mean FD is within acceptable range."""
        # Create a mock CSV
        df = pd.DataFrame({
            'subject_id': [1, 2, 3],
            'mean_fd': [0.1, 0.15, 0.18]
        })
        csv_path = tmp_path / "fd_metrics.csv"
        df.to_csv(csv_path, index=False)

        result = calculate_mean_fd_from_processed_data(tmp_path)
        
        # Expected mean: (0.1 + 0.15 + 0.18) / 3 = 0.1433...
        expected = df['mean_fd'].mean()
        assert np.isclose(result, expected)
        assert result <= 0.2

    def test_mean_fd_above_threshold(self, tmp_path):
        """Test calculation when mean FD exceeds threshold (should still calculate correctly)."""
        df = pd.DataFrame({
            'subject_id': [1, 2, 3],
            'mean_fd': [0.4, 0.5, 0.6]
        })
        csv_path = tmp_path / "fd_metrics.csv"
        df.to_csv(csv_path, index=False)

        result = calculate_mean_fd_from_processed_data(tmp_path)
        
        expected = df['mean_fd'].mean()
        assert np.isclose(result, expected)
        assert result > 0.2

    def test_missing_file_raises_error(self, tmp_path):
        """Test that missing data raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            calculate_mean_fd_from_processed_data(tmp_path)

    def test_missing_column_raises_error(self, tmp_path):
        """Test that missing 'mean_fd' column raises ValueError."""
        df = pd.DataFrame({
            'subject_id': [1, 2],
            'other_col': [10, 20]
        })
        csv_path = tmp_path / "fd_metrics.csv"
        df.to_csv(csv_path, index=False)

        with pytest.raises(ValueError):
            calculate_mean_fd_from_processed_data(tmp_path)

class TestVerifyQuality:
    @patch('data.verify_quality.info')
    @patch('data.verify_quality.warning')
    def test_quality_passes(self, mock_warn, mock_info, tmp_path):
        """Test successful verification."""
        df = pd.DataFrame({'subject_id': [1], 'mean_fd': [0.1]})
        df.to_csv(tmp_path / "fd_metrics.csv", index=False)

        with patch('data.verify_quality.DATA_PROCESSED_PATH', str(tmp_path)):
            result = verify_quality(threshold=0.2)

        assert result is True
        mock_info.assert_any_call("Quality check PASSED: Mean FD (0.1000 mm) is within threshold (0.2 mm).")
        mock_warn.assert_not_called()

    @patch('data.verify_quality.info')
    @patch('data.verify_quality.warning')
    def test_quality_warns(self, mock_warn, mock_info, tmp_path):
        """Test verification with warning."""
        df = pd.DataFrame({'subject_id': [1], 'mean_fd': [0.3]})
        df.to_csv(tmp_path / "fd_metrics.csv", index=False)

        with patch('data.verify_quality.DATA_PROCESSED_PATH', str(tmp_path)):
            result = verify_quality(threshold=0.2)

        assert result is True
        mock_warn.assert_called()
        assert "exceeds threshold" in str(mock_warn.call_args)

    @patch('data.verify_quality.error')
    def test_missing_directory(self, mock_error, tmp_path):
        """Test failure when directory does not exist."""
        fake_path = tmp_path / "non_existent"
        
        with patch('data.verify_quality.DATA_PROCESSED_PATH', str(fake_path)):
            result = verify_quality(threshold=0.2)

        assert result is False
        mock_error.assert_called()
