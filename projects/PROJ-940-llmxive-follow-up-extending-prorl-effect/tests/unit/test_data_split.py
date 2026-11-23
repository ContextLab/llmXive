"""
Unit tests for time-based data splitting functionality.
"""

import pytest
import json
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from src.data_loader import (
    split_dataset_by_time,
    _parse_timestamp,
    load_and_split_dataset
)
from src.exceptions import DataSplitError, DataFetchError


class TestParseTimestamp:
    """Tests for timestamp parsing utility."""

    def test_parse_epoch_seconds(self):
        """Test parsing Unix epoch seconds."""
        ts = 1609459200  # 2021-01-01 00:00:00 UTC
        assert _parse_timestamp(ts, 'test') == float(ts)

    def test_parse_epoch_milliseconds(self):
        """Test parsing Unix epoch milliseconds."""
        ts = 1609459200000  # 2021-01-01 00:00:00 UTC in ms
        assert _parse_timestamp(ts, 'test') == ts / 1000.0

    def test_parse_iso_format(self):
        """Test parsing ISO format strings."""
        ts_str = '2021-01-01T00:00:00'
        expected = datetime(2021, 1, 1).timestamp()
        assert abs(_parse_timestamp(ts_str, 'test') - expected) < 1

    def test_parse_date_format(self):
        """Test parsing date-only strings."""
        ts_str = '2021-01-01'
        expected = datetime(2021, 1, 1).timestamp()
        assert abs(_parse_timestamp(ts_str, 'test') - expected) < 1

    def test_parse_none(self):
        """Test handling of None values."""
        assert _parse_timestamp(None, 'test') is None

    def test_parse_invalid_string(self):
        """Test handling of invalid date strings."""
        assert _parse_timestamp('invalid', 'test') is None


class TestTimeBasedSplit:
    """Tests for time-based dataset splitting."""

    @pytest.fixture
    def mock_dataset(self):
        """Create a mock dataset with time-ordered interactions."""
        # Create interactions for multiple users with different timestamps
        interactions = [
            {'user_id': 'user1', 'item_id': 'item1', 'timestamp': '2021-01-01'},
            {'user_id': 'user1', 'item_id': 'item2', 'timestamp': '2021-01-02'},
            {'user_id': 'user1', 'item_id': 'item3', 'timestamp': '2021-01-03'},
            {'user_id': 'user1', 'item_id': 'item4', 'timestamp': '2021-01-04'},
            {'user_id': 'user2', 'item_id': 'item1', 'timestamp': '2021-01-01'},
            {'user_id': 'user2', 'item_id': 'item2', 'timestamp': '2021-01-02'},
            {'user_id': 'user2', 'item_id': 'item3', 'timestamp': '2021-01-03'},
            {'user_id': 'user3', 'item_id': 'item1', 'timestamp': '2021-01-01'},
            {'user_id': 'user3', 'item_id': 'item2', 'timestamp': '2021-01-02'},
        ]

        # Convert to list of dicts with original interaction
        result = []
        for i, item in enumerate(interactions):
            result.append({
                'user_id': item['user_id'],
                'item_id': item['item_id'],
                'timestamp': item['timestamp'],
                'original_interaction': item
            })
        return result

    def test_split_preserves_time_order(self, mock_dataset, tmp_path):
        """Test that test set contains more recent interactions than train set."""
        # Create a mock dataset object
        mock_ds = Mock()
        mock_ds.__iter__ = Mock(return_value=iter(mock_dataset))

        train_path, test_path = split_dataset_by_time(
            dataset=mock_ds,
            dataset_name='test',
            timestamp_column='timestamp',
            user_column='user_id',
            item_column='item_id',
            test_ratio=0.3,
            output_dir=str(tmp_path),
            streaming=False
        )

        # Load the results
        with open(train_path, 'r') as f:
            train_data = json.load(f)
        with open(test_path, 'r') as f:
            test_data = json.load(f)

        # Verify split occurred
        assert len(train_data) > 0
        assert len(test_data) > 0

        # For user1: 4 items, 30% test = ~1 item in test (most recent)
        user1_train = [d for d in train_data if d['user_id'] == 'user1']
        user1_test = [d for d in test_data if d['user_id'] == 'user1']

        # Most recent item (item4) should be in test
        user1_test_items = [d['item_id'] for d in user1_test]
        assert 'item4' in user1_test_items

        # Older items should be in train
        user1_train_items = [d['item_id'] for d in user1_train]
        assert 'item1' in user1_train_items

    def test_invalid_test_ratio(self, mock_dataset, tmp_path):
        """Test that invalid test_ratio raises error."""
        mock_ds = Mock()
        mock_ds.__iter__ = Mock(return_value=iter(mock_dataset))

        with pytest.raises(DataSplitError):
            split_dataset_by_time(
                dataset=mock_ds,
                dataset_name='test',
                timestamp_column='timestamp',
                user_column='user_id',
                item_column='item_id',
                test_ratio=1.5,
                output_dir=str(tmp_path),
                streaming=False
            )

    def test_missing_timestamp_column(self, mock_dataset, tmp_path):
        """Test that missing timestamp column raises error."""
        mock_ds = Mock()
        mock_ds.__iter__ = Mock(return_value=iter(mock_dataset))

        with pytest.raises(DataSplitError):
            split_dataset_by_time(
                dataset=mock_ds,
                dataset_name='test',
                timestamp_column='nonexistent',
                user_column='user_id',
                item_column='item_id',
                test_ratio=0.2,
                output_dir=str(tmp_path),
                streaming=False
            )

    def test_single_interaction_user(self, tmp_path):
        """Test handling of users with only one interaction."""
        interactions = [
            {'user_id': 'user1', 'item_id': 'item1', 'timestamp': '2021-01-01'},
            {'user_id': 'user2', 'item_id': 'item1', 'timestamp': '2021-01-01'},
            {'user_id': 'user2', 'item_id': 'item2', 'timestamp': '2021-01-02'},
        ]

        mock_ds = Mock()
        mock_ds.__iter__ = Mock(return_value=iter(interactions))

        train_path, test_path = split_dataset_by_time(
            dataset=mock_ds,
            dataset_name='test',
            timestamp_column='timestamp',
            user_column='user_id',
            item_column='item_id',
            test_ratio=0.5,
            output_dir=str(tmp_path),
            streaming=False
        )

        with open(train_path, 'r') as f:
            train_data = json.load(f)
        with open(test_path, 'r') as f:
            test_data = json.load(f)

        # User1 should be entirely in train (only 1 interaction)
        user1_train = [d for d in train_data if d['user_id'] == 'user1']
        user1_test = [d for d in test_data if d['user_id'] == 'user1']

        assert len(user1_train) == 1
        assert len(user1_test) == 0

        # User2 should have split
        user2_train = [d for d in train_data if d['user_id'] == 'user2']
        user2_test = [d for d in test_data if d['user_id'] == 'user2']

        assert len(user2_train) == 1
        assert len(user2_test) == 1