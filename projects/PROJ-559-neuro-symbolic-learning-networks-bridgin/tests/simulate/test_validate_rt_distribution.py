"""
Unit tests for validate_rt_distribution.py
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from simulate.validate_rt_distribution import (
    load_simulation_logs,
    validate_rt_distribution,
    MAX_ALLOWED_GAP_DURATION,
    BIN_WIDTH_SECONDS
)

class TestLoadSimulationLogs:
    def test_load_valid_logs(self, tmp_path):
        """Test loading valid simulation logs."""
        log_file = tmp_path / "simulation_logs.csv"
        data = {
            'response_time_seconds': [1.5, 2.3, 4.1, 5.2, 3.8],
            'student_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'condition': ['neural', 'neural', 'symbolic', 'neuro_symbolic', 'neural']
        }
        df = pd.DataFrame(data)
        df.to_csv(log_file, index=False)
        
        loaded_df = load_simulation_logs(str(log_file))
        assert len(loaded_df) == 5
        assert 'response_time_seconds' in loaded_df.columns

    def test_load_missing_file(self, tmp_path):
        """Test loading from a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_simulation_logs(str(tmp_path / "nonexistent.csv"))

    def test_load_missing_columns(self, tmp_path):
        """Test loading a file with missing required columns raises ValueError."""
        log_file = tmp_path / "bad_logs.csv"
        data = {
            'student_id': ['S1', 'S2'],
            'condition': ['neural', 'symbolic']
        }
        pd.DataFrame(data).to_csv(log_file, index=False)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            load_simulation_logs(str(log_file))

    def test_load_empty_valid_data(self, tmp_path):
        """Test loading a file with valid columns but no data raises ValueError."""
        log_file = tmp_path / "empty_logs.csv"
        data = {
            'response_time_seconds': [],
            'student_id': [],
            'condition': []
        }
        pd.DataFrame(data).to_csv(log_file, index=False)
        
        with pytest.raises(ValueError, match="No valid response time records found"):
            load_simulation_logs(str(log_file))

class TestValidateRtDistribution:
    def test_no_empty_bins(self):
        """Test distribution with no empty bins passes."""
        # Create data that fills every bin
        # 5 bins of 5s each -> 0-5, 5-10, 10-15, 15-20, 20-25
        data = [2.5, 7.5, 12.5, 17.5, 22.5]
        df = pd.DataFrame({'response_time_seconds': data})
        
        result = validate_rt_distribution(df, bin_width=5.0)
        assert result['validation_passed'] is True
        assert result['max_consecutive_empty_bins'] == 0

    def test_single_empty_bin(self):
        """Test distribution with one empty bin (5s gap) passes (<= 5s)."""
        # Create data with a gap in the middle
        # Bins: 0-5 (filled), 5-10 (empty), 10-15 (filled)
        data = [2.5, 12.5]
        df = pd.DataFrame({'response_time_seconds': data})
        
        result = validate_rt_distribution(df, bin_width=5.0)
        # 1 empty bin = 5.0s duration. Allowed if <= 5.0.
        assert result['validation_passed'] is True
        assert result['max_consecutive_empty_bins'] == 1
        assert result['max_consecutive_gap_duration_seconds'] == 5.0

    def test_two_consecutive_empty_bins(self):
        """Test distribution with two consecutive empty bins (10s gap) fails."""
        # Create data with a gap of 10s
        # Bins: 0-5 (filled), 5-10 (empty), 10-15 (empty), 15-20 (filled)
        data = [2.5, 17.5]
        df = pd.DataFrame({'response_time_seconds': data})
        
        result = validate_rt_distribution(df, bin_width=5.0)
        # 2 empty bins = 10.0s duration. Fails if > 5.0.
        assert result['validation_passed'] is False
        assert result['max_consecutive_empty_bins'] == 2
        assert result['max_consecutive_gap_duration_seconds'] == 10.0

    def test_large_gap(self):
        """Test distribution with a large gap fails."""
        # Create data with a gap of 20s (4 empty bins)
        data = [2.5, 27.5]
        df = pd.DataFrame({'response_time_seconds': data})
        
        result = validate_rt_distribution(df, bin_width=5.0)
        assert result['validation_passed'] is False
        assert result['max_consecutive_empty_bins'] == 4
        assert result['max_consecutive_gap_duration_seconds'] == 20.0

    def test_multiple_gaps(self):
        """Test distribution with multiple gaps, one of which is too large."""
        # Gap 1: 5s (1 bin) - OK
        # Gap 2: 10s (2 bins) - Fail
        # Data: 2.5 (bin 0), 12.5 (bin 2), 17.5 (bin 3), 22.5 (bin 4)
        # Bins: 0-5 (filled), 5-10 (empty), 10-15 (filled), 15-20 (filled), 20-25 (filled)
        # Wait, 12.5 is in 10-15. 17.5 is in 15-20.
        # Let's construct:
        # 0-5: filled (2.5)
        # 5-10: empty
        # 10-15: filled (12.5)
        # 15-20: empty
        # 20-25: empty
        # 25-30: filled (27.5)
        # Gap 1: 5-10 (5s)
        # Gap 2: 15-25 (10s) -> Should fail
        data = [2.5, 12.5, 27.5]
        df = pd.DataFrame({'response_time_seconds': data})
        
        result = validate_rt_distribution(df, bin_width=5.0)
        assert result['validation_passed'] is False
        assert result['max_consecutive_empty_bins'] == 2
        assert result['max_consecutive_gap_duration_seconds'] == 10.0

class TestIntegration:
    def test_full_pipeline(self, tmp_path):
        """Test the full pipeline with a valid dataset."""
        log_file = tmp_path / "simulation_logs.csv"
        output_file = tmp_path / "validation_report.json"
        
        # Create valid data
        data = {
            'response_time_seconds': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            'student_id': [f'S{i}' for i in range(10)],
            'condition': ['neural'] * 10
        }
        pd.DataFrame(data).to_csv(log_file, index=False)
        
        # Run validation logic directly
        df = load_simulation_logs(str(log_file))
        result = validate_rt_distribution(df, bin_width=5.0)
        
        assert result['validation_passed'] is True
        assert result['sample_size'] == 10

    def test_full_pipeline_failure(self, tmp_path):
        """Test the full pipeline with an invalid dataset."""
        log_file = tmp_path / "simulation_logs.csv"
        
        # Create data with a large gap
        data = {
            'response_time_seconds': [1.0, 20.0],
            'student_id': ['S1', 'S2'],
            'condition': ['neural', 'neural']
        }
        pd.DataFrame(data).to_csv(log_file, index=False)
        
        df = load_simulation_logs(str(log_file))
        result = validate_rt_distribution(df, bin_width=5.0)
        
        assert result['validation_passed'] is False