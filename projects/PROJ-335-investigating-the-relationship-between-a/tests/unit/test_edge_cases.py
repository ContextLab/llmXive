"""
Unit tests for edge cases in the EEG processing pipeline.
Tests cover:
- N < 30 (insufficient power)
- Missing electrodes
- Empty datasets
- Invalid data types
"""
import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

# Import utilities from the project
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from utils.validation import (
    validate_eeg_channels,
    validate_behavioral_metrics,
    check_power_requirements,
    log_error,
    exit_on_validation_failure
)
from utils.logging_config import setup_logging, get_logger


class TestInsufficientSampleSize:
    """Test handling of N < 30 (insufficient power)"""

    def test_check_power_requirements_insufficient(self):
        """Test that N < 30 raises appropriate error"""
        with pytest.raises(ValueError) as excinfo:
            check_power_requirements(n_count=25, min_required=30)
        
        assert "INSUFFICIENT POWER" in str(excinfo.value)
        assert "25" in str(excinfo.value)
        assert "30" in str(excinfo.value)

    def test_check_power_requirements_limited(self, tmp_path):
        """Test that N=30-52 logs warning and creates status file"""
        status_file = tmp_path / "power_status.json"
        
        # This should NOT raise, but should create the status file
        result = check_power_requirements(n_count=40, min_required=30, status_file=str(status_file))
        
        assert result is True
        assert status_file.exists()
        
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        
        assert status_data['n_count'] == 40
        assert status_data['status'] == 'LIMITED'

    def test_check_power_requirements_sufficient(self):
        """Test that N > 52 proceeds without warning"""
        result = check_power_requirements(n_count=100, min_required=30)
        assert result is True


class TestMissingElectrodes:
    """Test handling of missing electrode data"""

    def test_validate_eeg_channels_missing_required(self):
        """Test validation fails when required electrodes are missing"""
        existing_channels = ['F3', 'F4', 'Fz', 'P3', 'P4']  # Missing Pz
        required_channels = {'F3', 'F4', 'Fz', 'P3', 'P4', 'Pz'}
        
        with pytest.raises(ValueError) as excinfo:
            validate_eeg_channels(existing_channels, required_channels)
        
        assert "CRITICAL: Missing required electrode data" in str(excinfo.value)
        assert "Pz" in str(excinfo.value)

    def test_validate_eeg_channels_all_present(self):
        """Test validation passes when all required electrodes are present"""
        existing_channels = ['F3', 'F4', 'Fz', 'P3', 'P4', 'Pz', 'Cz']
        required_channels = {'F3', 'F4', 'Fz', 'P3', 'P4', 'Pz'}
        
        result = validate_eeg_channels(existing_channels, required_channels)
        assert result is True

    def test_validate_eeg_channels_empty(self):
        """Test validation fails with empty channel list"""
        with pytest.raises(ValueError) as excinfo:
            validate_eeg_channels([], {'F3', 'F4'})
        
        assert "No EEG channels found" in str(excinfo.value)


class TestMissingBehavioralMetrics:
    """Test handling of missing behavioral measures"""

    def test_validate_behavioral_metrics_missing_k_score(self):
        """Test validation fails when k-scores are missing"""
        df = pd.DataFrame({
            'subject_id': ['S01', 'S02'],
            'accuracy': [0.8, 0.9]
            # Missing 'k_score' column
        })
        
        with pytest.raises(ValueError) as excinfo:
            validate_behavioral_metrics(df, required_metrics=['k_score'])
        
        assert "Missing behavioral measures" in str(excinfo.value)
        assert "k_score" in str(excinfo.value)

    def test_validate_behavioral_metrics_all_present(self):
        """Test validation passes when all required metrics are present"""
        df = pd.DataFrame({
            'subject_id': ['S01', 'S02'],
            'k_score': [4.5, 5.2],
            'd_prime': [1.2, 1.5]
        })
        
        result = validate_behavioral_metrics(df, required_metrics=['k_score', 'd_prime'])
        assert result is True

    def test_validate_behavioral_metrics_empty_dataframe(self):
        """Test validation fails with empty dataframe"""
        df = pd.DataFrame(columns=['subject_id', 'k_score'])
        
        with pytest.raises(ValueError) as excinfo:
            validate_behavioral_metrics(df, required_metrics=['k_score'])
        
        assert "No data" in str(excinfo.value) or "empty" in str(excinfo.value).lower()


class TestEdgeCaseDataTypes:
    """Test handling of invalid data types"""

    def test_validate_with_nan_values(self):
        """Test validation handles NaN values in behavioral metrics"""
        df = pd.DataFrame({
            'subject_id': ['S01', 'S02', 'S03'],
            'k_score': [4.5, np.nan, 5.2]
        })
        
        # Should raise warning or error for NaN values
        with pytest.raises(ValueError) as excinfo:
            validate_behavioral_metrics(df, required_metrics=['k_score'])
        
        assert "NaN" in str(excinfo.value) or "missing" in str(excinfo.value).lower()

    def test_validate_with_negative_values(self):
        """Test validation handles negative k-scores (invalid)"""
        df = pd.DataFrame({
            'subject_id': ['S01', 'S02'],
            'k_score': [-1.0, 5.2]  # Negative k-score is invalid
        })
        
        # Negative k-scores should be flagged
        with pytest.raises(ValueError) as excinfo:
            validate_behavioral_metrics(df, required_metrics=['k_score'])
        
        assert "negative" in str(excinfo.value).lower() or "invalid" in str(excinfo.value).lower()


class TestLoggingEdgeCases:
    """Test logging behavior in edge cases"""

    def test_log_error_creates_entry(self, tmp_path):
        """Test that log_error creates proper log entries"""
        log_file = tmp_path / "test_error.log"
        logger = setup_logging(log_file=str(log_file), level='ERROR')
        
        log_error(logger, "FR-006", "Test error message")
        
        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
            assert "FR-006" in content
            assert "Test error message" in content

    def test_exit_on_validation_failure(self, capsys):
        """Test that exit_on_validation_failure exits with code 1"""
        with pytest.raises(SystemExit) as excinfo:
            exit_on_validation_failure("Test validation failed")
        
        assert excinfo.value.code == 1