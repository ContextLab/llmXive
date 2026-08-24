"""
Unit tests for T040: DeepFashion2 streaming loader.

Tests that loader.py correctly streams the dataset without OOM.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock, Iterator
import json

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.data.loader import (
    load_config,
    load_deepfashion2_streaming,
    process_batch,
    iterate_dataset,
    get_dataset_info
)


class TestConfigLoading:
    """Tests for configuration loading."""

    def test_load_config_returns_dict(self):
        """Test that config loading returns a dictionary."""
        with patch('src.data.loader.Path.exists', return_value=True):
            with patch('builtins.open', MagicMock()):
                with patch('yaml.safe_load', return_value={'seed': 42}):
                    config = load_config(Path('dummy_path.yaml'))
                    
                    assert isinstance(config, dict)
                    assert config['seed'] == 42

    def test_load_config_handles_missing_file(self):
        """Test behavior when config file is missing."""
        with patch('src.data.loader.Path.exists', return_value=False):
            config = load_config(Path('nonexistent.yaml'))
            
            assert isinstance(config, dict)
            assert 'seed' in config


class TestStreamingLoader:
    """Tests for streaming dataset loading."""

    @patch('src.data.loader.load_dataset')
    def test_load_deepfashion2_streaming_returns_generator(self, mock_load_dataset):
        """Test that streaming loader returns a generator."""
        # Mock the dataset to return an iterable
        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([{'id': '1'}, {'id': '2'}]))
        mock_load_dataset.return_value = mock_dataset
        
        result = load_deepfashion2_streaming()
        
        # Should return a generator/iterator
        assert hasattr(result, '__iter__')
        assert hasattr(result, '__next__')

    @patch('src.data.loader.load_dataset')
    def test_load_deepfashion2_streaming_with_streaming_true(self, mock_load_dataset):
        """Test that streaming=True is passed to load_dataset."""
        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset
        
        list(load_deepfashion2_streaming())
        
        # Verify streaming=True was passed
        call_kwargs = mock_load_dataset.call_args[1]
        assert call_kwargs.get('streaming') is True

    @patch('src.data.loader.load_dataset')
    def test_load_deepfashion2_streaming_returns_correct_dataset(self, mock_load_dataset):
        """Test that correct dataset name is used."""
        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset
        
        list(load_deepfashion2_streaming())
        
        # Verify DeepFashion2 dataset name
        call_args = mock_load_dataset.call_args[0]
        assert 'deepfashion2' in call_args[0].lower() or 'deepfashion' in call_args[0].lower()


class TestBatchProcessing:
    """Tests for batch processing logic."""

    def test_process_batch_returns_list(self):
        """Test that batch processing returns a list."""
        batch = [{'id': '1'}, {'id': '2'}, {'id': '3'}]
        
        result = process_batch(batch)
        
        assert isinstance(result, list)
        assert len(result) == 3

    def test_process_batch_preserves_data(self):
        """Test that batch processing preserves original data."""
        original_batch = [
            {'id': '1', 'value': 10},
            {'id': '2', 'value': 20}
        ]
        
        result = process_batch(original_batch)
        
        assert result[0]['id'] == '1'
        assert result[0]['value'] == 10
        assert result[1]['id'] == '2'
        assert result[1]['value'] == 20

    def test_process_batch_with_empty_batch(self):
        """Test processing an empty batch."""
        result = process_batch([])
        
        assert result == []


class TestDatasetIteration:
    """Tests for dataset iteration logic."""

    @patch('src.data.loader.load_deepfashion2_streaming')
    def test_iterate_dataset_yields_records(self, mock_streaming):
        """Test that iteration yields records correctly."""
        # Mock streaming to return a simple iterator
        mock_streaming.return_value = iter([
            {'id': '1', 'data': 'a'},
            {'id': '2', 'data': 'b'},
            {'id': '3', 'data': 'c'}
        ])
        
        records = list(iterate_dataset(limit=3))
        
        assert len(records) == 3
        assert records[0]['id'] == '1'
        assert records[1]['id'] == '2'
        assert records[2]['id'] == '3'

    @patch('src.data.loader.load_deepfashion2_streaming')
    def test_iterate_dataset_respects_limit(self, mock_streaming):
        """Test that iteration respects the limit parameter."""
        mock_streaming.return_value = iter([
            {'id': str(i)} for i in range(100)
        ])
        
        records = list(iterate_dataset(limit=10))
        
        assert len(records) == 10

    @patch('src.data.loader.load_deepfashion2_streaming')
    def test_iterate_dataset_handles_none_limit(self, mock_streaming):
        """Test iteration with no limit (should yield all)."""
        # Create a finite iterator for testing
        mock_streaming.return_value = iter([{'id': '1'}, {'id': '2'}])
        
        records = list(iterate_dataset(limit=None))
        
        assert len(records) == 2


class TestDatasetInfo:
    """Tests for dataset info retrieval."""

    @patch('src.data.loader.load_deepfashion2_streaming')
    def test_get_dataset_info_returns_info_dict(self, mock_streaming):
        """Test that dataset info is returned correctly."""
        # Mock a small dataset for counting
        mock_streaming.return_value = iter([
            {'id': '1'}, {'id': '2'}, {'id': '3'}
        ])
        
        info = get_dataset_info(limit=10)
        
        assert isinstance(info, dict)
        assert 'total_records' in info
        assert 'total_records' == 3

    @patch('src.data.loader.load_deepfashion2_streaming')
    def test_get_dataset_info_handles_empty_dataset(self, mock_streaming):
        """Test info retrieval for empty dataset."""
        mock_streaming.return_value = iter([])
        
        info = get_dataset_info(limit=10)
        
        assert info['total_records'] == 0