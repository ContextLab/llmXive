"""
Unit tests for the logging utility module.
"""

import pytest
import logging
import sys
from io import StringIO
from pathlib import Path
from datetime import datetime

# Import the module under test
from src.utils.logging import (
    get_logger,
    set_log_level,
    setup_logger,
    log_info,
    log_warning,
    log_error,
    log_critical,
    flag_edge_case,
    get_edge_cases,
    clear_edge_cases,
    log_data_quality_issue,
    get_data_quality_issues,
    clear_data_quality_issues,
    log_provenance_mismatch,
    get_provenance_mismatches,
    clear_provenance_mismatches,
    log_label_validation_issue,
    get_label_validation_issues,
    clear_label_validation_issues,
    generate_edge_case_report
)


class TestSetupLogger:
    def test_get_logger_creates_instance(self):
        """Test that get_logger creates a logger instance."""
        logger = get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive"

    def test_get_logger_with_name(self):
        """Test that get_logger creates a named logger."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "llmXive.test_module"

    def test_setup_logger_with_file(self, tmp_path):
        """Test setup_logger with a file output."""
        log_file = tmp_path / "test.log"
        logger = setup_logger(log_file=log_file, level=logging.DEBUG)
        assert isinstance(logger, logging.Logger)
        assert log_file.exists()

    def test_set_log_level(self):
        """Test setting log level."""
        set_log_level(logging.DEBUG)
        logger = get_logger()
        assert logger.level == logging.DEBUG


class TestLogWarning:
    def test_log_warning_outputs_message(self, caplog):
        """Test that log_warning outputs a warning message."""
        with caplog.at_level(logging.WARNING):
            log_warning("Test warning message")
        assert "Test warning message" in caplog.text
        assert "WARNING" in caplog.text

    def test_log_warning_with_module(self, caplog):
        """Test log_warning with module context."""
        with caplog.at_level(logging.WARNING):
            log_warning("Module warning", module="test_module")
        assert "test_module" in caplog.text or "WARNING" in caplog.text


class TestLogError:
    def test_log_error_outputs_message(self, caplog):
        """Test that log_error outputs an error message."""
        with caplog.at_level(logging.ERROR):
            log_error("Test error message")
        assert "Test error message" in caplog.text
        assert "ERROR" in caplog.text


class TestLogCritical:
    def test_log_critical_outputs_message(self, caplog):
        """Test that log_critical outputs a critical message."""
        with caplog.at_level(logging.CRITICAL):
            log_critical("Test critical message")
        assert "Test critical message" in caplog.text
        assert "CRITICAL" in caplog.text


class TestFlagEdgeCase:
    def setup_method(self):
        """Clear edge cases before each test."""
        clear_edge_cases()

    def test_flag_edge_case_adds_entry(self):
        """Test that flag_edge_case adds an entry to the list."""
        flag_edge_case("missing_label", "Label is missing", {"id": "123"})
        cases = get_edge_cases()
        assert len(cases) == 1
        assert cases[0]["category"] == "missing_label"
        assert cases[0]["description"] == "Label is missing"
        assert cases[0]["context"]["id"] == "123"
        assert "timestamp" in cases[0]

    def test_flag_edge_case_without_context(self):
        """Test flagging edge case without context."""
        flag_edge_case("outlier", "Value is outlier")
        cases = get_edge_cases()
        assert len(cases) == 1
        assert cases[0]["context"] == {}


class TestSpecializedLoggingFunctions:
    def setup_method(self):
        """Clear all tracking lists before each test."""
        clear_edge_cases()
        clear_data_quality_issues()
        clear_provenance_mismatches()
        clear_label_validation_issues()

    def test_log_data_quality_issue(self):
        """Test logging data quality issues."""
        log_data_quality_issue("nan_values", "Found NaN in column X", data_id="row_1")
        issues = get_data_quality_issues()
        assert len(issues) == 1
        assert issues[0]["issue_type"] == "nan_values"
        assert issues[0]["data_id"] == "row_1"

    def test_log_provenance_mismatch(self):
        """Test logging provenance mismatches."""
        log_provenance_mismatch("rec_001", "kinetic", "product", "Invalid source")
        mismatches = get_provenance_mismatches()
        assert len(mismatches) == 1
        assert mismatches[0]["record_id"] == "rec_001"
        assert mismatches[0]["expected"] == "kinetic"
        assert mismatches[0]["actual"] == "product"

    def test_log_label_validation_issue(self):
        """Test logging label validation issues."""
        log_label_validation_issue("rec_002", "SN1", "Invalid class label")
        issues = get_label_validation_issues()
        assert len(issues) == 1
        assert issues[0]["record_id"] == "rec_002"
        assert issues[0]["label"] == "SN1"


class TestLoggerAccess:
    def test_multiple_get_logger_calls_return_same_base(self):
        """Test that multiple calls to get_logger return the same base logger."""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2

    def test_named_loggers_are_children(self):
        """Test that named loggers are children of the base logger."""
        base = get_logger()
        child = get_logger("child")
        assert child.name == "llmXive.child"


class TestEdgeCaseCategories:
    def setup_method(self):
        """Clear all lists before each test."""
        clear_edge_cases()
        clear_data_quality_issues()
        clear_provenance_mismatches()
        clear_label_validation_issues()

    def test_clear_edge_cases(self):
        """Test clearing edge cases."""
        flag_edge_case("test", "Test case")
        assert len(get_edge_cases()) == 1
        clear_edge_cases()
        assert len(get_edge_cases()) == 0

    def test_clear_data_quality_issues(self):
        """Test clearing data quality issues."""
        log_data_quality_issue("test", "Test issue")
        assert len(get_data_quality_issues()) == 1
        clear_data_quality_issues()
        assert len(get_data_quality_issues()) == 0

    def test_clear_provenance_mismatches(self):
        """Test clearing provenance mismatches."""
        log_provenance_mismatch("id", "a", "b", "reason")
        assert len(get_provenance_mismatches()) == 1
        clear_provenance_mismatches()
        assert len(get_provenance_mismatches()) == 0

    def test_clear_label_validation_issues(self):
        """Test clearing label validation issues."""
        log_label_validation_issue("id", "val", "issue")
        assert len(get_label_validation_issues()) == 1
        clear_label_validation_issues()
        assert len(get_label_validation_issues()) == 0

    def test_generate_edge_case_report(self, tmp_path):
        """Test generating the edge case report."""
        flag_edge_case("cat1", "desc1")
        log_data_quality_issue("type1", "msg1")
        log_provenance_mismatch("id1", "a", "b", "r1")
        log_label_validation_issue("id2", "v", "i")

        report_path = tmp_path / "report.json"
        report = generate_edge_case_report(report_path)

        assert report_path.exists()
        assert report["summary"]["total_edge_cases"] == 1
        assert report["summary"]["total_data_quality_issues"] == 1
        assert report["summary"]["total_provenance_mismatches"] == 1
        assert report["summary"]["total_label_validation_issues"] == 1
        assert "generated_at" in report