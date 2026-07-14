"""
Unit tests for validation logic, specifically sample size validation (T015).
"""
import logging
from unittest.mock import patch, MagicMock
import pytest

from main import validate_sample_size

# Setup logging for tests
logging.basicConfig(level=logging.WARNING)

class TestSampleSizeValidation:
    """Tests for the validate_sample_size function."""

    def test_valid_sample_size(self):
        """Test that datasets with N >= 30 pass validation."""
        dataset_info = {"name": "test_dataset", "n_samples": 50}
        assert validate_sample_size(dataset_info) is True

    def test_boundary_sample_size(self):
        """Test that datasets with exactly N=30 pass validation."""
        dataset_info = {"name": "test_dataset", "n_samples": 30}
        assert validate_sample_size(dataset_info) is True

    def test_insufficient_sample_size(self, caplog):
        """Test that datasets with N < 30 fail validation and log warning."""
        dataset_info = {"name": "small_dataset", "n_samples": 25}
        
        with caplog.at_level(logging.WARNING):
            result = validate_sample_size(dataset_info)
        
        assert result is False
        assert "insufficient sample size" in caplog.text
        assert "small_dataset" in caplog.text
        assert "N=25" in caplog.text

    def test_missing_samples_key(self):
        """Test that datasets missing 'n_samples' key fail validation."""
        dataset_info = {"name": "incomplete_dataset"}
        assert validate_sample_size(dataset_info) is False

    def test_zero_samples(self, caplog):
        """Test that datasets with N=0 fail validation."""
        dataset_info = {"name": "empty_dataset", "n_samples": 0}
        
        with caplog.at_level(logging.WARNING):
            result = validate_sample_size(dataset_info)
        
        assert result is False
        assert "N=0" in caplog.text

    def test_large_sample_size(self):
        """Test that very large datasets pass validation."""
        dataset_info = {"name": "big_dataset", "n_samples": 10000}
        assert validate_sample_size(dataset_info) is True