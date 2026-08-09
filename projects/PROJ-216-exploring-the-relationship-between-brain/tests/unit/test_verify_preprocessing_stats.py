"""
Unit tests for verify_preprocessing_stats.py (T019a verification logic).
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_preprocessing_stats import verify_schema, REQUIRED_KEYS

class TestVerifyPreprocessingStats:
    
    def test_schema_valid(self):
        """Test that a valid schema passes verification."""
        valid_data = {
            "total_subjects": 10,
            "successful_subjects": 8,
            "success_rate_percentage": 80.0
        }
        assert verify_schema(valid_data) is True

    def test_schema_missing_key(self):
        """Test that missing keys are detected."""
        invalid_data = {
            "total_subjects": 10,
            "successful_subjects": 8
            # Missing success_rate_percentage
        }
        assert verify_schema(invalid_data) is False

    def test_schema_wrong_type_int(self):
        """Test that wrong type for total_subjects is detected."""
        invalid_data = {
            "total_subjects": "10",  # Should be int
            "successful_subjects": 8,
            "success_rate_percentage": 80.0
        }
        assert verify_schema(invalid_data) is False

    def test_schema_wrong_type_float(self):
        """Test that wrong type for success_rate_percentage is detected."""
        invalid_data = {
            "total_subjects": 10,
            "successful_subjects": 8,
            "success_rate_percentage": "80.0"  # Should be float
        }
        assert verify_schema(invalid_data) is False

    def test_schema_success_gt_total(self):
        """Test that successful > total is detected."""
        invalid_data = {
            "total_subjects": 10,
            "successful_subjects": 12,
            "success_rate_percentage": 120.0
        }
        assert verify_schema(invalid_data) is False

    def test_schema_not_dict(self):
        """Test that non-dict data is rejected."""
        assert verify_schema([1, 2, 3]) is False
        assert verify_schema("string") is False
        assert verify_schema(123) is False

    def test_required_keys_constant(self):
        """Verify the REQUIRED_KEYS constant matches the task description."""
        expected_keys = {"total_subjects", "successful_subjects", "success_rate_percentage"}
        assert REQUIRED_KEYS == expected_keys
