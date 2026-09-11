import os
import sys
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

from src.data.ingest import check_and_report_variables, validate_metadata_variables
from src.utils.logging import get_logger

class TestT004MissingMetadata:
    """
    Tests for T004: Log warning and skip datasets with missing metadata rather than crashing.
    """

    def test_validate_metadata_complete(self):
        """Test validation passes when all required variables are present."""
        dataset = {
            "id": "ds_complete",
            "metadata": {
                "stimulus_type": "tactile",
                "response_correctness": "binary"
            }
        }
        is_valid, missing = validate_metadata_variables(dataset, ["stimulus_type", "response_correctness"])
        assert is_valid is True
        assert len(missing) == 0

    def test_validate_metadata_missing_one(self):
        """Test validation fails when one variable is missing."""
        dataset = {
            "id": "ds_missing_one",
            "metadata": {
                "stimulus_type": "tactile"
                # response_correctness missing
            }
        }
        is_valid, missing = validate_metadata_variables(dataset, ["stimulus_type", "response_correctness"])
        assert is_valid is False
        assert "response_correctness" in missing

    def test_validate_metadata_missing_both(self):
        """Test validation fails when both variables are missing."""
        dataset = {
            "id": "ds_missing_both",
            "metadata": {}
        }
        is_valid, missing = validate_metadata_variables(dataset, ["stimulus_type", "response_correctness"])
        assert is_valid is False
        assert len(missing) == 2

    def test_check_and_report_variables_skips_missing(self, caplog):
        """
        Test that check_and_report_variables logs a warning and returns False
        when metadata is missing, instead of crashing.
        """
        dataset = {
            "id": "ds_skip_me",
            "metadata": {
                "stimulus_type": "visual" # Missing response_correctness
            }
        }
        
        # Ensure we capture the log
        with caplog.at_level(logging.WARNING):
            result = check_and_report_variables(dataset, ["stimulus_type", "response_correctness"])
        
        assert result is False
        assert "Skipping this dataset" in caplog.text
        assert "ds_skip_me" in caplog.text
        assert "response_correctness" in caplog.text

    def test_check_and_report_variables_accepts_valid(self, caplog):
        """
        Test that check_and_report_variables returns True for valid datasets.
        """
        dataset = {
            "id": "ds_valid",
            "metadata": {
                "stimulus_type": "tactile",
                "response_correctness": "binary"
            }
        }
        
        with caplog.at_level(logging.INFO):
            result = check_and_report_variables(dataset, ["stimulus_type", "response_correctness"])
        
        assert result is True
        assert "dataset_validated" in caplog.text or "valid" in caplog.text.lower()

    def test_no_crash_on_empty_metadata(self):
        """
        Verify the function does not crash when metadata key is missing entirely.
        """
        dataset = {
            "id": "ds_no_meta"
            # No 'metadata' key at all
        }
        # Should not raise an exception
        result = check_and_report_variables(dataset, ["stimulus_type"])
        assert result is False