"""
Unit tests for the data_loader module.
Tests verify that the loader correctly interfaces with streaming datasets
and yields items with expected keys.
"""

import pytest
from unittest.mock import patch, MagicMock

from code.utils.data_loader import (
    load_gsm8k_streaming,
    load_humaneval_streaming,
    load_dataset_streaming
)


class TestGSM8KStreaming:
    def test_load_gsm8k_yields_items_with_correct_keys(self):
        """Verify GSM8K loader yields items with 'question' and 'answer' keys."""
        mock_dataset = [
            {"question": "Test Q1", "answer": "Test A1"},
            {"question": "Test Q2", "answer": "Test A2"}
        ]

        with patch("code.utils.data_loader.load_dataset") as mock_load:
            mock_load.return_value = iter(mock_dataset)

            loader = load_gsm8k_streaming()
            items = list(loader)

            assert len(items) == 2
            assert "question" in items[0]
            assert "answer" in items[0]
            assert "question" in items[1]
            assert "answer" in items[1]

    def test_load_gsm8k_passes_correct_args(self):
        """Verify GSM8K loader passes correct arguments to load_dataset."""
        with patch("code.utils.data_loader.load_dataset") as mock_load:
            mock_load.return_value = iter([])

            list(load_gsm8k_streaming(split="test", config="custom", cache_dir="/tmp"))

            mock_load.assert_called_once_with(
                "gsm8k",
                "custom",
                split="test",
                streaming=True,
                cache_dir="/tmp"
            )


class TestHumanEvalStreaming:
    def test_load_humaneval_yields_items_with_correct_keys(self):
        """Verify HumanEval loader yields items with expected keys."""
        mock_dataset = [
            {
                "task_id": "HumanEval/0",
                "prompt": "def foo():",
                "code": "    return 1",
                "test": "assert foo() == 1",
                "entry_point": "foo"
            }
        ]

        with patch("code.utils.data_loader.load_dataset") as mock_load:
            mock_load.return_value = iter(mock_dataset)

            loader = load_humaneval_streaming()
            items = list(loader)

            assert len(items) == 1
            assert "task_id" in items[0]
            assert "prompt" in items[0]
            assert "code" in items[0]
            assert "test" in items[0]
            assert "entry_point" in items[0]

    def test_load_humaneval_passes_correct_args(self):
        """Verify HumanEval loader passes correct arguments to load_dataset."""
        with patch("code.utils.data_loader.load_dataset") as mock_load:
            mock_load.return_value = iter([])

            list(load_humaneval_streaming(split="train", cache_dir="/tmp"))

            mock_load.assert_called_once_with(
                "openai_humaneval",
                split="train",
                streaming=True,
                cache_dir="/tmp"
            )


class TestUnifiedLoader:
    def test_load_dataset_streaming_gsm8k(self):
        """Test unified loader for GSM8K."""
        mock_dataset = [{"question": "Q", "answer": "A"}]
        with patch("code.utils.data_loader.load_gsm8k_streaming") as mock_gsm8k:
            mock_gsm8k.return_value = iter(mock_dataset)

            result = list(load_dataset_streaming("gsm8k"))

            assert len(result) == 1
            mock_gsm8k.assert_called_once()

    def test_load_dataset_streaming_humaneval(self):
        """Test unified loader for HumanEval."""
        mock_dataset = [{"task_id": "0"}]
        with patch("code.utils.data_loader.load_humaneval_streaming") as mock_humaneval:
            mock_humaneval.return_value = iter(mock_dataset)

            result = list(load_dataset_streaming("humaneval"))

            assert len(result) == 1
            mock_humaneval.assert_called_once()

    def test_load_dataset_streaming_invalid_type(self):
        """Test unified loader raises ValueError for invalid dataset type."""
        with pytest.raises(ValueError, match="Unsupported dataset type"):
            list(load_dataset_streaming("invalid_type"))
