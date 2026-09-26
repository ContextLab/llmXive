import pytest
import os
import json
from pathlib import Path
import logging
from unittest.mock import patch, MagicMock

from data.logging_setup import setup_processing_logger, log_excluded_subjects, save_exclusion_report

class TestLoggingSetup:
    """Tests for the logging setup functionality."""

    def test_setup_logger_creates_file(self, tmp_path):
        """Test that setup_logger creates the log file."""
        log_path = tmp_path / "test_log.json"
        logger = setup_processing_logger(str(log_path))
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
        
        # The file should be created after logging something
        logger.info("Test message")
        assert log_path.exists()

    def test_setup_logger_has_handlers(self, tmp_path):
        """Test that setup_logger has both file and console handlers."""
        log_path = tmp_path / "test_log.json"
        logger = setup_processing_logger(str(log_path))
        
        assert len(logger.handlers) == 2
        
        # Check that one is a FileHandler
        file_handler = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handler) == 1

class TestLogExcludedSubjects:
    """Tests for logging excluded subjects."""

    def test_log_excluded_subjects_with_exclusions(self, tmp_path, caplog):
        """Test logging when there are excluded subjects."""
        log_path = tmp_path / "test_log.json"
        logger = setup_processing_logger(str(log_path))
        
        excluded_reasons = [
            {'subject_id': 'sub-001', 'reason': 'High motion (FD=0.6)'},
            {'subject_id': 'sub-002', 'reason': 'Missing metadata'}
        ]
        
        with caplog.at_level(logging.INFO):
            log_excluded_subjects(logger, excluded_reasons, total_processed=10, total_valid=8)
        
        # Check that the log contains the summary
        assert "Total subjects processed: 10" in caplog.text
        assert "Total valid subjects: 8" in caplog.text
        assert "Total excluded subjects: 2" in caplog.text
        assert "Excluded: sub-001" in caplog.text
        assert "Excluded: sub-002" in caplog.text

    def test_log_excluded_subjects_no_exclusions(self, tmp_path, caplog):
        """Test logging when there are no excluded subjects."""
        log_path = tmp_path / "test_log.json"
        logger = setup_processing_logger(str(log_path))
        
        with caplog.at_level(logging.INFO):
            log_excluded_subjects(logger, [], total_processed=10, total_valid=10)
        
        assert "Total excluded subjects: 0" in caplog.text
        assert "No subjects were excluded." in caplog.text

class TestSaveExclusionReport:
    """Tests for saving the exclusion report."""

    def test_save_exclusion_report_creates_file(self, tmp_path):
        """Test that save_exclusion_report creates the JSON file."""
        output_path = tmp_path / "exclusion_report.json"
        
        excluded_reasons = [
            {'subject_id': 'sub-001', 'reason': 'High motion'}
        ]
        
        save_exclusion_report(
            str(output_path),
            excluded_reasons,
            total_processed=10,
            total_valid=9
        )
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert report['summary']['total_processed'] == 10
        assert report['summary']['total_valid'] == 9
        assert report['summary']['total_excluded'] == 1
        assert len(report['excluded_subjects']) == 1
        assert report['excluded_subjects'][0]['subject_id'] == 'sub-001'

    def test_save_exclusion_report_empty_exclusions(self, tmp_path):
        """Test saving report with no excluded subjects."""
        output_path = tmp_path / "exclusion_report.json"
        
        save_exclusion_report(
            str(output_path),
            [],
            total_processed=5,
            total_valid=5
        )
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert report['summary']['total_excluded'] == 0
        assert report['excluded_subjects'] == []