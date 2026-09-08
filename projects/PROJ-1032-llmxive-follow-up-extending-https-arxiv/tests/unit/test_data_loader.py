"""
Unit tests for data_loader.py.

Tests cover:
- Successful streaming of GSM8K data.
- Validation of sample structure.
- Raising DATA_INTEGRITY_ERROR on invalid data.
- Handling of max_samples limit.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from datasets.exceptions import DatasetNotFoundError, DatasetGenerationError

from llmxive.data_loader import load_gsm8k_stream, validate_sample
from llmxive.exceptions import DATA_INTEGRITY_ERROR


class TestDataLoader:
    """Test suite for the GSM8K data loader."""

    def test_validate_sample_valid(self):
        """Test that a valid GSM8K sample passes validation."""
        valid_sample = {
            "question": "If I have 5 apples and buy 3 more, how many do I have?",
            "answer": "I have 5 apples, buy 3 more. 5 + 3 = 8. #### 8"
        }
        assert validate_sample(valid_sample) is True

    def test_validate_sample_missing_question(self):
        """Test that a sample missing 'question' raises DATA_INTEGRITY_ERROR."""
        invalid_sample = {
            "answer": "#### 10"
        }
        with pytest.raises(DATA_INTEGRITY_ERROR):
            validate_sample(invalid_sample)

    def test_validate_sample_missing_answer(self):
        """Test that a sample missing 'answer' raises DATA_INTEGRITY_ERROR."""
        invalid_sample = {
            "question": "What is 2+2?"
        }
        with pytest.raises(DATA_INTEGRITY_ERROR):
            validate_sample(invalid_sample)

    def test_validate_sample_invalid_answer_format(self):
        """Test that a sample with invalid answer format raises DATA_INTEGRITY_ERROR."""
        invalid_sample = {
            "question": "What is 2+2?",
            "answer": "It is 4." # Missing ####
        }
        with pytest.raises(DATA_INTEGRITY_ERROR):
            validate_sample(invalid_sample)

    def test_load_gsm8k_stream_success(self):
        """Test successful streaming of data."""
        mock_sample = {
            "question": "Test question",
            "answer": "Test answer #### 42"
        }
        
        with patch('llmxive.data_loader.load_dataset') as mock_load:
            mock_ds = MagicMock()
            mock_ds.__iter__ = MagicMock(return_value=iter([mock_sample, mock_sample]))
            mock_load.return_value = mock_ds
            
            loader = load_gsm8k_stream(split="train", streaming=True, max_samples=2)
            results = list(loader)
            
            assert len(results) == 2
            assert results[0]["question"] == "Test question"

    def test_load_gsm8k_stream_dataset_not_found(self):
        """Test that DATA_INTEGRITY_ERROR is raised if dataset is not found."""
        with patch('llmxive.data_loader.load_dataset') as mock_load:
            mock_load.side_effect = DatasetNotFoundError("Dataset not found")
            
            with pytest.raises(DATA_INTEGRITY_ERROR):
                list(load_gsm8k_stream(split="train"))

    def test_load_gsm8k_stream_generation_error(self):
        """Test that DATA_INTEGRITY_ERROR is raised if dataset generation fails."""
        with patch('llmxive.data_loader.load_dataset') as mock_load:
            mock_load.side_effect = DatasetGenerationError("Generation failed")
            
            with pytest.raises(DATA_INTEGRITY_ERROR):
                list(load_gsm8k_stream(split="train"))

    def test_load_gsm8k_stream_truncation(self):
        """Test that DATA_INTEGRITY_ERROR is raised if max_samples is not met."""
        mock_sample = {
            "question": "Test question",
            "answer": "Test answer #### 42"
        }
        
        with patch('llmxive.data_loader.load_dataset') as mock_load:
            mock_ds = MagicMock()
            # Only yield 1 sample when 2 were requested
            mock_ds.__iter__ = MagicMock(return_value=iter([mock_sample]))
            mock_load.return_value = mock_ds
            
            with pytest.raises(DATA_INTEGRITY_ERROR) as exc_info:
                list(load_gsm8k_stream(split="train", max_samples=2))
            
            assert "truncated" in str(exc_info.value).lower()

    def test_load_gsm8k_stream_invalid_sample_raises(self):
        """Test that an invalid sample in the stream raises DATA_INTEGRITY_ERROR."""
        valid_sample = {
            "question": "Good question",
            "answer": "Good answer #### 10"
        }
        invalid_sample = {
            "question": "Bad question",
            "answer": "Bad answer without hash"
        }
        
        with patch('llmxive.data_loader.load_dataset') as mock_load:
            mock_ds = MagicMock()
            mock_ds.__iter__ = MagicMock(return_value=iter([valid_sample, invalid_sample]))
            mock_load.return_value = mock_ds
            
            with pytest.raises(DATA_INTEGRITY_ERROR):
                list(load_gsm8k_stream(split="train"))