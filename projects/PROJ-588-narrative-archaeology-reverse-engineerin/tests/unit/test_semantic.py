"""
Unit tests for semantic feature extraction (BERT CPU inference).
Tests the `code/models/semantic.py` module functionality.
"""

import unittest
import numpy as np
import torch
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models.semantic import get_semantic_features
from transformers import BertTokenizer, BertModel


class TestSemanticFeatureExtraction(unittest.TestCase):
    """Tests for BERT-based semantic feature extraction."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_texts = [
            "The hero entered the castle.",
            "The villain plotted in the shadows.",
            "A sudden storm changed the course of events.",
            "The king made a decree.",
            "Peace was restored at the end."
        ]
        # Expected output shape for 5 texts with BERT-base (768 hidden size)
        self.expected_shape = (len(self.sample_texts), 768)

    @patch('models.semantic.BertModel')
    @patch('models.semantic.BertTokenizer')
    def test_get_semantic_features_shape(self, mock_tokenizer_class, mock_model_class):
        """Test that output shape matches expected BERT embedding dimensions."""
        # Mock tokenizer
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.return_value = {
            'input_ids': torch.randint(0, 1000, (len(self.sample_texts), 10)),
            'attention_mask': torch.ones((len(self.sample_texts), 10), dtype=torch.long)
        }
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer_instance

        # Mock model
        mock_model_instance = MagicMock()
        mock_output = MagicMock()
        # Pooler output is [batch_size, hidden_size]
        mock_output.pooler_output = torch.randn(len(self.sample_texts), 768)
        mock_model_instance.return_value = mock_output
        mock_model_class.from_pretrained.return_value = mock_model_instance

        # Run the function
        features = get_semantic_features(self.sample_texts)

        # Assertions
        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(features.shape, self.expected_shape)
        self.assertEqual(features.dtype, np.float32)

    @patch('models.semantic.BertModel')
    @patch('models.semantic.BertTokenizer')
    def test_get_semantic_features_cpu_only(self, mock_tokenizer_class, mock_model_class):
        """Test that model is forced to CPU as per project constraints."""
        # Mock tokenizer
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.return_value = {
            'input_ids': torch.randint(0, 1000, (len(self.sample_texts), 10)),
            'attention_mask': torch.ones((len(self.sample_texts), 10), dtype=torch.long)
        }
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer_instance

        # Mock model
        mock_model_instance = MagicMock()
        mock_output = MagicMock()
        mock_output.pooler_output = torch.randn(len(self.sample_texts), 768)
        mock_model_instance.return_value = mock_output
        mock_model_class.from_pretrained.return_value = mock_model_instance

        # Run the function
        _ = get_semantic_features(self.sample_texts)

        # Verify model was moved to CPU
        mock_model_instance.assert_called_once()
        # Check if .to('cpu') was called on the model
        # The function should call model.eval() and model.to('cpu')
        calls = [str(call) for call in mock_model_instance.mock_calls]
        # We expect 'to' to be called with 'cpu' or 'cpu' device
        to_calls = [call for call in calls if 'to' in call]
        self.assertTrue(len(to_calls) > 0, "Model should be moved to CPU")

    @patch('models.semantic.BertModel')
    @patch('models.semantic.BertTokenizer')
    def test_get_semantic_features_inference_mode(self, mock_tokenizer_class, mock_model_class):
        """Test that model is set to eval mode (no gradient tracking)."""
        # Mock tokenizer
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.return_value = {
            'input_ids': torch.randint(0, 1000, (len(self.sample_texts), 10)),
            'attention_mask': torch.ones((len(self.sample_texts), 10), dtype=torch.long)
        }
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer_instance

        # Mock model
        mock_model_instance = MagicMock()
        mock_output = MagicMock()
        mock_output.pooler_output = torch.randn(len(self.sample_texts), 768)
        mock_model_instance.return_value = mock_output
        mock_model_class.from_pretrained.return_value = mock_model_instance

        # Run the function
        _ = get_semantic_features(self.sample_texts)

        # Verify eval mode was called
        mock_model_instance.eval.assert_called_once()

    def test_get_semantic_features_empty_input(self):
        """Test behavior with empty text list."""
        # This should handle gracefully or raise a clear error
        # Depending on implementation, we expect either an empty array or a ValueError
        try:
            features = get_semantic_features([])
            # If it returns, it should be an empty array with correct feature dim
            self.assertIsInstance(features, np.ndarray)
            self.assertEqual(features.shape[1], 768)
        except (ValueError, IndexError) as e:
            # Also acceptable: explicit error for empty input
            self.assertIn("empty", str(e).lower())

    def test_get_semantic_features_single_text(self):
        """Test with a single text input."""
        single_text = ["Just one sentence."]

        # We need to mock for this specific test to avoid loading real model
        with patch('models.semantic.BertModel') as mock_model_class, \
             patch('models.semantic.BertTokenizer') as mock_tokenizer_class:

            # Mock tokenizer
            mock_tokenizer_instance = MagicMock()
            mock_tokenizer_instance.return_value = {
                'input_ids': torch.randint(0, 1000, (1, 5)),
                'attention_mask': torch.ones((1, 5), dtype=torch.long)
            }
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer_instance

            # Mock model
            mock_model_instance = MagicMock()
            mock_output = MagicMock()
            mock_output.pooler_output = torch.randn(1, 768)
            mock_model_instance.return_value = mock_output
            mock_model_class.from_pretrained.return_value = mock_model_instance

            features = get_semantic_features(single_text)

            self.assertEqual(features.shape, (1, 768))
            self.assertIsInstance(features, np.ndarray)


if __name__ == '__main__':
    unittest.main()