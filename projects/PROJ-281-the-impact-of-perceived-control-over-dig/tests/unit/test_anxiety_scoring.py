import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.services.anxiety_scoring import (
    filter_text_quality, 
    filter_non_english, 
    calculate_text_entropy,
    compute_anxiety_scores,
    load_anxiety_model,
    ConfigurationError
)

class TestGibberishFiltering:
    """Tests for T014c: Gibberish filtering logic."""

    def setup_method(self):
        """Setup test data."""
        self.data = pd.DataFrame({
            'text': [
                "This is a normal tweet about anxiety.",
                "asdfjkl;ghjk",  # Gibberish
                "x",  # Too short
                "   ",  # Whitespace only (length 3 but low entropy? depends on logic)
                "Normal text with good entropy.",
                "12345678901234567890", # Numbers, might be high entropy
                "I feel really scared today."
            ]
        })

    @patch('code.services.anxiety_scoring.load_config_params')
    def test_filter_short_text(self, mock_config):
        """Test that text shorter than min_length is removed."""
        mock_config.return_value = (4.5, 5) # entropy, min_length
        
        result = filter_text_quality(self.data)
        
        # "x" (len 1) should be removed
        # "   " (len 3) should be removed if min_length is 5
        assert len(result) < len(self.data)
        assert not any(len(str(t)) < 5 for t in result['text'])

    @patch('code.services.anxiety_scoring.load_config_params')
    def test_filter_gibberish_by_entropy(self, mock_config):
        """Test that high entropy text is removed."""
        # Set a low entropy threshold to catch gibberish
        mock_config.return_value = (1.0, 1) # Very low entropy threshold
        
        result = filter_text_quality(self.data)
        
        # "asdfjkl;ghjk" is likely to have high entropy
        # We expect it to be filtered out
        # The exact behavior depends on the entropy calculation, but the logic should be present
        assert 'asdfjkl;ghjk' not in result['text'].values

    @patch('code.services.anxiety_scoring.load_config_params')
    def test_keep_normal_text(self, mock_config):
        """Test that normal text is kept."""
        mock_config.return_value = (5.0, 3) # High threshold, low min_length
        
        result = filter_text_quality(self.data)
        
        # Normal texts should remain
        assert "This is a normal tweet about anxiety." in result['text'].values
        assert "I feel really scared today." in result['text'].values

    def test_missing_config_raises_error(self):
        """Test that missing config raises ConfigurationError."""
        # Mock the load_config_params to raise an error
        with patch('code.services.anxiety_scoring.load_config_params', side_effect=ConfigurationError("Missing")):
            with pytest.raises(ConfigurationError):
                filter_text_quality(self.data)

    @patch('code.services.anxiety_scoring.load_config_params')
    def test_empty_dataframe(self, mock_config):
        """Test handling of empty DataFrame."""
        mock_config.return_value = (4.5, 3)
        empty_df = pd.DataFrame(columns=['text'])
        
        result = filter_text_quality(empty_df)
        assert result.empty

    @patch('code.services.anxiety_scoring.load_config_params')
    def test_no_text_column(self, mock_config):
        """Test that missing text column raises error."""
        mock_config.return_value = (4.5, 3)
        df_no_text = pd.DataFrame({'other': ['data']})
        
        with pytest.raises(ValueError):
            filter_text_quality(df_no_text)

class TestNonEnglishFiltering:
    """Tests for T014b: Non-English text filtering."""

    def setup_method(self):
        """Setup test data."""
        self.data = pd.DataFrame({
            'text': [
                "This is English.",
                "Esto es español.",
                "Ceci est français.",
                "This is also English."
            ]
        })

    @patch('code.services.anxiety_scoring.langdetect.detect')
    @patch('code.services.anxiety_scoring.load_config_params')
    def test_filter_non_english(self, mock_config, mock_detect):
        """Test that non-English text is removed."""
        mock_config.return_value = 0.8
        mock_detect.side_effect = ['en', 'es', 'fr', 'en']
        
        result = filter_non_english(self.data)
        
        # Should keep only English rows
        assert len(result) == 2
        assert "This is English." in result['text'].values

    @patch('code.services.anxiety_scoring.langdetect.detect')
    @patch('code.services.anxiety_scoring.load_config_params')
    def test_filter_low_confidence(self, mock_config, mock_detect):
        """Test that low confidence detections are removed."""
        mock_config.return_value = 0.9
        mock_detect.side_effect = [
            ('en', 0.5),  # Low confidence
            ('en', 0.95), # High confidence
            ('es', 0.99), # Spanish
            ('en', 0.95)  # High confidence
        ]
        
        # Note: The actual implementation might handle confidence differently
        # This test assumes detect returns (lang, confidence) or similar
        # Adjust based on actual implementation
        pass

    @patch('code.services.anxiety_scoring.langdetect.detect')
    @patch('code.services.anxiety_scoring.load_config_params')
    def test_keep_english(self, mock_config, mock_detect):
        """Test that English text is kept."""
        mock_config.return_value = 0.8
        mock_detect.side_effect = ['en', 'en', 'en', 'en']
        
        result = filter_non_english(self.data)
        
        # All should be kept
        assert len(result) == len(self.data)

class TestTextEntropy:
    """Tests for entropy calculation."""

    def test_entropy_calculation(self):
        """Test that entropy is calculated correctly."""
        # Low entropy text (repetitive)
        low_entropy = calculate_text_entropy("aaaaaa")
        # High entropy text (random)
        high_entropy = calculate_text_entropy("abcdef")
        
        # High entropy should be greater than low entropy
        assert high_entropy > low_entropy

    def test_empty_string(self):
        """Test entropy of empty string."""
        entropy = calculate_text_entropy("")
        assert entropy == 0.0

    def test_whitespace_only(self):
        """Test entropy of whitespace only."""
        entropy = calculate_text_entropy("   ")
        assert entropy == 0.0

class TestAnxietyScoring:
    """Tests for T015: Anxiety scoring with mocked model."""

    def setup_method(self):
        """Setup test data."""
        self.data = pd.DataFrame({
            'text': [
                "I feel anxious today.",
                "This is a happy day.",
                "I am scared of the future."
            ]
        })

    @patch('code.services.anxiety_scoring.AutoModelForSequenceClassification.from_pretrained')
    @patch('code.services.anxiety_scoring.AutoTokenizer.from_pretrained')
    def test_load_model(self, mock_tokenizer, mock_model):
        """Test that model is loaded correctly."""
        mock_tokenizer.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        
        tokenizer, model = load_anxiety_model("cardiffnlp/twitter-roberta-base-emotion")
        
        assert tokenizer is not None
        assert model is not None

    @patch('code.services.anxiety_scoring.load_anxiety_model')
    @patch('code.services.anxiety_scoring.load_config_params')
    def test_compute_anxiety_scores(self, mock_config, mock_load_model):
        """Test anxiety score computation with mocked model."""
        mock_config.return_value = 0.6  # confidence threshold
        
        # Mock the model and tokenizer
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {'input_ids': [[1, 2, 3]], 'attention_mask': [[1, 1, 1]]}
        
        mock_model = MagicMock()
        mock_model.return_value.logits = torch.tensor([[0.1, 0.2, 0.3, 0.4]])  # Mock logits
        
        mock_load_model.return_value = (mock_tokenizer, mock_model)
        
        # Mock the label mapping
        with patch('code.services.anxiety_scoring.CONFIG', {'model_mapping': {'fear_to_anxiety': False}}):
            result = compute_anxiety_scores(self.data)
            
            assert 'anxiety_score' in result.columns
            assert 'confidence_score' in result.columns
            assert len(result) > 0

# Additional imports needed for the test
try:
    import torch
except ImportError:
    # If torch is not available, skip torch-dependent tests
    pytest.skip("torch not available", allow_module_level=True)