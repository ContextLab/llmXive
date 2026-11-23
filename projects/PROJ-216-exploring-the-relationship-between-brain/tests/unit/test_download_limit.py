import os
import sys
import json
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download import enforce_sample_limit

class TestSampleLimitEnforcement:
    """
    Unit tests for the N=10 sample limit enforcement logic (T015c).
    """

    def test_limit_not_exceeded(self):
        """Test that if subjects <= limit, all are returned."""
        subjects = ["sub-01", "sub-02", "sub-03"]
        limit = 10
        result = enforce_sample_limit(subjects, limit)
        assert result == subjects
        assert len(result) == 3

    def test_limit_exceeded_truncates(self):
        """Test that if subjects > limit, list is truncated to limit."""
        subjects = [f"sub-{i:03d}" for i in range(1, 16)] # 15 subjects
        limit = 10
        result = enforce_sample_limit(subjects, limit)
        assert len(result) == 10
        assert result == subjects[:10]
        assert result[0] == "sub-001"
        assert result[9] == "sub-010"

    def test_limit_exceeded_strictly(self):
        """Test truncation with a limit of 1."""
        subjects = ["sub-01", "sub-02", "sub-03"]
        limit = 1
        result = enforce_sample_limit(subjects, limit)
        assert len(result) == 1
        assert result == ["sub-01"]

    def test_empty_list(self):
        """Test behavior with empty subject list."""
        subjects = []
        limit = 10
        result = enforce_sample_limit(subjects, limit)
        assert result == []

    def test_limit_zero(self):
        """Test behavior with limit 0."""
        subjects = ["sub-01", "sub-02"]
        limit = 0
        result = enforce_sample_limit(subjects, limit)
        assert result == []

    @patch('download.logger')
    def test_logging_truncation(self, mock_logger):
        """Verify that a warning is logged when truncation occurs."""
        subjects = [f"sub-{i}" for i in range(1, 12)]
        limit = 5
        enforce_sample_limit(subjects, limit)
        
        # Check that warning was called
        assert mock_logger.warning.called
        call_args = mock_logger.warning.call_args[0][0]
        assert "EXCEED limit" in call_args
        assert "Truncating" in call_args

    @patch('download.logger')
    def test_logging_within_limit(self, mock_logger):
        """Verify that an info message is logged when within limit."""
        subjects = ["sub-01", "sub-02"]
        limit = 10
        enforce_sample_limit(subjects, limit)
        
        assert mock_logger.info.called
        call_args = mock_logger.info.call_args[0][0]
        assert "within limit" in call_args