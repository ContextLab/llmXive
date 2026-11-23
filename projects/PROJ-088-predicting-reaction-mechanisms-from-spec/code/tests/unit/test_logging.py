"""
Unit tests for the logging utilities in src/utils/logging.py
"""

import pytest
import logging
import sys
from io import StringIO
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import the module under test
import src.utils.logging as logging_utils


class TestSetupLogger:
    """Tests for setup_logger function"""
    
    def test_setup_logger_default(self):
        """Test logger setup with default parameters"""
        logger = logging_utils.setup_logger()
        assert logger is not None
        assert logger.name == "llmXive"
        assert logger.level == logging.INFO
        
        # Verify handlers are set up
        assert len(logger.handlers) > 0
    
    def test_setup_logger_with_file(self, tmp_path):
        """Test logger setup with file output"""
        log_file = tmp_path / "test.log"
        logger = logging_utils.setup_logger(log_file=str(log_file))
        
        assert logger is not None
        assert log_file.exists()
        
        # Log a message and verify file content
        logger.info("Test message")
        content = log_file.read_text()
        assert "Test message" in content
    
    def test_setup_logger_custom_level(self):
        """Test logger setup with custom log level"""
        logger = logging_utils.setup_logger(level=logging.DEBUG)
        assert logger.level == logging.DEBUG
    
    def test_setup_logger_custom_name(self):
        """Test logger setup with custom name"""
        logger = logging_utils.setup_logger(name="custom_logger")
        assert logger.name == "custom_logger"


class TestLogWarning:
    """Tests for log_warning function"""
    
    def test_log_warning_basic(self, caplog):
        """Test basic warning logging"""
        with caplog.at_level(logging.WARNING):
            logging_utils.log_warning("Test warning")
            assert "Test warning" in caplog.text
    
    def test_log_warning_with_category(self, caplog):
        """Test warning logging with category"""
        with caplog.at_level(logging.WARNING):
            logging_utils.log_warning("Test warning", category="data_quality")
            assert "[data_quality]" in caplog.text
    
    def test_log_warning_tracks_quality_issue(self):
        """Test that data quality warnings are tracked"""
        logging_utils.clear_data_quality_issues()
        logging_utils.log_warning(
            "Test quality issue", 
            category="data_quality",
            extra_info="test"
        )
        issues = logging_utils.get_data_quality_issues()
        assert len(issues) == 1
        assert "Test quality issue" in issues[0]["message"]


class TestLogError:
    """Tests for log_error function"""
    
    def test_log_error_basic(self, caplog):
        """Test basic error logging"""
        with caplog.at_level(logging.ERROR):
            logging_utils.log_error("Test error")
            assert "Test error" in caplog.text
    
    def test_log_error_with_metadata(self, caplog):
        """Test error logging with additional metadata"""
        with caplog.at_level(logging.ERROR):
            logging_utils.log_error("Test error", code=500, context="test")
            assert "Test error" in caplog.text


class TestLogCritical:
    """Tests for log_critical function"""
    
    def test_log_critical_basic(self, caplog):
        """Test basic critical logging"""
        with caplog.at_level(logging.CRITICAL):
            logging_utils.log_critical("Critical issue")
            assert "Critical issue" in caplog.text


class TestFlagEdgeCase:
    """Tests for flag_edge_case function"""
    
    def test_flag_edge_case_valid_category(self):
        """Test flagging edge case with valid category"""
        logging_utils.clear_edge_cases()
        logging_utils.flag_edge_case(
            category="missing_data",
            description="Test missing data"
        )
        edge_cases = logging_utils.get_edge_cases()
        assert len(edge_cases) == 1
        assert edge_cases[0]["category"] == "missing_data"
        assert edge_cases[0]["description"] == "Test missing data"
    
    def test_flag_edge_case_invalid_category(self):
        """Test that invalid category raises error"""
        with pytest.raises(ValueError):
            logging_utils.flag_edge_case(
                category="invalid_category",
                description="Test"
            )
    
    def test_flag_edge_case_with_context(self):
        """Test edge case with data context"""
        logging_utils.clear_edge_cases()
        context = {"row_id": 123, "column": "value"}
        logging_utils.flag_edge_case(
            category="outliers",
            description="Outlier detected",
            data_context=context
        )
        edge_cases = logging_utils.get_edge_cases()
        assert edge_cases[0]["data_context"] == context
    
    def test_flag_edge_case_severity_levels(self):
        """Test different severity levels"""
        logging_utils.clear_edge_cases()
        logging_utils.flag_edge_case(
            category="missing_data",
            description="Critical issue",
            severity="critical"
        )
        edge_cases = logging_utils.get_edge_cases()
        assert edge_cases[0]["severity"] == "critical"


class TestSpecializedLoggingFunctions:
    """Tests for specialized logging functions"""
    
    def test_log_data_quality_issue(self):
        """Test data quality issue logging"""
        logging_utils.clear_data_quality_issues()
        logging_utils.log_data_quality_issue(
            issue_type="missing_values",
            description="Missing values in column X",
            affected_records=10,
            severity="warning"
        )
        issues = logging_utils.get_data_quality_issues()
        assert len(issues) == 1
        assert issues[0]["issue_type"] == "missing_values"
        assert issues[0]["affected_records"] == 10
    
    def test_log_label_validation_issue(self):
        """Test label validation issue logging"""
        logging_utils.clear_label_validation_issues()
        logging_utils.log_label_validation_issue(
            label="invalid_label",
            issue="Label not in valid set",
            sample_id="sample_123"
        )
        issues = logging_utils.get_label_validation_issues()
        assert len(issues) == 1
        assert issues[0]["label"] == "invalid_label"
        assert issues[0]["sample_id"] == "sample_123"
    
    def test_log_provenance_mismatch(self):
        """Test provenance mismatch logging"""
        logging_utils.clear_provenance_mismatches()
        logging_utils.log_provenance_mismatch(
            expected="kinetic_studies",
            actual="product_structure",
            source="nist_webbook",
            record_id="rec_456"
        )
        mismatches = logging_utils.get_provenance_mismatches()
        assert len(mismatches) == 1
        assert mismatches[0]["expected"] == "kinetic_studies"
        assert mismatches[0]["actual"] == "product_structure"


class TestLoggerAccess:
    """Tests for logger access and configuration"""
    
    def test_get_logger(self):
        """Test getting the global logger"""
        logger = logging_utils.get_logger()
        assert logger is not None
        assert isinstance(logger, logging.Logger)
    
    def test_set_log_level(self):
        """Test setting log level"""
        original_level = logging_utils._log_level
        logging_utils.set_log_level(logging.DEBUG)
        assert logging_utils._log_level == logging.DEBUG
        # Restore
        logging_utils.set_log_level(original_level)
    
    def test_generate_edge_case_report(self):
        """Test generating edge case report"""
        logging_utils.clear_edge_cases()
        logging_utils.clear_data_quality_issues()
        logging_utils.clear_provenance_mismatches()
        logging_utils.clear_label_validation_issues()
        
        # Add some test data
        logging_utils.flag_edge_case("missing_data", "Test 1")
        logging_utils.flag_edge_case("outliers", "Test 2")
        logging_utils.log_data_quality_issue("missing_values", "Test 3")
        
        report = logging_utils.generate_edge_case_report()
        
        assert "timestamp" in report
        assert "edge_cases" in report
        assert "data_quality_issues" in report
        assert "provenance_mismatches" in report
        assert "label_validation_issues" in report
        assert report["edge_cases"]["total"] == 2
        assert report["data_quality_issues"]["total"] == 1


class TestEdgeCaseCategories:
    """Tests for edge case category handling"""
    
    def test_all_categories_defined(self):
        """Test that all expected categories are defined"""
        expected_categories = [
            "missing_data", "outliers", "provenance_mismatch",
            "label_validation", "class_imbalance", "data_quality",
            "configuration", "performance"
        ]
        for category in expected_categories:
            assert category in logging_utils.EDGE_CASE_CATEGORIES
    
    def test_category_descriptions(self):
        """Test that categories have descriptions"""
        for category, description in logging_utils.EDGE_CASE_CATEGORIES.items():
            assert isinstance(description, str)
            assert len(description) > 0
    
    def test_clear_functions(self):
        """Test clear functions"""
        # Add test data
        logging_utils.flag_edge_case("missing_data", "Test")
        logging_utils.log_data_quality_issue("missing", "Test")
        logging_utils.log_provenance_mismatch("exp", "act", "src")
        logging_utils.log_label_validation_issue("lbl", "issue")
        
        assert len(logging_utils.get_edge_cases()) > 0
        assert len(logging_utils.get_data_quality_issues()) > 0
        assert len(logging_utils.get_provenance_mismatches()) > 0
        assert len(logging_utils.get_label_validation_issues()) > 0
        
        # Clear all
        logging_utils.clear_edge_cases()
        logging_utils.clear_data_quality_issues()
        logging_utils.clear_provenance_mismatches()
        logging_utils.clear_label_validation_issues()
        
        assert len(logging_utils.get_edge_cases()) == 0
        assert len(logging_utils.get_data_quality_issues()) == 0
        assert len(logging_utils.get_provenance_mismatches()) == 0
        assert len(logging_utils.get_label_validation_issues()) == 0