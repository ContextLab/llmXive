import pytest
import logging
from pathlib import Path
import tempfile
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.logging_utils import setup_logging, get_logger, log_data_ingestion_step, log_coverage_audit_result

class TestLoggingUtils:
    def test_setup_logging_creates_file(self, tmp_path):
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=log_file, level=logging.INFO)
        
        assert logger is not None
        assert log_file.exists()
        
        # Write a test log
        logger.info("Test message")
        
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test message" in content

    def test_log_data_ingestion_step_logs_info(self, caplog, tmp_path):
        log_file = tmp_path / "test_ingest.log"
        setup_logging(log_file=log_file, level=logging.INFO)
        logger = get_logger(__name__)
        
        with caplog.at_level(logging.INFO):
            log_data_ingestion_step(
                logger,
                step_name="Test Step",
                total_count=100,
                matched_count=90,
                mismatched_count=5,
                missing_count=5,
                source="TestSource"
            )
        
        assert "Test Step" in caplog.text
        assert "Matched: 90" in caplog.text
        assert "Mismatched: 5" in caplog.text

    def test_log_data_ingestion_step_warns_on_mismatches(self, caplog, tmp_path):
        log_file = tmp_path / "test_warn.log"
        setup_logging(log_file=log_file, level=logging.WARNING)
        logger = get_logger(__name__)
        
        with caplog.at_level(logging.WARNING):
            log_data_ingestion_step(
                logger,
                step_name="Bad Step",
                total_count=100,
                matched_count=50,
                mismatched_count=50,
                missing_count=0,
                source="TestSource"
            )
        
        assert "Bad Step" in caplog.text
        assert "WARNING" in caplog.text

    def test_log_coverage_audit_result_warns_on_significance(self, caplog, tmp_path):
        log_file = tmp_path / "test_audit.log"
        setup_logging(log_file=log_file, level=logging.WARNING)
        logger = get_logger(__name__)
        
        with caplog.at_level(logging.WARNING):
            log_coverage_audit_result(
                logger,
                property_name="mu",
                p_value=0.01,
                is_significant=True
            )
        
        assert "mu" in caplog.text
        assert "SIGNIFICANT DIFFERENCE" in caplog.text

    def test_log_coverage_audit_result_info_on_no_significance(self, caplog, tmp_path):
        log_file = tmp_path / "test_audit_info.log"
        setup_logging(log_file=log_file, level=logging.INFO)
        logger = get_logger(__name__)
        
        with caplog.at_level(logging.INFO):
            log_coverage_audit_result(
                logger,
                property_name="alpha",
                p_value=0.8,
                is_significant=False
            )
        
        assert "alpha" in caplog.text
        assert "No significant difference" in caplog.text