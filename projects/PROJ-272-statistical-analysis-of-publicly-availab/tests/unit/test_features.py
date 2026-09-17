import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features import (
    calculate_ttr, 
    calculate_mtld, 
    calculate_noun_verb_ratio, 
    extract_semantic_features,
    get_embedding_model
)

class TestSemanticFeatures:
    """Tests for semantic feature extraction (T024)."""

    def test_embedding_shape(self):
        """Test that embeddings have the correct shape [N, 384] and dtype float32."""
        texts = [
            "This is a test sentence.",
            "Another test sentence here.",
            "Short one."
        ]
        
        embeddings = extract_semantic_features(texts)
        
        assert embeddings.shape == (len(texts), 384), f"Expected shape (3, 384), got {embeddings.shape}"
        assert embeddings.dtype == np.float32, f"Expected dtype float32, got {embeddings.dtype}"

    def test_embedding_values(self):
        """Test that embeddings are within valid range (cosine similarity based, but raw embeddings can vary)."""
        texts = ["Hello world", "Hello world"]
        embeddings = extract_semantic_features(texts)
        
        # Check for NaNs
        assert not np.any(np.isnan(embeddings)), "Embeddings contain NaN values"
        
        # Check for Inf
        assert not np.any(np.isinf(embeddings)), "Embeddings contain Inf values"

    def test_identical_texts_similarity(self):
        """Test that identical texts produce similar embeddings."""
        texts = ["The quick brown fox", "The quick brown fox"]
        embeddings = extract_semantic_features(texts)
        
        # Cosine similarity between identical embeddings should be 1.0
        # We'll check the Euclidean distance is near zero
        dist = np.linalg.norm(embeddings[0] - embeddings[1])
        assert dist < 1e-5, f"Identical texts produced different embeddings: dist={dist}"

    def test_empty_text_handling(self):
        """Test that empty or invalid texts result in zero vectors."""
        texts = ["Valid text", "", None, "Another valid"]
        embeddings = extract_semantic_features(texts)
        
        # Check the second and third rows are zero vectors
        assert np.allclose(embeddings[1], 0), "Empty string should produce zero vector"
        assert np.allclose(embeddings[2], 0), "None should produce zero vector"

    def test_model_loading_cpu(self):
        """Test that the model loads and respects CPU constraints (conceptual)."""
        model = get_embedding_model()
        # The model should be loaded. We can't easily check device in this unit test without running,
        # but we ensure the function returns a valid model object.
        assert model is not None
        assert hasattr(model, 'encode')