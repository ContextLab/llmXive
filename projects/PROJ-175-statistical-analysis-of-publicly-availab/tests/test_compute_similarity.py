import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
import json

# Mock the sentence transformer to avoid heavy download during unit tests
# but ensure the logic holds
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

from code.data.compute_similarity import (
    load_ingredient_pairs,
    compute_cosine_similarity,
    process_similarity,
    save_output
)

def test_compute_cosine_similarity_unit():
    """Test the math of cosine similarity with known vectors."""
    # Vector A: [1, 0, 0]
    # Vector B: [0, 1, 0]
    # Vector C: [1, 0, 0]
    # Sim(A, B) = 0, Sim(A, C) = 1, Sim(A, A) = 1
    matrix = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0]
    ])
    
    sim_matrix = compute_cosine_similarity(matrix)
    
    assert np.isclose(sim_matrix[0, 1], 0.0)
    assert np.isclose(sim_matrix[0, 2], 1.0)
    assert np.isclose(sim_matrix[0, 0], 1.0)
    assert np.isclose(sim_matrix[1, 2], 0.0)

def test_process_similarity_structure():
    """Test that process_similarity returns the correct structure."""
    # Create a mock dataframe
    df = pd.DataFrame({
        'canonical_name': ['flour', 'sugar', 'salt']
    })
    
    # Mock model
    class MockModel:
        def encode(self, texts, convert_to_numpy=True):
            # Return random orthogonal-ish vectors for testing
            # Shape: (len(texts), 384)
            return np.random.rand(len(texts), 384)
    
    mock_model = MockModel()
    result = process_similarity(df, mock_model)
    
    assert 'ingredient_1' in result.columns
    assert 'ingredient_2' in result.columns
    assert 'similarity_score' in result.columns
    
    # Check row count: 3 items -> 3 pairs (0-1, 0-2, 1-2)
    assert len(result) == 3

def test_save_output_creates_file():
    """Test that save_output actually writes a file."""
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.parquet")
        save_output(df, output_path)
        
        assert os.path.exists(output_path)
        loaded = pd.read_parquet(output_path)
        assert len(loaded) == 2
        assert 'a' in loaded.columns