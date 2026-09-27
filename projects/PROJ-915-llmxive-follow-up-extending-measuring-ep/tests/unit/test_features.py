"""
tests/unit/test_features.py

Unit tests for linguistic feature extraction logic in code/features.py
"""
import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from features import (
    count_sentences,
    count_modal_verbs,
    count_imperative_sentences,
    count_declarative_sentences,
    count_citations,
    extract_features,
    flag_undefined_imperative_ratio
)

class TestSentenceCounting:
    def test_empty_text(self):
        assert count_sentences("") == 0
        assert count_sentences(None) == 0

    def test_single_sentence(self):
        assert count_sentences("This is a sentence.") == 1

    def test_multiple_sentences(self):
        text = "First sentence. Second sentence? Third sentence!"
        assert count_sentences(text) == 3

    def test_mixed_punctuation(self):
        text = "Hello. How are you? Fine! Great."
        assert count_sentences(text) == 4

class TestModalVerbCounting:
    def test_empty_text(self):
        assert count_modal_verbs("") == 0

    def test_no_modals(self):
        assert count_modal_verbs("The cat sat on the mat.") == 0

    def test_single_modal(self):
        assert count_modal_verbs("You can do it.") == 1

    def test_multiple_modals(self):
        text = "You can and should do this. It might work."
        assert count_modal_verbs(text) == 3

    def test_modal_variants(self):
        text = "I can't, couldn't, and shouldn't."
        assert count_modal_verbs(text) == 3

class TestImperativeSentenceCounting:
    def test_empty_text(self):
        assert count_imperative_sentences("") == 0

    def test_no_imperatives(self):
        text = "The dog barked. The cat slept."
        assert count_imperative_sentences(text) == 0

    def test_single_imperative(self):
        text = "Take this medicine."
        assert count_imperative_sentences(text) == 1

    def test_multiple_imperatives(self):
        text = "Take this. Give that. Do it."
        assert count_imperative_sentences(text) == 3

    def test_please_prefix(self):
        text = "Please help me. Kindly answer."
        assert count_imperative_sentences(text) == 2

class TestCitationCounting:
    def test_empty_text(self):
        assert count_citations("") == 0

    def test_no_citations(self):
        assert count_citations("This is a test.") == 0

    def test_bracket_citations(self):
        text = "According to studies [1], [2], and [3-5]."
        assert count_citations(text) == 3

    def test_parenthetical_citations(self):
        text = "As shown (1) and (2,3)."
        assert count_citations(text) == 2

    def test_author_year(self):
        text = "Smith (2020) reported this."
        assert count_citations(text) == 1

class TestFeatureExtraction:
    def test_empty_prompt(self):
        features = extract_features("")
        assert features['modal_freq'] == 0.0
        assert features['imperative_ratio'] == 0.0
        assert features['citation_density'] == 0.0
        assert features['is_ratio_undefined'] is True

    def test_normal_prompt(self):
        text = "You should take this medicine [1]. It can help."
        features = extract_features(text)
        
        assert features['modal_freq'] > 0.0
        assert features['citation_density'] > 0.0
        assert 'is_ratio_undefined' in features
        assert 'ratio_safe_value' in features

    def test_undefined_ratio_handling(self):
        # Create a text with only imperative sentences (no declarative)
        text = "Take this. Do that. Give here."
        features = extract_features(text)
        
        # Should have imperative_count > 0 and declarative_count = 0
        assert features['is_ratio_undefined'] is True
        assert features['ratio_safe_value'] == 0.0
        assert features['imperative_ratio'] == 0.0

class TestFlagUndefinedRatio:
    def test_flag_missing_fields(self):
        features_list = [
            {'modal_freq': 0.5, 'imperative_ratio': 0.0, 'citation_density': 0.1}
        ]
        
        result = flag_undefined_imperative_ratio(features_list)
        
        assert 'is_ratio_undefined' in result[0]
        assert 'ratio_safe_value' in result[0]

    def test_preserve_existing_values(self):
        features_list = [
            {
                'modal_freq': 0.5,
                'imperative_ratio': 1.0,
                'citation_density': 0.1,
                'is_ratio_undefined': False,
                'ratio_safe_value': 1.0
            }
        ]
        
        result = flag_undefined_imperative_ratio(features_list)
        
        assert result[0]['is_ratio_undefined'] is False
        assert result[0]['ratio_safe_value'] == 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])