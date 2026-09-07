import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.services.anxiety_scoring import filter_text_quality, ConfigurationError

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
