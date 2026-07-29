import pytest
from unittest.mock import MagicMock, patch
from code.eval.exclusion_logger import validate_needle_presence, log_exclusion, scan_dataset_for_exclusions
import logging

class TestValidateNeedlePresence:
    def test_needle_found(self):
        sample = {"needle": "test", "context": "This is a test string"}
        is_valid, reason = validate_needle_presence(sample)
        assert is_valid is True
        assert reason == "Found"

    def test_needle_missing(self):
        sample = {"needle": "missing", "context": "This is a test string"}
        is_valid, reason = validate_needle_presence(sample)
        assert is_valid is False
        assert "not found" in reason

    def test_missing_needle_key(self):
        sample = {"context": "This is a test string"}
        is_valid, reason = validate_needle_presence(sample)
        assert is_valid is False
        assert "Missing" in reason

    def test_missing_context_key(self):
        sample = {"needle": "test"}
        is_valid, reason = validate_needle_presence(sample)
        assert is_valid is False
        assert "Missing" in reason

    def test_empty_needle(self):
        sample = {"needle": "", "context": "This is a test string"}
        is_valid, reason = validate_needle_presence(sample)
        assert is_valid is False
        assert "empty" in reason

    def test_empty_context(self):
        sample = {"needle": "test", "context": ""}
        is_valid, reason = validate_needle_presence(sample)
        assert is_valid is False
        assert "empty" in reason

class TestLogExclusion:
    def test_log_exclusion_called(self):
        mock_logger = MagicMock(spec=logging.Logger)
        log_exclusion("sample_1", "Reason: Missing needle", mock_logger)
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "sample_1" in call_args[0][0]
        assert "Missing needle" in call_args[0][0]

class TestScanDatasetForExclusions:
    def test_scan_all_valid(self):
        dataset = [
            {"id": "1", "needle": "a", "context": "contains a"},
            {"id": "2", "needle": "b", "context": "contains b"}
        ]
        mock_logger = MagicMock(spec=logging.Logger)
        results = scan_dataset_for_exclusions(dataset, mock_logger)
        
        assert results["total_samples"] == 2
        assert results["excluded_count"] == 0
        assert results["valid_count"] == 2
        assert results["exclusion_reasons"] == {}

    def test_scan_all_invalid(self):
        dataset = [
            {"id": "1", "needle": "x", "context": "no x here"},
            {"id": "2", "needle": "y", "context": "no y here"}
        ]
        mock_logger = MagicMock(spec=logging.Logger)
        results = scan_dataset_for_exclusions(dataset, mock_logger)
        
        assert results["total_samples"] == 2
        assert results["excluded_count"] == 2
        assert results["valid_count"] == 0
        assert "not found" in results["exclusion_reasons"]

    def test_scan_mixed(self):
        dataset = [
            {"id": "1", "needle": "a", "context": "contains a"},
            {"id": "2", "needle": "x", "context": "no x here"},
            {"id": "3", "needle": "b", "context": "contains b"}
        ]
        mock_logger = MagicMock(spec=logging.Logger)
        results = scan_dataset_for_exclusions(dataset, mock_logger)
        
        assert results["total_samples"] == 3
        assert results["excluded_count"] == 1
        assert results["valid_count"] == 2

    def test_scan_missing_keys(self):
        dataset = [
            {"id": "1", "context": "valid"}, # missing needle
            {"id": "2", "needle": "a"}       # missing context
        ]
        mock_logger = MagicMock(spec=logging.Logger)
        results = scan_dataset_for_exclusions(dataset, mock_logger)
        
        assert results["total_samples"] == 2
        assert results["excluded_count"] == 2
        # Should have reasons for missing keys
        assert any("Missing" in r for r in results["exclusion_reasons"].keys())