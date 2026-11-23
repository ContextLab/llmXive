import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from code.features import extract_ttr, extract_mtld, extract_noun_verb_ratio, extract_syntactic_features, calculate_participant_similarity

class TestTTR:
    def test_ttr_basic(self):
        texts = ["the cat the dog"]
        ttrs = extract_ttr(texts)
        # Tokens: ["the", "cat", "the", "dog"] -> Unique: {"the", "cat", "dog"} -> 3/4 = 0.75
        assert abs(ttrs[0] - 0.75) < 1e-5

    def test_ttr_empty(self):
        texts = ["", "   ", None]
        ttrs = extract_ttr(texts)
        assert all(t == 0.0 for t in ttrs)

class TestMTLD:
    def test_mtld_basic(self):
        # A text with high variety should have high MTLD
        # Using a simple string for testing
        text = "one two three four five six seven eight nine ten " * 10
        mtlds = extract_mtld([text], segment_length=5, threshold=0.72)
        assert mtlds[0] > 0.0

    def test_mtld_empty(self):
        texts = ["", "   "]
        mtlds = extract_mtld(texts)
        assert all(m == 0.0 for m in mtlds)

class TestNounVerbRatio:
    @patch('spacy.load')
    def test_noun_verb_ratio(self, mock_spacy_load):
        # Mock the nlp object
        mock_doc = Mock()
        mock_token1 = Mock()
        mock_token1.pos_ = "NOUN"
        mock_token2 = Mock()
        mock_token2.pos_ = "VERB"
        mock_token3 = Mock()
        mock_token3.pos_ = "NOUN"
        mock_doc.__iter__ = Mock(return_value=iter([mock_token1, mock_token2, mock_token3]))
        mock_doc.sents = []
        
        mock_nlp = Mock(return_value=mock_doc)
        mock_spacy_load.return_value = mock_nlp
        
        texts = ["The dog runs."]
        ratios = extract_noun_verb_ratio(texts, mock_nlp)
        # 2 Nouns, 1 Verb -> Ratio 2.0
        assert ratios[0] == 2.0

class TestSyntacticFeatures:
    @patch('spacy.load')
    def test_syntactic_features(self, mock_spacy_load):
        mock_sent = Mock()
        mock_sent.text = "This is a test sentence."
        mock_doc = Mock()
        mock_doc.sents = [mock_sent]
        mock_doc.__iter__ = Mock(return_value=iter([]))
        
        mock_nlp = Mock(return_value=mock_doc)
        mock_spacy_load.return_value = mock_nlp
        
        texts = ["This is a test sentence."]
        mean_len, t_units = extract_syntactic_features(texts, mock_nlp)
        assert t_units[0] == 1
        assert mean_len[0] > 0.0

class TestCosineSimilarity:
    def test_calculate_participant_similarity(self):
        # Create two identical vectors
        embeddings = np.array([[1.0, 0.0], [1.0, 0.0]])
        sim = calculate_participant_similarity(embeddings)
        assert abs(sim - 1.0) < 1e-5

    def test_calculate_participant_similarity_orthogonal(self):
        # Create two orthogonal vectors
        embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])
        sim = calculate_participant_similarity(embeddings)
        assert abs(sim - 0.0) < 1e-5

    def test_calculate_participant_similarity_single(self):
        # Only one vector
        embeddings = np.array([[1.0, 0.0]])
        sim = calculate_participant_similarity(embeddings)
        assert sim == 0.0

    def test_calculate_participant_similarity_empty(self):
        # No vectors
        embeddings = np.array([]).reshape(0, 2)
        sim = calculate_participant_similarity(embeddings)
        assert sim == 0.0
