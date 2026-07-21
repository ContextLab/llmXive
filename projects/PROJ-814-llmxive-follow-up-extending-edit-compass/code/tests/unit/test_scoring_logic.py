import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from sentence_transformers import SentenceTransformer
import torch

from src.services.scoring import compute_logic_score, calculate_logic_scores_batch, load_embedding_model
from src.data_models import EditInstance

@pytest.fixture
def mock_model():
    """Create a mock SentenceTransformer model."""
    model = Mock(spec=SentenceTransformer)
    # Mock encode to return random but consistent embeddings for testing
    def mock_encode(sentences, convert_to_tensor=False):
        if convert_to_tensor:
            return torch.tensor([[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]) # Identical for simplicity
        return np.array([[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]])
    model.encode = mock_encode
    return model

def test_compute_logic_score_similarity(mock_model):
    """Test that compute_logic_score returns a value in [-1, 1]."""
    instruction = "Edit this image"
    description = "The image has been edited"
    
    score = compute_logic_score(instruction, description, mock_model)
    
    assert -1.0 <= score <= 1.0

def test_compute_logic_score_empty_strings(mock_model):
    """Test handling of empty strings."""
    score = compute_logic_score("", "", mock_model)
    assert score == 0.0

def test_compute_logic_score_single_char(mock_model):
    """Test handling of single character strings."""
    score = compute_logic_score("a", "b", mock_model)
    assert -1.0 <= score <= 1.0

def test_calculate_logic_scores_batch(mock_model):
    """Test batch calculation of logic scores."""
    instances = [
        EditInstance(instance_id="1", source_image_path="a.jpg", edited_image_path="b.jpg", instruction="I1", category="C", human_judgment_score=1.0),
        EditInstance(instance_id="2", source_image_path="c.jpg", edited_image_path="d.jpg", instruction="I2", category="C", human_judgment_score=1.0)
    ]
    descriptions = ["D1", "D2"]
    
    scores = calculate_logic_scores_batch(instances, descriptions, mock_model)
    
    assert len(scores) == 2
    for s in scores:
        assert -1.0 <= s <= 1.0

def test_load_embedding_model_cpu():
    """Test that the embedding model can be loaded on CPU."""
    # This test might be skipped if the model is too large for the test environment,
    # but we verify the function exists and accepts the device argument.
    with patch('src.services.scoring.SentenceTransformer') as mock_sentence_transformer:
        mock_sentence_transformer.return_value = Mock()
        model = load_embedding_model("cpu")
        mock_sentence_transformer.assert_called_once_with("all-MiniLM-L6-v2", device="cpu")