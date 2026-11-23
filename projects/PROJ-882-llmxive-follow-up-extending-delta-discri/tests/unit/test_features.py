import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.extract_features import (
    load_nlp_model,
    load_embedding_model,
    extract_ngram_features,
    extract_pos_features,
    compute_semantic_similarity,
    extract_token_features,
    load_gsm8k_verified,
    save_features,
    validate_features
)
from sentence_transformers import SentenceTransformer
import spacy
from sklearn.feature_extraction.text import CountVectorizer

class TestFeatureExtraction:
    
    @pytest.fixture(scope="class")
    def nlp_model(self):
        return load_nlp_model()
    
    @pytest.fixture(scope="class")
    def embedding_model(self):
        return load_embedding_model()
    
    @pytest.fixture(scope="class")
    def vectorizer(self):
        # Create a simple vectorizer for testing
        texts = ["This is a test", "Another test example", "Testing n-grams"]
        vectorizer = CountVectorizer(ngram_range=(1, 2))
        vectorizer.fit(texts)
        return vectorizer
    
    @pytest.fixture(scope="class")
    def sample_reference_texts(self):
        return ["This is a test sentence", "Another example sentence"]
    
    def test_load_nlp_model(self, nlp_model):
        """Test that spaCy model loads successfully."""
        assert nlp_model is not None
        assert isinstance(nlp_model, spacy.Language)
    
    def test_load_embedding_model(self, embedding_model):
        """Test that sentence-transformers model loads successfully."""
        assert embedding_model is not None
        assert isinstance(embedding_model, SentenceTransformer)
    
    def test_extract_ngram_features(self, vectorizer):
        """Test n-gram feature extraction."""
        text = "This is a test"
        features = extract_ngram_features(text, vectorizer)
        
        assert isinstance(features, np.ndarray)
        assert len(features) > 0
        assert np.all(features >= 0)
    
    def test_extract_pos_features(self, nlp_model):
        """Test POS feature extraction."""
        text = "The quick brown fox jumps over the lazy dog"
        features = extract_pos_features(text, nlp_model)
        
        assert isinstance(features, np.ndarray)
        assert len(features) == 12  # Number of POS_FEATURES
        assert np.all(features >= 0)
        assert np.all(features <= 1)  # Normalized values
    
    def test_compute_semantic_similarity(self, embedding_model, sample_reference_texts):
        """Test semantic similarity computation."""
        text = "This is a test"
        similarity = compute_semantic_similarity(text, sample_reference_texts, embedding_model)
        
        assert isinstance(similarity, float)
        assert -1.0 <= similarity <= 1.0
    
    def test_extract_token_features(self, nlp_model, embedding_model, vectorizer, sample_reference_texts):
        """Test token feature extraction."""
        row = {
            'id': 'test_123',
            'question': 'What is 2+2?',
            'answer': 'The answer is 4'
        }
        
        features = extract_token_features(row, nlp_model, embedding_model, vectorizer, sample_reference_texts)
        
        assert isinstance(features, list)
        assert len(features) > 0
        
        for feature in features:
            assert 'example_id' in feature
            assert 'token_id' in feature
            assert 'token_text' in feature
            assert 'feature_vector' in feature
            assert isinstance(feature['feature_vector'], list)
            assert len(feature['feature_vector']) > 0
    
    def test_validate_features(self):
        """Test feature validation."""
        # Create a valid DataFrame
        valid_df = pd.DataFrame({
            'example_id': ['test_1', 'test_2'],
            'token_id': [0, 1],
            'token_text': ['test', 'data'],
            'feature_vector': [[1.0, 2.0], [3.0, 4.0]]
        })
        
        assert validate_features(valid_df) is True
        
        # Test with missing column
        invalid_df = valid_df.drop(columns=['token_text'])
        assert validate_features(invalid_df) is False
        
        # Test with NaN feature vectors
        nan_df = valid_df.copy()
        nan_df.loc[0, 'feature_vector'] = None
        assert validate_features(nan_df) is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
