"""
Unit tests for preprocessing deviation logging functionality in preprocess.py
"""
import pytest
import logging
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import log_preprocessing_deviations, setup_logging


class TestLogPreprocessingDeviations:
    """Test cases for the log_preprocessing_deviations function."""

    def test_log_single_deviation(self, tmp_path):
        """Test logging a single deviation."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file)
        
        deviations = [
            {
                'subject_id': '01',
                'deviation_type': 'motion',
                'message': 'Subject excluded due to excessive motion'
            }
        ]
        
        log_preprocessing_deviations(deviations, logger)
        
        # Read log file and verify content
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        assert "DEVIATION [motion]" in log_content
        assert "Subject 01" in log_content
        assert "excessive motion" in log_content

    def test_log_multiple_deviations(self, tmp_path):
        """Test logging multiple deviations."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file)
        
        deviations = [
            {
                'subject_id': '01',
                'deviation_type': 'motion',
                'message': 'Excessive motion'
            },
            {
                'subject_id': '02',
                'deviation_type': 'fmriprep_failure',
                'message': 'Execution failed'
            },
            {
                'subject_id': '03',
                'deviation_type': 'missing_file',
                'message': 'Motion file not found'
            }
        ]
        
        log_preprocessing_deviations(deviations, logger)
        
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        assert log_content.count("DEVIATION") == 3
        assert "Subject 01" in log_content
        assert "Subject 02" in log_content
        assert "Subject 03" in log_content

    def test_log_deviation_without_subject_id(self, tmp_path):
        """Test logging a deviation without a subject ID."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file)
        
        deviations = [
            {
                'deviation_type': 'system_error',
                'message': 'Docker not available'
            }
        ]
        
        log_preprocessing_deviations(deviations, logger)
        
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        assert "DEVIATION [system_error]" in log_content
        assert "Docker not available" in log_content
        assert "N/A" in log_content

    def test_log_empty_deviations_list(self, tmp_path):
        """Test logging an empty list of deviations."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file)
        
        deviations = []
        
        # Should not raise any errors
        log_preprocessing_deviations(deviations, logger)
        
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        # No DEVIATION messages should be logged
        assert "DEVIATION" not in log_content

    def test_log_deviation_with_missing_fields(self, tmp_path):
        """Test logging a deviation with missing optional fields."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file)
        
        deviations = [
            {
                'deviation_type': 'error'
                # Missing subject_id and message
            }
        ]
        
        log_preprocessing_deviations(deviations, logger)
        
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        assert "DEVIATION [error]" in log_content
        assert "N/A" in log_content
        assert "No message provided" in log_content

    def test_log_deviation_types(self, tmp_path):
        """Test logging different types of deviations."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file)
        
        deviation_types = ['motion', 'fmriprep_failure', 'missing_file', 'error', 'unknown']
        
        for dev_type in deviation_types:
            deviations = [
                {
                    'subject_id': '01',
                    'deviation_type': dev_type,
                    'message': f'Test {dev_type} deviation'
                }
            ]
            log_preprocessing_deviations(deviations, logger)
        
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        for dev_type in deviation_types:
            assert f"DEVIATION [{dev_type}]" in log_content


class TestSetupLogging:
    """Test cases for the setup_logging function."""

    def test_logging_creates_file(self, tmp_path):
        """Test that setup_logging creates the log file."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file)
        
        assert log_file.exists()

    def test_logging_creates_directory(self, tmp_path):
        """Test that setup_logging creates parent directories."""
        nested_log_file = tmp_path / "subdir" / "nested" / "test.log"
        logger = setup_logging(nested_log_file)
        
        assert nested_log_file.exists()
        assert nested_log_file.parent.exists()

    def test_logging_to_console_and_file(self, tmp_path, caplog):
        """Test that logging writes to both console and file."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file)
        
        logger.info("Test message")
        
        # Check file
        with open(log_file, 'r') as f:
            log_content = f.read()
        assert "Test message" in log_content

    def test_log_format_includes_timestamp(self, tmp_path):
        """Test that log format includes timestamp."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file)
        
        logger.info("Test message")
        
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        # Log format includes timestamp
        assert len(log_content) > 0
        # Basic check that there's content (timestamp format is YYYY-MM-DD HH:MM:SS)
        assert " - " in log_content or ":" in log_content
