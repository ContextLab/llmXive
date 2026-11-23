"""
Unit tests for anxiety scoring logic in code/services/anxiety_scoring.py.
These tests use mocked model outputs to verify the scoring logic without
requiring a live model or external data.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.services.anxiety_scoring import (
    calculate_text_entropy,
    filter_text_quality,
    filter_non_english,
    load_anxiety_model,
    compute_anxiety_scores,
    ConfigurationError
)
from code.config import CONFIG


class TestAnxietyScoring(unittest.TestCase):
    """Unit tests for anxiety scoring functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_data = pd.DataFrame({
            'text': [
                "I am feeling very anxious about the future.",
                "This is a normal day.",
                "I feel scared and overwhelmed.",
                "Just another day at the office.",
                "I don't know what to do anymore.",
                None,
                "",
                "   ",
                "Short",
                "This is a longer text with more entropy and better quality for testing purposes."
            ],
            'id': list(range(10))
        })

        self.mock_config = {
            'filtering': {
                'min_text_length': 3,
                'entropy_threshold': 0.7,
                'langdetect_threshold': 0.8
            },
            'model_mapping': {
                'fear_to_anxiety': True
            }
        }

    def test_calculate_text_entropy_valid(self):
        """Test entropy calculation for valid text."""
        text = "This is a sample text with some entropy."
        entropy = calculate_text_entropy(text)
        self.assertIsInstance(entropy, float)
        self.assertGreaterEqual(entropy, 0)

    def test_calculate_text_entropy_empty(self):
        """Test entropy calculation for empty text."""
        entropy = calculate_text_entropy("")
        self.assertEqual(entropy, 0.0)

    def test_filter_text_quality(self):
        """Test text quality filtering."""
        # Filter with low threshold to keep most texts
        filtered_df = filter_text_quality(
            self.test_data.copy(),
            min_length=1,
            entropy_threshold=0.0
        )
        # Should keep non-empty, non-whitespace texts
        self.assertGreater(len(filtered_df), 0)
        # Check that empty strings and whitespace are removed
        self.assertNotIn("", filtered_df['text'].tolist())

    def test_filter_text_quality_removes_short(self):
        """Test that short texts are removed."""
        filtered_df = filter_text_quality(
            self.test_data.copy(),
            min_length=10,
            entropy_threshold=0.0
        )
        # "Short" (5 chars) should be removed
        self.assertNotIn("Short", filtered_df['text'].tolist())

    def test_filter_non_english(self):
        """Test non-English text filtering."""
        # Create test data with mixed languages
        mixed_data = pd.DataFrame({
            'text': [
                "This is English text.",
                "Ceci est du français.",
                "Esto es español.",
                "This is also English."
            ],
            'id': [1, 2, 3, 4]
        })

        # Mock langdetect to return English for first and last, non-English for others
        with patch('code.services.anxiety_scoring.detect') as mock_detect:
            mock_detect.side_effect = [
                ('en', 0.9),  # English
                ('fr', 0.9),  # French
                ('es', 0.9),  # Spanish
                ('en', 0.9)   # English
            ]

            filtered_df = filter_non_english(mixed_data, langdetect_threshold=0.8)

            # Should keep only English texts
            self.assertEqual(len(filtered_df), 2)
            self.assertIn("This is English text.", filtered_df['text'].tolist())
            self.assertIn("This is also English.", filtered_df['text'].tolist())

    def test_filter_non_english_low_confidence(self):
        """Test filtering when confidence is below threshold."""
        mixed_data = pd.DataFrame({
            'text': [
                "This is English text.",
                "Uncertain language."
            ],
            'id': [1, 2]
        })

        with patch('code.services.anxiety_scoring.detect') as mock_detect:
            mock_detect.side_effect = [
                ('en', 0.9),  # High confidence English
                ('en', 0.5)   # Low confidence English
            ]

            filtered_df = filter_non_english(mixed_data, langdetect_threshold=0.8)

            # Should only keep the high confidence one
            self.assertEqual(len(filtered_df), 1)
            self.assertIn("This is English text.", filtered_df['text'].tolist())

    @patch('code.services.anxiety_scoring.AutoTokenizer')
    @patch('code.services.anxiety_scoring.AutoModelForSequenceClassification')
    def test_load_anxiety_model(self, mock_model, mock_tokenizer):
        """Test model loading."""
        mock_tokenizer_instance = MagicMock()
        mock_model_instance = MagicMock()
        mock_tokenizer.return_value = mock_tokenizer_instance
        mock_model.return_value = mock_model_instance

        tokenizer, model = load_anxiety_model("cardiffnlp/twitter-roberta-base-emotion")

        self.assertIsNotNone(tokenizer)
        self.assertIsNotNone(model)
        mock_tokenizer.assert_called_once()
        mock_model.assert_called_once()

    @patch('code.services.anxiety_scoring.AutoTokenizer')
    @patch('code.services.anxiety_scoring.AutoModelForSequenceClassification')
    @patch('code.services.anxiety_scoring.torch.no_grad')
    def test_compute_anxiety_scores(self, mock_no_grad, mock_model, mock_tokenizer):
        """Test anxiety score computation with mocked model output."""
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_model_instance = MagicMock()
        mock_tokenizer.return_value = mock_tokenizer_instance
        mock_model.return_value = mock_model_instance

        # Mock tokenizer output
        mock_tokenizer_instance.return_value = {
            'input_ids': torch.tensor([[1, 2, 3]]),
            'attention_mask': torch.tensor([[1, 1, 1]])
        }

        # Mock model output - simulate a distribution where 'fear' is high
        # Label mapping: 0: sadness, 1: joy, 2: love, 3: anger, 4: fear, 5: surprise
        mock_logits = torch.tensor([[0.1, 0.2, 0.1, 0.1, 0.4, 0.1]])
        mock_model_instance.return_value.logits = mock_logits

        # Mock no_grad context manager
        mock_no_grad.return_value.__enter__ = MagicMock()
        mock_no_grad.return_value.__exit__ = MagicMock()

        # Create test data
        test_df = pd.DataFrame({
            'text': ["I am scared and anxious."],
            'id': [1]
        })

        # Mock config
        with patch('code.services.anxiety_scoring.load_config_params', return_value=self.mock_config):
            result_df = compute_anxiety_scores(test_df)

            self.assertIn('anxiety_score', result_df.columns)
            self.assertIn('confidence_score', result_df.columns)
            self.assertEqual(len(result_df), 1)
            # Anxiety score should be derived from fear label (index 4)
            # In this mock, fear is 0.4, which should be mapped to anxiety
            self.assertGreater(result_df['anxiety_score'].iloc[0], 0)

    @patch('code.services.anxiety_scoring.load_config_params')
    @patch('code.services.anxiety_scoring.filter_non_english')
    @patch('code.services.anxiety_scoring.filter_text_quality')
    @patch('code.services.anxiety_scoring.compute_anxiety_scores')
    def test_run_full_scoring_pipeline(self, mock_compute, mock_filter_quality, mock_filter_lang, mock_load_config):
        """Test the full scoring pipeline with mocked dependencies."""
        # Setup mocks
        mock_load_config.return_value = self.mock_config
        mock_filter_lang.return_value = self.test_data.copy()
        mock_filter_quality.return_value = self.test_data.dropna().copy()

        # Mock compute_anxiety_scores to return a DataFrame with required columns
        mock_result = self.test_data.dropna().copy()
        mock_result['anxiety_score'] = 0.5
        mock_result['confidence_score'] = 0.9
        mock_compute.return_value = mock_result

        input_path = Path("data/processed/preprocessed_text.csv")
        output_path = Path("data/processed/scoring_results.csv")

        # Mock file existence
        with patch('pathlib.Path.exists', return_value=True):
            result = run_full_scoring_pipeline(input_path, output_path, mock_load_config.return_value)

            self.assertIsInstance(result, pd.DataFrame)
            self.assertIn('anxiety_score', result.columns)
            self.assertIn('confidence_score', result.columns)
            mock_compute.assert_called_once()

    def test_compute_anxiety_scores_with_mapping(self):
        """Test that fear is correctly mapped to anxiety when mapping is enabled."""
        test_df = pd.DataFrame({
            'text': ["I am very afraid."],
            'id': [1]
        })

        # Mock the model and tokenizer
        with patch('code.services.anxiety_scoring.AutoTokenizer') as mock_tokenizer, \
             patch('code.services.anxiety_scoring.AutoModelForSequenceClassification') as mock_model, \
             patch('code.services.anxiety_scoring.torch.no_grad') as mock_no_grad:

            # Setup mocks
            mock_tokenizer_instance = MagicMock()
            mock_model_instance = MagicMock()
            mock_tokenizer.return_value = mock_tokenizer_instance
            mock_model.return_value = mock_model_instance

            # Mock tokenizer output
            mock_tokenizer_instance.return_value = {
                'input_ids': torch.tensor([[1, 2, 3]]),
                'attention_mask': torch.tensor([[1, 1, 1]])
            }

            # Mock model output with high 'fear' probability
            # Assuming label 4 is 'fear' in the model
            mock_logits = torch.tensor([[0.1, 0.1, 0.1, 0.1, 0.6, 0.0]])
            mock_model_instance.return_value.logits = mock_logits

            # Mock no_grad
            mock_no_grad.return_value.__enter__ = MagicMock()
            mock_no_grad.return_value.__exit__ = MagicMock()

            # Mock config with fear_to_anxiety = True
            config_with_mapping = self.mock_config.copy()
            config_with_mapping['model_mapping'] = {'fear_to_anxiety': True}

            with patch('code.services.anxiety_scoring.load_config_params', return_value=config_with_mapping):
                result = compute_anxiety_scores(test_df)

                self.assertIn('anxiety_score', result.columns)
                # With high fear (0.6) and mapping enabled, anxiety should be high
                self.assertGreater(result['anxiety_score'].iloc[0], 0.5)

    def test_compute_anxiety_scores_without_mapping(self):
        """Test that fear is NOT mapped to anxiety when mapping is disabled."""
        test_df = pd.DataFrame({
            'text': ["I am very afraid."],
            'id': [1]
        })

        with patch('code.services.anxiety_scoring.AutoTokenizer') as mock_tokenizer, \
             patch('code.services.anxiety_scoring.AutoModelForSequenceClassification') as mock_model, \
             patch('code.services.anxiety_scoring.torch.no_grad') as mock_no_grad:

            mock_tokenizer_instance = MagicMock()
            mock_model_instance = MagicMock()
            mock_tokenizer.return_value = mock_tokenizer_instance
            mock_model.return_value = mock_model_instance

            mock_tokenizer_instance.return_value = {
                'input_ids': torch.tensor([[1, 2, 3]]),
                'attention_mask': torch.tensor([[1, 1, 1]])
            }

            # Mock model output with high 'fear' probability
            mock_logits = torch.tensor([[0.1, 0.1, 0.1, 0.1, 0.6, 0.0]])
            mock_model_instance.return_value.logits = mock_logits

            mock_no_grad.return_value.__enter__ = MagicMock()
            mock_no_grad.return_value.__exit__ = MagicMock()

            # Mock config with fear_to_anxiety = False
            config_without_mapping = self.mock_config.copy()
            config_without_mapping['model_mapping'] = {'fear_to_anxiety': False}

            with patch('code.services.anxiety_scoring.load_config_params', return_value=config_without_mapping):
                result = compute_anxiety_scores(test_df)

                self.assertIn('anxiety_score', result.columns)
                # Without mapping, fear should not contribute to anxiety
                # The anxiety score should be low (assuming other emotions are low)
                self.assertLess(result['anxiety_score'].iloc[0], 0.5)


if __name__ == '__main__':
    unittest.main()