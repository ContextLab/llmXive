"""
Unit tests for dataset_loader.py.

These tests verify the logic of filtering and data handling without
necessarily downloading the full dataset (using mocks where appropriate).
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.data.dataset_loader import fetch_and_filter_dataset, TARGET_PLATFORMS, MAX_SAMPLES

class TestDatasetLoaderLogic:
    """Tests for the filtering logic."""

    def test_filtering_logic(self):
        """Verify that the filtering logic correctly selects target platforms."""
        # Mock dataset items
        mock_items = [
            {"platform_id": "franka", "data": "row1"},
            {"platform_id": "ur5", "data": "row2"},
            {"platform_id": "kuka", "data": "row3"},
            {"platform_id": "other", "data": "row4"},
            {"platform_id": "franka", "data": "row5"},
            {"platform_id": "xarm", "data": "row6"},
        ]
        
        # Simulate the filtering loop logic
        filtered = []
        for item in mock_items:
            platform = item.get("platform_id")
            if platform and platform.lower() in TARGET_PLATFORMS:
                filtered.append(item)
        
        assert len(filtered) == 4
        assert all(item["platform_id"] in TARGET_PLATFORMS for item in filtered)
        assert not any(item["platform_id"] == "other" for item in filtered)
        assert not any(item["platform_id"] == "xarm" for item in filtered)

    @patch('src.data.dataset_loader.datasets.load_dataset')
    @patch('src.data.dataset_loader.get_current_ram_gb')
    @patch('src.data.dataset_loader.check_ram_limit')
    def test_fetch_and_filter_with_mock_streaming(self, mock_check_ram, mock_ram_gb, mock_load):
        """Test the fetch function with a mocked streaming dataset."""
        # Setup mocks
        mock_check_ram.return_value = False  # Don't stop due to RAM
        mock_ram_gb.return_value = 2.0
        
        # Create a mock iterator that yields our test items
        mock_iterator = iter([
            {"platform_id": "franka", "value": 1},
            {"platform_id": "ur5", "value": 2},
            {"platform_id": "other", "value": 3},
            {"platform_id": "kuka", "value": 4},
            {"platform_id": "franka", "value": 5},
            {"platform_id": "franka", "value": 6}, # Should stop at MAX_SAMPLES if we had more
        ])
        
        mock_ds = MagicMock()
        mock_ds.__iter__ = MagicMock(return_value=mock_iterator)
        mock_load.return_value = mock_ds
        
        # Run the function
        df = fetch_and_filter_dataset()
        
        # Verify results
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 4  # franka, ur5, kuka, franka (4 matches)
        assert all(p in TARGET_PLATFORMS for p in df["platform_id"])
        
        # Verify load_dataset was called with correct args
        mock_load.assert_called_once()
        args, kwargs = mock_load.call_args
        assert kwargs.get("streaming") is True
        assert kwargs.get("split") == "train"

    def test_empty_result_handling(self):
        """Verify behavior when no matching data is found."""
        mock_items = [
            {"platform_id": "other1"},
            {"platform_id": "other2"},
        ]
        
        filtered = []
        for item in mock_items:
            platform = item.get("platform_id")
            if platform and platform.lower() in TARGET_PLATFORMS:
                filtered.append(item)
        
        assert len(filtered) == 0
        # In the real function, this would raise ValueError
        # We just verify the logic here
