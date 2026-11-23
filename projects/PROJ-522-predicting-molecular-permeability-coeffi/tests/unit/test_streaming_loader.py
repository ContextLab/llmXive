"""
Unit tests for the streaming loader.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.streaming_loader import (
    check_memory_and_fail_if_exceeded,
    load_streaming_dataset,
    MEMORY_LIMIT_MB
)
from utils.memory_monitor import get_memory_usage_mb


class TestMemoryLimit:
    def test_memory_limit_enforcement(self):
        """
        Test that MemoryError is raised when memory limit is exceeded.
        """
        # Mock memory usage to be above limit
        with patch('utils.streaming_loader.get_memory_usage_mb', return_value=MEMORY_LIMIT_MB + 100):
            with patch('utils.streaming_logger.logger') as mock_logger:
                with pytest.raises(MemoryError):
                    check_memory_and_fail_if_exceeded()
                mock_logger.error.assert_called_once()

    def test_memory_limit_ok(self):
        """
        Test that no error is raised when memory is within limits.
        """
        with patch('utils.streaming_loader.get_memory_usage_mb', return_value=1000):
            # Should not raise
            check_memory_and_fail_if_exceeded()


class TestStreamingLoader:
    @patch('utils.streaming_loader.load_dataset')
    def test_streaming_load_success(self, mock_load_dataset):
        """
        Test successful streaming load.
        """
        # Mock dataset iterator
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"smiles": "CCO", "target": 0.5},
            {"smiles": "CCCO", "target": 0.4}
        ]))
        mock_load_dataset.return_value = mock_dataset

        df = load_streaming_dataset(sources=["nist"], batch_size=2)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "smiles" in df.columns
        assert "target" in df.columns

    @patch('utils.streaming_loader.load_dataset')
    def test_streaming_load_memory_failure(self, mock_load_dataset):
        """
        Test that MemoryError is raised if memory limit is hit during load.
        """
        # Mock dataset iterator that yields many items
        def mock_iter():
            for i in range(10000):
                yield {"smiles": f"SMILES_{i}", "target": i}
        
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=mock_iter())
        mock_load_dataset.return_value = mock_dataset

        # Mock memory check to fail after a few items
        call_count = 0
        def mock_check_memory():
            nonlocal call_count
            call_count += 1
            if call_count > 5:
                raise MemoryError("Simulated memory limit")

        with patch('utils.streaming_loader.check_memory_and_fail_if_exceeded', side_effect=mock_check_memory):
            with pytest.raises(MemoryError):
                load_streaming_dataset(sources=["nist"], batch_size=1)

    @patch('utils.streaming_loader.load_dataset')
    def test_streaming_load_source_error(self, mock_load_dataset):
        """
        Test that RuntimeError is raised if a source fails to load.
        """
        mock_load_dataset.side_effect = Exception("Dataset not found")

        with pytest.raises(RuntimeError):
            load_streaming_dataset(sources=["nist"], batch_size=1)

    def test_unknown_source(self):
        """
        Test that ValueError is raised for unknown source.
        """
        with pytest.raises(ValueError):
            load_streaming_dataset(sources=["unknown_source"], batch_size=1)
