"""
Unit tests for semantic similarity extraction (T017b).

These tests verify the logic of the similarity computation without
necessarily running the full model if dependencies are missing,
but they mock the model to ensure the pipeline logic is sound.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.feature_extraction.semantic_similarity import (
    calculate_similarity,
    extract_semantic_similarity_scores,
    get_embeddings_batch
)


def test_calculate_similarity_identical():
    """Test that identical vectors have similarity 1.0."""
    v1 = np.array([1.0, 2.0, 3.0])
    v2 = np.array([1.0, 2.0, 3.0])
    score = calculate_similarity(v1, v2)
    assert np.isclose(score, 1.0)


def test_calculate_similarity_orthogonal():
    """Test that orthogonal vectors have similarity 0.0."""
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0])
    score = calculate_similarity(v1, v2)
    assert np.isclose(score, 0.0)


def test_calculate_similarity_opposite():
    """Test that opposite vectors have similarity -1.0."""
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([-1.0, 0.0, 0.0])
    score = calculate_similarity(v1, v2)
    assert np.isclose(score, -1.0)


@patch('code.feature_extraction.semantic_similarity.AutoTokenizer')
@patch('code.feature_extraction.semantic_similarity.AutoModel')
def test_extract_scores_logic(mock_model_class, mock_tokenizer_class):
    """Test the extraction logic with mocked model."""
    # Setup mocks
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = MagicMock(
        attention_mask=torch.tensor([[1, 1, 0]]),
        input_ids=torch.tensor([[1, 2, 3]])
    )
    mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
    
    mock_model = MagicMock()
    mock_output = MagicMock()
    mock_output.last_hidden_state = torch.tensor([[[0.1, 0.2], [0.3, 0.4], [0.0, 0.0]]])
    mock_model.return_value = mock_model
    mock_model.return_value.return_value = mock_output
    mock_model_class.from_pretrained.return_value = mock_model
    
    # Mock the forward pass to return a fixed tensor
    mock_model.forward = MagicMock(return_value=mock_output)
    
    # Create dummy dataframe
    df = pd.DataFrame({
        'code_content': ['print("hello")', 'x = 1 + 2'],
        'pr_id': [1, 2]
    })
    
    # We need to patch the torch and transformers imports inside the module
    # or pass the mock objects directly. Since the function calls load_model,
    # let's patch the whole load process.
    
    with patch('code.feature_extraction.semantic_similarity.load_model_and_tokenizer') as mock_load:
        mock_t = MagicMock()
        mock_m = MagicMock()
        
        # Mock embeddings generation to return dummy vectors
        mock_m.embeddings = np.array([[0.1, 0.2], [0.9, 0.8]])
        
        def mock_get_embeddings(snippets, tok, mdl, bs):
            # Return dummy embeddings
            return np.array([[0.1, 0.2], [0.9, 0.8]])
        
        with patch('code.feature_extraction.semantic_similarity.get_embeddings_batch', side_effect=mock_get_embeddings):
            result = extract_semantic_similarity_scores(df, mock_m, mock_t)
            
            assert 'semantic_similarity_score' in result.columns
            assert len(result) == 2
            # Check that scores are reasonable (between -1 and 1)
            assert all(-1.0 <= s <= 1.0 for s in result['semantic_similarity_score'])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
