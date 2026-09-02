"""
Unit tests for lexical feature extraction in code/features.py.
"""

import pytest
import numpy as np
from code.features import calculate_ttr, calculate_mtld, calculate_noun_verb_ratio, extract_lexical_features

class TestTTR:
    def test_ttr_all_unique(self):
        """TTR should be 1.0 when all tokens are unique."""
        tokens = ['apple', 'banana', 'cherry', 'date']
        assert calculate_ttr(tokens) == 1.0

    def test_ttr_all_same(self):
        """TTR should be 0.25 when only 1 unique token in 4 tokens."""
        tokens = ['apple', 'apple', 'apple', 'apple']
        assert calculate_ttr(tokens) == 0.25

    def test_ttr_empty(self):
        """TTR should be 0.0 for empty list."""
        assert calculate_ttr([]) == 0.0

    def test_ttr_mixed(self):
        """TTR for mixed unique and repeated tokens."""
        tokens = ['apple', 'banana', 'apple', 'cherry']
        # 3 unique / 4 total = 0.75
        assert calculate_ttr(tokens) == 0.75

class TestMTLD:
    def test_mtld_high_diversity(self):
        """MTLD should be high for text with high lexical diversity."""
        # Create a long text with many unique words
        tokens = [f'word{i}' for i in range(100)]
        mtld = calculate_mtld(tokens)
        assert mtld > 50  # High diversity should yield high MTLD

    def test_mtld_low_diversity(self):
        """MTLD should be lower for text with repeated words."""
        # Create text with many repetitions
        tokens = ['the', 'the', 'the', 'cat', 'the', 'cat'] * 20
        mtld = calculate_mtld(tokens)
        assert mtld < 50  # Low diversity should yield lower MTLD

    def test_mtld_short_text(self):
        """MTLD should be 0.0 for very short text."""
        tokens = ['hello', 'world']
        assert calculate_mtld(tokens) == 0.0

    def test_mtld_empty(self):
        """MTLD should be 0.0 for empty list."""
        assert calculate_mtld([]) == 0.0

class TestNounVerbRatio:
    def test_noun_verb_ratio_normal(self):
        """Test normal noun/verb ratio calculation."""
        # "The cat runs fast" -> cat(NN), runs(VBZ) -> 1/1 = 1.0
        tokens = ['The', 'cat', 'runs', 'fast']
        ratio = calculate_noun_verb_ratio(tokens)
        # The exact ratio depends on POS tagging, but it should be a number
        assert isinstance(ratio, float)
        assert not np.isinf(ratio)

    def test_noun_verb_ratio_no_verbs(self):
        """Ratio should be capped when there are no verbs."""
        # "The cat is happy" -> cat(NN), happy(JJ) -> 1/0 -> inf -> capped
        tokens = ['The', 'cat', 'is', 'happy']
        ratio = calculate_noun_verb_ratio(tokens)
        assert ratio <= 999.0  # Should be capped

    def test_noun_verb_ratio_empty(self):
        """Ratio should be 0.0 for empty list."""
        assert calculate_noun_verb_ratio([]) == 0.0

class TestExtractLexicalFeatures:
    def test_extract_features_basic(self):
        """Test basic feature extraction."""
        text = "The quick brown fox jumps over the lazy dog. This is a simple sentence."
        features = extract_lexical_features(text)
        
        assert 'ttr' in features
        assert 'mtld' in features
        assert 'noun_verb_ratio' in features
        assert features['ttr'] >= 0.0
        assert features['ttr'] <= 1.0
        assert features['mtld'] >= 0.0
        assert isinstance(features['noun_verb_ratio'], float)

    def test_extract_features_empty(self):
        """Test feature extraction on empty text."""
        features = extract_lexical_features("")
        assert features['ttr'] == 0.0
        assert features['mtld'] == 0.0
        assert features['noun_verb_ratio'] == 0.0

    def test_extract_features_short(self):
        """Test feature extraction on very short text."""
        features = extract_lexical_features("Hello world")
        assert features['ttr'] == 0.0
        assert features['mtld'] == 0.0
        assert features['noun_verb_ratio'] == 0.0

    def test_extract_features_special_chars(self):
        """Test feature extraction with special characters."""
        text = "Hello! How are you? I am fine, thanks."
        features = extract_lexical_features(text)
        assert features['ttr'] >= 0.0
        assert features['mtld'] >= 0.0
        assert not np.isinf(features['noun_verb_ratio'])