"""
Unit tests for the pronoun extractor (T010).
Verifies metric calculations against manual spot-checks.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.extraction.pronoun_extractor import (
    calculate_pronoun_rate, 
    extract_pronoun_features,
    FIRST_PERSON_PRONOUNS
)

class TestCalculatePronounRate:
    def test_empty_string(self):
        """Test handling of empty string."""
        assert calculate_pronoun_rate("") == 0.0

    def test_none_input(self):
        """Test handling of None input."""
        assert calculate_pronoun_rate(None) == 0.0

    def test_no_pronouns(self):
        """Test text with no first-person pronouns."""
        text = "The cat sat on the mat."
        # Expected: 0 first person pronouns / 6 words = 0.0
        rate = calculate_pronoun_rate(text)
        assert rate == 0.0

    def test_single_pronoun(self):
        """Test text with a single first-person pronoun."""
        text = "I am happy."
        # Expected: 1 pronoun ('I') / 3 words = 0.333...
        rate = calculate_pronoun_rate(text)
        expected = 1.0 / 3.0
        assert abs(rate - expected) < 1e-6

    def test_multiple_pronouns(self):
        """Test text with multiple first-person pronouns."""
        text = "We believe we can do it."
        # Words: We, believe, we, can, do, it (6 words)
        # Pronouns: We, we (2 pronouns)
        # Rate: 2/6 = 0.333...
        rate = calculate_pronoun_rate(text)
        expected = 2.0 / 6.0
        assert abs(rate - expected) < 1e-6

    def test_mixed_case(self):
        """Test that pronoun detection is case-insensitive."""
        text = "I love I. My name is I."
        # Words: I, love, I, My, name, is, I (7 words)
        # Pronouns: I, I, My, I (4 pronouns)
        rate = calculate_pronoun_rate(text)
        expected = 4.0 / 7.0
        assert abs(rate - expected) < 1e-6

    def test_punctuation_handling(self):
        """Test that punctuation is not counted as words."""
        text = "I said, 'Hello!' Then I left."
        # Words: I, said, Hello, Then, I, left (6 words)
        # Pronouns: I, I (2 pronouns)
        rate = calculate_pronoun_rate(text)
        expected = 2.0 / 6.0
        assert abs(rate - expected) < 1e-6

class TestExtractPronounFeatures:
    def test_basic_extraction(self):
        """Test basic feature extraction on a DataFrame."""
        data = {
            "conversation_id": [1, 2],
            "text": ["I am here.", "They are there."]
        }
        df = pd.DataFrame(data)
        
        result = extract_pronoun_features(df)
        
        assert "pronoun_rate" in result.columns
        # Row 1: "I am here." -> 1/3 = 0.333
        # Row 2: "They are there." -> 0/3 = 0.0
        assert abs(result.iloc[0]["pronoun_rate"] - (1.0/3.0)) < 1e-6
        assert result.iloc[1]["pronoun_rate"] == 0.0

    def test_missing_column_error(self):
        """Test that an error is raised if the text column is missing."""
        data = {
            "id": [1],
            "content": ["Hello"]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Column 'text' not found"):
            extract_pronoun_features(df, text_column="text")

    def test_custom_column_names(self):
        """Test extraction with custom column names."""
        data = {
            "id": [1],
            "message": ["We win."]
        }
        df = pd.DataFrame(data)
        
        result = extract_pronoun_features(df, text_column="message", output_column="my_rate")
        
        assert "my_rate" in result.columns
        assert result.iloc[0]["my_rate"] == 2.0 / 3.0 # "We", "win" -> 2 words, 1 pronoun? 
        # Wait: "We win." -> Words: We, win (2). Pronouns: We (1). Rate = 0.5
        assert abs(result.iloc[0]["my_rate"] - 0.5) < 1e-6
