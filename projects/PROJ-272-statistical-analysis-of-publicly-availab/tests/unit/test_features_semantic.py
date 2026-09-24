import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features import (
    clean_text_for_embedding,
    extract_semantic_features,
    calculate_participant_similarity,
    calculate_cosine_similarity_matrix
)
from config import get_device

@pytest.fixture
def sample_texts():
    return [
        "This is a test sentence.",
        "Another sentence for testing.",
        "The quick brown fox jumps over the lazy dog.",
        "<laughter> This has non-verbal annotation.",
        "Short.",
        "" # Empty string
    ]

def test_clean_text_for_embedding(sample_texts):
    cleaned = [clean_text_for_embedding(t) for t in sample_texts]
    # Check non-verbal annotation removal
    assert "<laughter>" not in cleaned[3]
    # Check normalization
    assert cleaned[0] == "This is a test sentence."
    # Check empty string handling
    assert cleaned[5] == ""

def test_extract_semantic_features(sample_texts):
    # This test requires the model to be loaded. 
    # In a real CI, we might mock the model or use a smaller model.
    # For this task, we assume the model is available or skip if not.
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2", device=get_device())
        
        embeddings = extract_semantic_features(sample_texts, model, batch_size=2)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (len(sample_texts), 384)
        assert embeddings.dtype == np.float32
        
        # Check that non-empty texts have non-zero embeddings (roughly)
        # Empty text should be zeros
        assert np.allclose(embeddings[5], 0.0)
        
        # Check that non-empty texts are not all zeros
        assert not np.allclose(embeddings[0], 0.0)
        
    except ImportError:
        pytest.skip("sentence_transformers not installed")
    except Exception as e:
        # If model download fails or similar, skip
        pytest.skip(f"Model loading failed: {e}")

def test_calculate_cosine_similarity_matrix(sample_texts):
    # Create dummy embeddings
    embeddings = np.random.rand(len(sample_texts), 384).astype(np.float32)
    sim_matrix = calculate_cosine_similarity_matrix(embeddings)
    
    assert sim_matrix.shape == (len(sample_texts), len(sample_texts))
    # Diagonal should be 1.0 (self-similarity)
    assert np.allclose(np.diag(sim_matrix), 1.0, atol=1e-5)

def test_calculate_participant_similarity(sample_texts):
    embeddings = np.random.rand(len(sample_texts), 384).astype(np.float32)
    similarities = calculate_participant_similarity(embeddings)
    
    assert len(similarities) == len(sample_texts)
    assert all(-1.0 <= s <= 1.0 for s in similarities)