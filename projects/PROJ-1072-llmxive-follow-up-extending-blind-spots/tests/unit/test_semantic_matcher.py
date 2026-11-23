import pytest
from unittest.mock import Mock, patch
import numpy as np

from code.utils.semantic_matcher import encode_texts, cosine_similarity, is_paraphrase
from code.utils.logging_config import get_logger

logger = get_logger(__name__)

class TestSemanticMatcher:
    """Unit tests for semantic matching functionality."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock SentenceTransformer model."""
        model = Mock()
        # Mock encode to return dummy embeddings
        def mock_encode(texts, **kwargs):
            # Return shape (len(texts), 384) with random but deterministic values
            np.random.seed(42)
            return np.random.rand(len(texts), 384).astype(np.float32)
        model.encode = mock_encode
        return model

    def test_encode_texts(self, mock_model):
        """Test that encode_texts returns embeddings for input texts."""
        texts = ["Hello world", "How are you?"]
        embeddings = encode_texts(texts, mock_model)
        
        assert embeddings.shape == (2, 384)
        assert embeddings.dtype == np.float32

    def test_cosine_similarity(self, mock_model):
        """Test cosine similarity calculation."""
        texts = ["Same meaning", "Identical meaning"]
        embeddings = encode_texts(texts, mock_model)
        
        sim = cosine_similarity(embeddings[0].unsqueeze(0), embeddings[1].unsqueeze(0))
        
        assert sim.shape == (1, 1)
        # Similarity should be between -1 and 1
        assert -1.0 <= sim[0][0] <= 1.0

    def test_is_paraphrase_above_threshold(self, mock_model):
        """Test that is_paraphrase returns True when similarity >= threshold."""
        # Mock the similarity to be high
        with patch('code.utils.semantic_matcher.cosine_similarity', return_value=np.array([[0.85]])):
            result = is_paraphrase("Text A", "Text B", mock_model, threshold=0.7)
            assert result is True

    def test_is_paraphrase_below_threshold(self, mock_model):
        """Test that is_paraphrase returns False when similarity < threshold."""
        # Mock the similarity to be low
        with patch('code.utils.semantic_matcher.cosine_similarity', return_value=np.array([[0.5]])):
            result = is_paraphrase("Text A", "Text B", mock_model, threshold=0.7)
            assert result is False

    def test_is_paraphrase_edge_case(self, mock_model):
        """Test is_paraphrase at exact threshold."""
        with patch('code.utils.semantic_matcher.cosine_similarity', return_value=np.array([[0.7]])):
            result = is_paraphrase("Text A", "Text B", mock_model, threshold=0.7)
            assert result is True  # >= threshold

    def test_batch_is_paraphrase(self, mock_model):
        """Test batch paraphrase detection."""
        texts1 = ["A", "B", "C"]
        texts2 = ["A'", "B'", "C'"]
        
        # Mock batch similarity
        with patch('code.utils.semantic_matcher.encode_texts', return_value=np.random.rand(6, 384).astype(np.float32)):
            with patch('code.utils.semantic_matcher.cosine_similarity', return_value=np.array([[0.8], [0.6], [0.9]])):
                results = is_paraphrase(texts1, texts2, mock_model, threshold=0.7)
                
                # Should return list of booleans
                assert len(results) == 3
                assert results[0] is True   # 0.8 >= 0.7
                assert results[1] is False  # 0.6 < 0.7
                assert results[2] is True   # 0.9 >= 0.7
