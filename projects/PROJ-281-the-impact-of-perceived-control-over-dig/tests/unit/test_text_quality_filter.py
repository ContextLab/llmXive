import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.services.anxiety_scoring import (
    calculate_text_entropy,
    filter_text_quality,
    ConfigurationError
)

class TestTextEntropy:
    def test_entropy_empty_string(self):
        assert calculate_text_entropy("") == 0.0
    
    def test_entropy_single_char(self):
        assert calculate_text_entropy("a") == 0.0
    
    def test_entropy_repeated_chars(self):
        # "aaaa" has very low entropy
        entropy = calculate_text_entropy("aaaa")
        assert entropy == 0.0
    
    def test_entropy_random_chars(self):
        # "abcd" has higher entropy
        entropy = calculate_text_entropy("abcd")
        assert entropy > 0.5  # Should be significantly higher than repeated chars

class TestFilterTextQuality:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'text': [
                "This is a normal tweet",
                "a" * 100,  # Very low entropy
                "x!@#$%^&*()_+",  # High entropy gibberish
                "Short",  # Short but valid
                "",  # Empty
                "Normal text here with some content",
                "ababababab"  # Low entropy pattern
            ]
        })
    
    @pytest.fixture
    def valid_config(self):
        return {
            'filtering': {
                'min_text_length': 3,
                'entropy_threshold': 0.7
            }
        }
    
    def test_filter_by_length(self, sample_df, valid_config):
        # Should remove empty string and "Short" (length < 3)
        filtered = filter_text_quality(sample_df, valid_config)
        assert len(filtered) < len(sample_df)
        assert all(len(str(t)) >= 3 for t in filtered['text'])
    
    def test_filter_by_entropy(self, sample_df, valid_config):
        # Should remove high entropy gibberish
        filtered = filter_text_quality(sample_df, valid_config)
        # Check that high entropy text is removed
        for text in filtered['text']:
            entropy = calculate_text_entropy(str(text))
            assert entropy <= valid_config['filtering']['entropy_threshold']
    
    def test_missing_config_key_length(self, sample_df):
        config = {'filtering': {'entropy_threshold': 0.7}}
        with pytest.raises(ConfigurationError) as exc_info:
            filter_text_quality(sample_df, config)
        assert "min_text_length" in str(exc_info.value)
    
    def test_missing_config_key_entropy(self, sample_df):
        config = {'filtering': {'min_text_length': 3}}
        with pytest.raises(ConfigurationError) as exc_info:
            filter_text_quality(sample_df, config)
        assert "entropy_threshold" in str(exc_info.value)
    
    def test_missing_text_column(self, valid_config):
        df = pd.DataFrame({'other_col': ['text']})
        with pytest.raises(ValueError):
            filter_text_quality(df, valid_config)
    
    def test_combined_filtering(self, sample_df, valid_config):
        filtered = filter_text_quality(sample_df, valid_config)
        # All remaining rows should pass both filters
        for _, row in filtered.iterrows():
            text = str(row['text'])
            assert len(text) >= valid_config['filtering']['min_text_length']
            entropy = calculate_text_entropy(text)
            assert entropy <= valid_config['filtering']['entropy_threshold']
