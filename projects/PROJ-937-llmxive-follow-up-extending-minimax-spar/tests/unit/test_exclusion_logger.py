"""
Unit tests for the exclusion logger functionality.
"""
import pytest
from unittest.mock import MagicMock, patch
import logging
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from eval.exclusion_logger import (
    validate_needle_presence,
    log_exclusion,
    scan_dataset_for_exclusions,
    logger
)


class TestValidateNeedlePresence:
    """Tests for validate_needle_presence function."""

    def test_needle_found_in_context(self):
        """Test that a sample with needle in context is valid."""
        sample = {
            "context": "This is a long text with a hidden needle string in the middle.",
            "id": "sample_1"
        }
        is_valid, error = validate_needle_presence(sample, needle_patterns=["needle"])
        assert is_valid is True
        assert error is None

    def test_needle_found_in_needle_field(self):
        """Test that a sample with needle in dedicated field is valid."""
        sample = {
            "context": "Some other text...",
            "needle": "specific_target_string",
            "id": "sample_2"
        }
        is_valid, error = validate_needle_presence(sample, needle_patterns=["specific_target_string"])
        assert is_valid is True
        assert error is None

    def test_needle_missing(self):
        """Test that a sample without needle is invalid."""
        sample = {
            "context": "This text has no needle or target string.",
            "id": "sample_3"
        }
        is_valid, error = validate_needle_presence(sample, needle_patterns=["needle", "target"])
        assert is_valid is False
        assert "not found" in error

    def test_missing_text_content(self):
        """Test that a sample with no text content is invalid."""
        sample = {
            "id": "sample_4"
        }
        is_valid, error = validate_needle_presence(sample)
        assert is_valid is False
        assert "Missing text content" in error

    def test_case_insensitive_match(self):
        """Test that needle matching is case insensitive."""
        sample = {
            "context": "This has a NEEDLE string.",
            "id": "sample_5"
        }
        is_valid, error = validate_needle_presence(sample, needle_patterns=["needle"])
        assert is_valid is True
        assert error is None

    def test_regex_pattern_match(self):
        """Test that regex patterns work correctly."""
        sample = {
            "context": "The number is 12345 in this text.",
            "id": "sample_6"
        }
        is_valid, error = validate_needle_presence(sample, needle_patterns=[r"\d{5}"])
        assert is_valid is True
        assert error is None


class TestLogExclusion:
    """Tests for log_exclusion function."""

    @patch('eval.exclusion_logger.logger')
    def test_log_exclusion_basic(self, mock_logger):
        """Test that log_exclusion calls logger.warning with correct data."""
        log_exclusion("sample_123", "missing needle")
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        
        # Check the message
        assert call_args[0][0] == "Sample excluded"
        
        # Check the extra data
        extra_data = call_args[1]['extra']
        assert extra_data['event'] == 'sample_excluded'
        assert extra_data['sample_id'] == 'sample_123'
        assert extra_data['reason'] == 'missing needle'

    @patch('eval.exclusion_logger.logger')
    def test_log_exclusion_with_snippet(self, mock_logger):
        """Test that log_exclusion includes sample snippet when provided."""
        sample_data = {"context": "A" * 200, "id": "test"}
        log_exclusion("sample_456", "corrupted", sample_data)
        
        call_args = mock_logger.warning.call_args
        extra_data = call_args[1]['extra']
        
        assert 'sample_snippet' in extra_data
        assert len(extra_data['sample_snippet']['context']) < 105  # Should be truncated
        assert "..." in extra_data['sample_snippet']['context']


class TestScanDatasetForExclusions:
    """Tests for scan_dataset_for_exclusions function."""

    def test_scan_valid_dataset(self):
        """Test scanning a dataset with all valid samples."""
        # Create a mock dataset
        mock_samples = [
            {"context": "Text with needle here", "id": f"i_{i}"} 
            for i in range(10)
        ]
        
        results = scan_dataset_for_exclusions(
            mock_samples, 
            needle_patterns=["needle"]
        )
        
        assert results['total_scanned'] == 10
        assert results['excluded_count'] == 0
        assert len(results['sample_ids_excluded']) == 0

    def test_scan_dataset_with_exclusions(self):
        """Test scanning a dataset with some invalid samples."""
        mock_samples = [
            {"context": "Valid with needle", "id": "v1"},
            {"context": "No needle here", "id": "v2"},
            {"context": "Another valid needle", "id": "v3"},
            {"id": "v4"},  # Missing content
        ]
        
        results = scan_dataset_for_exclusions(
            mock_samples, 
            needle_patterns=["needle"]
        )
        
        assert results['total_scanned'] == 4
        assert results['excluded_count'] == 2
        assert len(results['sample_ids_excluded']) == 2
        assert "v2" in results['sample_ids_excluded']
        assert "v4" in results['sample_ids_excluded']

    def test_max_samples_limit(self):
        """Test that max_samples limits the scan."""
        mock_samples = [
            {"context": "Valid with needle", "id": f"i_{i}"} 
            for i in range(100)
        ]
        
        results = scan_dataset_for_exclusions(
            mock_samples, 
            needle_patterns=["needle"],
            max_samples=10
        )
        
        assert results['total_scanned'] == 10
        assert results['excluded_count'] == 0

    def test_empty_dataset(self):
        """Test scanning an empty dataset."""
        results = scan_dataset_for_exclusions([], needle_patterns=["needle"])
        
        assert results['total_scanned'] == 0
        assert results['excluded_count'] == 0
        assert results['exclusion_rate'] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])