"""
Unit tests for TextModel (src/models/text_model.py).
Tests distilled LLM wrapper for text modality.
"""
import os
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.models.text_model import TextModel


class TestTextModel:
    """Test suite for TextModel class."""

    def test_init_default(self):
        """Test default initialization."""
        model = TextModel()
        assert model.model is None
        assert model.tokenizer is None
        assert model.model_id is None
        assert model.logger is not None

    def test_load_model_mock(self):
        """Test load_model with mocked LLM."""
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()

        with patch('src.models.text_model.AutoModelForSequenceClassification') as mock_auto:
            with patch('src.models.text_model.AutoTokenizer') as mock_tok:
                mock_auto.from_pretrained.return_value = mock_model
                mock_tok.from_pretrained.return_value = mock_tokenizer
                
                model = TextModel()
                model.load_model("distilbert-base")
                
                assert model.model is not None
                assert model.tokenizer is not None
                assert model.model_id == "distilbert-base"
                
                mock_auto.from_pretrained.assert_called_once()
                mock_tok.from_pretrained.assert_called_once()

    def test_predict_single_text(self):
        """Test prediction with single text input."""
        model = TextModel()
        model.model = MagicMock()
        model.tokenizer = MagicMock()
        
        # Mock tokenizer output
        mock_encoded = {
            'input_ids': np.array([[101, 2000, 102]]),
            'attention_mask': np.array([[1, 1, 1]])
        }
        model.tokenizer.return_value = mock_encoded
        
        # Mock model output
        mock_output = MagicMock()
        mock_output.logits = np.array([[0.1, 0.9]])
        model.model.return_value = mock_output

        text = "This is a test sentence."
        result = model.predict(text)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (1, 1)
        assert result[0, 0] == 1  # Class with higher probability

    def test_predict_batch_texts(self):
        """Test prediction with multiple text inputs."""
        model = TextModel()
        model.model = MagicMock()
        model.tokenizer = MagicMock()
        
        mock_encoded = {
            'input_ids': np.array([
                [101, 2000, 102],
                [101, 3000, 102]
            ]),
            'attention_mask': np.array([
                [1, 1, 1],
                [1, 1, 1]
            ])
        }
        model.tokenizer.return_value = mock_encoded
        
        mock_output = MagicMock()
        mock_output.logits = np.array([
            [0.1, 0.9],
            [0.8, 0.2]
        ])
        model.model.return_value = mock_output

        texts = ["First text.", "Second text."]
        result = model.predict(texts)
        
        assert result.shape == (2, 1)

    def test_get_embedding(self):
        """Test embedding generation."""
        model = TextModel()
        model.model = MagicMock()
        model.tokenizer = MagicMock()
        
        mock_encoded = {
            'input_ids': np.array([[101, 2000, 102]]),
            'attention_mask': np.array([[1, 1, 1]])
        }
        model.tokenizer.return_value = mock_encoded
        
        mock_output = MagicMock()
        mock_output.last_hidden_state = np.random.randn(1, 3, 768).astype(np.float32)
        model.model.return_value = mock_output

        text = "Test text for embedding."
        embedding = model.get_embedding(text)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (1, 768)  # Pooling over sequence

    def test_predict_empty_text(self):
        """Test prediction with empty string."""
        model = TextModel()
        model.model = MagicMock()
        model.tokenizer = MagicMock()
        
        model.tokenizer.return_value = {
            'input_ids': np.array([[101, 102]]),
            'attention_mask': np.array([[1, 1]])
        }
        
        mock_output = MagicMock()
        mock_output.logits = np.array([[0.5, 0.5]])
        model.model.return_value = mock_output

        result = model.predict("")
        
        assert result.shape == (1, 1)

    def test_predict_invalid_type(self):
        """Test prediction with non-string input."""
        model = TextModel()
        
        with pytest.raises(TypeError, match="Input must be string or list of strings"):
            model.predict(123)

    def test_cpu_only_mode(self):
        """Test that model forces CPU execution."""
        mock_model = MagicMock()
        mock_tokenizer = MagicMock()

        with patch('src.models.text_model.AutoModelForSequenceClassification') as mock_auto:
            with patch('src.models.text_model.AutoTokenizer') as mock_tok:
                mock_auto.from_pretrained.return_value = mock_model
                mock_tok.from_pretrained.return_value = mock_tokenizer
                
                model = TextModel()
                model.load_model("cpu-model")
                
                mock_model.to.assert_called_with("cpu")


class TestTextModelIntegration:
    """Integration tests for TextModel with actual numpy operations."""

    def test_classification_flow(self):
        """Test complete classification flow."""
        model = TextModel()
        model.model = MagicMock()
        model.tokenizer = MagicMock()
        
        texts = [
            "Positive review text here.",
            "Negative review text here.",
            "Another positive review."
        ]
        
        # Mock encoding
        max_len = 10
        batch_size = len(texts)
        mock_encoded = {
            'input_ids': np.random.randint(0, 1000, (batch_size, max_len)),
            'attention_mask': np.ones((batch_size, max_len), dtype=int)
        }
        model.tokenizer.return_value = mock_encoded
        
        # Mock logits
        num_classes = 2
        mock_output = MagicMock()
        mock_output.logits = np.random.randn(batch_size, num_classes).astype(np.float32)
        model.model.return_value = mock_output

        predictions = model.predict(texts)
        
        assert predictions.shape == (batch_size, 1)
        assert np.all(predictions >= 0)
        assert np.all(predictions < num_classes)

    def test_embedding_pooling(self):
        """Test that embedding uses mean pooling correctly."""
        model = TextModel()
        model.model = MagicMock()
        model.tokenizer = MagicMock()
        
        text = "Test sentence for pooling."
        
        mock_encoded = {
            'input_ids': np.array([[101, 2000, 3000, 102]]),
            'attention_mask': np.array([[1, 1, 1, 1]])
        }
        model.tokenizer.return_value = mock_encoded
        
        hidden_size = 512
        seq_len = 4
        mock_output = MagicMock()
        mock_output.last_hidden_state = np.random.randn(1, seq_len, hidden_size).astype(np.float32)
        model.model.return_value = mock_output

        embedding = model.get_embedding(text)
        
        assert embedding.shape == (1, hidden_size)

    def test_long_text_handling(self):
        """Test with text longer than model max length."""
        model = TextModel()
        model.model = MagicMock()
        model.tokenizer = MagicMock()
        
        long_text = "Word " * 1000  # Very long text
        
        # Mock encoding (tokenizer should truncate)
        max_len = 512
        mock_encoded = {
            'input_ids': np.random.randint(0, 1000, (1, max_len)),
            'attention_mask': np.ones((1, max_len), dtype=int)
        }
        model.tokenizer.return_value = mock_encoded
        
        mock_output = MagicMock()
        mock_output.logits = np.array([[0.5, 0.5]])
        model.model.return_value = mock_output

        result = model.predict(long_text)
        
        assert result.shape == (1, 1)