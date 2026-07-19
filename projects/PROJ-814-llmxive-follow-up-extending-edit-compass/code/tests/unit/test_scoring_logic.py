"""
Unit tests for T018: Logic Score computation.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from sentence_transformers import SentenceTransformer
from src.services.scoring import compute_logic_score, calculate_logic_scores, load_embedding_model
from src.data_models import ScoreRecord

@pytest.fixture
def mock_model():
    """Create a mock SentenceTransformer model that returns deterministic embeddings."""
    mock = Mock(spec=SentenceTransformer)
    # Mock encode to return fixed embeddings for specific inputs
    # instruction: [1, 0, 0], description: [0.8, 0.6, 0] -> sim ~ 0.8
    def mock_encode(texts, convert_to_numpy=False):
        embeddings = []
        for t in texts:
            if "instruction" in t.lower():
                embeddings.append(np.array([1.0, 0.0, 0.0]))
            elif "description" in t.lower():
                embeddings.append(np.array([0.8, 0.6, 0.0]))
            else:
                # Random-ish but deterministic for other inputs
                np.random.seed(hash(t) % 2**32)
                vec = np.random.rand(3)
                vec = vec / np.linalg.norm(vec)
                embeddings.append(vec)
        result = np.array(embeddings)
        if convert_to_numpy:
            return result
        return result.tolist() # Return list if not numpy requested, though usually numpy
    
    mock.encode.side_effect = mock_encode
    return mock

def test_compute_logic_score_similarity(mock_model):
    """Test that compute_logic_score returns a value in [-1, 1]."""
    instruction = "instruction to edit image"
    description = "description of edited image"
    
    score = compute_logic_score(instruction, description, mock_model)
    
    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0

def test_compute_logic_score_empty_strings(mock_model):
    """Test behavior with empty strings."""
    score = compute_logic_score("", "", mock_model)
    assert score == 0.0

def test_compute_logic_score_single_char(mock_model):
    """Test with very short strings."""
    score = compute_logic_score("a", "b", mock_model)
    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0

def test_calculate_logic_scores_batch(mock_model):
    """Test batch calculation of logic scores."""
    batch = [
        {"id": "1", "instruction": "instruction A", "vllm_description": "description A"},
        {"id": "2", "instruction": "instruction B", "vllm_description": "description B"},
        {"id": "3", "instruction": "instruction C", "vllm_description": ""}, # Missing desc
    ]
    
    # Patch the function to use our mock model
    with patch('src.services.scoring.get_logger'):
        records = calculate_logic_scores(batch, mock_model)
    
    assert len(records) == 3
    assert all(isinstance(r, ScoreRecord) for r in records)
    assert all(isinstance(r.logic_score, float) for r in records)
    assert -1.0 <= records[0].logic_score <= 1.0
    assert -1.0 <= records[1].logic_score <= 1.0
    # Missing description should result in 0.0
    assert records[2].logic_score == 0.0
    assert records[2].instance_id == "3"

def test_load_embedding_model_cpu():
    """Test that the model is loaded with CPU device."""
    with patch('src.services.scoring.SentenceTransformer') as MockTransformer:
        mock_instance = Mock()
        MockTransformer.return_value = mock_instance
        
        model = load_embedding_model()
        
        # Verify SentenceTransformer was called with device="cpu"
        MockTransformer.assert_called_once_with("all-MiniLM-L6-v2", device="cpu")
        assert model == mock_instance
