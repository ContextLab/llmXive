"""
Unit tests for resource enforcement logic.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

import datasets

from src.utils.resource import (
    enforce_resource_limits,
    estimate_dataset_size,
    load_resource_log,
    save_resource_log,
    ensure_results_dir,
    RAM_THRESHOLD_BYTES,
    MAX_SAMPLES,
    RESULTS_DIR,
    RESOURCE_LOG_PATH
)


class TestResourceEnforcement:
    """Tests for resource enforcement functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        # Temporarily override results directory for testing
        self.original_results_dir = RESULTS_DIR
        self.test_results_dir = tmp_path / "results"
        
        # Patch the global constants
        import src.utils.resource as resource_module
        resource_module.RESULTS_DIR = self.test_results_dir
        resource_module.RESOURCE_LOG_PATH = self.test_results_dir / "resource_log.json"
        
        yield
        
        # Restore original
        resource_module.RESULTS_DIR = self.original_results_dir
        resource_module.RESOURCE_LOG_PATH = self.original_results_dir / "resource_log.json"

    def test_ensure_results_dir_creates_directory(self, tmp_path):
        """Test that ensure_results_dir creates the directory if it doesn't exist."""
        test_dir = tmp_path / "test_results"
        import src.utils.resource as resource_module
        resource_module.RESULTS_DIR = test_dir
        
        assert not test_dir.exists()
        ensure_results_dir()
        assert test_dir.exists()

    def test_load_resource_log_returns_empty_when_no_file(self, tmp_path):
        """Test loading log when file doesn't exist."""
        import src.utils.resource as resource_module
        resource_module.RESULTS_DIR = tmp_path / "results"
        
        log = load_resource_log()
        assert "enforcement_actions" in log
        assert "dataset_info" in log
        assert log["enforcement_actions"] == []

    def test_load_resource_log_loads_existing_file(self, tmp_path):
        """Test loading an existing log file."""
        import src.utils.resource as resource_module
        resource_module.RESULTS_DIR = tmp_path / "results"
        ensure_results_dir()
        
        test_data = {"enforcement_actions": [{"test": "data"}], "dataset_info": {}}
        with open(RESOURCE_LOG_PATH, "w") as f:
            json.dump(test_data, f)
        
        log = load_resource_log()
        assert len(log["enforcement_actions"]) == 1
        assert log["enforcement_actions"][0]["test"] == "data"

    @patch('src.utils.resource.datasets.Dataset')
    def test_estimate_dataset_size_with_known_size(self, mock_dataset):
        """Test size estimation when dataset has known size."""
        mock_info = MagicMock()
        mock_info.dataset_size = 1024 * 1024 * 100  # 100 MB
        mock_dataset._info = mock_info
        
        size = estimate_dataset_size(mock_dataset)
        assert size == 1024 * 1024 * 100

    @patch('src.utils.resource.datasets.Dataset')
    def test_estimate_dataset_size_fallback_estimation(self, mock_dataset):
        """Test size estimation fallback when size info is unavailable."""
        mock_dataset._info = None
        mock_dataset.__len__ = MagicMock(return_value=1000)
        
        size = estimate_dataset_size(mock_dataset)
        # Should use fallback: 1000 rows * 1KB estimate
        assert size == 1000 * 1024

    @patch('src.utils.resource.datasets.Dataset')
    def test_enforce_resource_limits_no_sampling_needed(self, mock_dataset):
        """Test that no sampling occurs when dataset is under limit."""
        mock_info = MagicMock()
        mock_info.dataset_size = 1024 * 1024 * 100  # 100 MB (under 7GB)
        mock_dataset._info = mock_info
        mock_dataset.__len__ = MagicMock(return_value=1000)
        
        result = enforce_resource_limits(mock_dataset, "test_dataset")
        
        # Should return the same dataset
        assert result is mock_dataset
        
        # Check log was updated
        log = load_resource_log()
        assert len(log["enforcement_actions"]) == 1
        assert log["enforcement_actions"][0]["action_taken"] == "none"

    @patch('src.utils.resource.datasets.Dataset')
    def test_enforce_resource_limits_sampling_applied(self, mock_dataset):
        """Test that sampling is applied when dataset exceeds limit."""
        # Mock a dataset that exceeds 7GB
        mock_info = MagicMock()
        mock_info.dataset_size = 8 * 1024 * 1024 * 1024  # 8 GB (over limit)
        mock_dataset._info = mock_info
        mock_dataset.__len__ = MagicMock(return_value=10_000_000)
        
        # Mock the select method to return a new dataset
        mock_sampled = MagicMock()
        mock_sampled.__len__ = MagicMock(return_value=MAX_SAMPLES)
        mock_dataset.select.return_value = mock_sampled
        mock_dataset.shuffle.return_value = mock_dataset
        
        result = enforce_resource_limits(mock_dataset, "large_dataset")
        
        # Should have called select
        mock_dataset.shuffle.assert_called_once()
        mock_dataset.select.assert_called_once()
        
        # Check log
        log = load_resource_log()
        assert len(log["enforcement_actions"]) == 1
        assert log["enforcement_actions"][0]["action_taken"] == "sampling"
        assert log["enforcement_actions"][0]["samples_after"] == MAX_SAMPLES

    def test_save_resource_log_creates_file(self, tmp_path):
        """Test that save_resource_log creates the file."""
        import src.utils.resource as resource_module
        resource_module.RESULTS_DIR = tmp_path / "results"
        ensure_results_dir()
        
        test_data = {"enforcement_actions": [], "dataset_info": {}}
        save_resource_log(test_data)
        
        assert RESOURCE_LOG_PATH.exists()
        
        with open(RESOURCE_LOG_PATH, "r") as f:
            saved_data = json.load(f)
        
        assert saved_data == test_data
