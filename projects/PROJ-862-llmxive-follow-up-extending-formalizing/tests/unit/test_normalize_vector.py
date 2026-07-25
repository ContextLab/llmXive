import pytest
import torch
import math
from code.model_utils import normalize_vector

class TestNormalizeVector:
    """
    Unit tests for the normalize_vector function in model_utils.py.
    Ensures L2 normalization logic is correct and handles edge cases.
    """

    def test_normalize_single_vector(self):
        """Test normalization of a simple 1D vector."""
        vector = torch.tensor([3.0, 4.0])
        expected_norm = 5.0
        expected_result = torch.tensor([0.6, 0.8])
        
        result = normalize_vector(vector)
        
        assert torch.allclose(result, expected_result, atol=1e-6)
        assert torch.allclose(torch.linalg.norm(result), torch.tensor(1.0), atol=1e-6)

    def test_normalize_batch_vectors(self):
        """Test normalization of a batch of 2D vectors."""
        vectors = torch.tensor([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0]
        ])
        
        result = normalize_vector(vectors)
        
        # Check shape
        assert result.shape == vectors.shape
        
        # Check that each row has unit norm
        norms = torch.linalg.norm(result, dim=1)
        assert torch.allclose(norms, torch.ones(3), atol=1e-6)

    def test_normalize_preserves_direction(self):
        """Test that normalization preserves the direction of the vector."""
        vector = torch.tensor([1.0, -2.0, 3.0])
        result = normalize_vector(vector)
        
        # The result should be a scalar multiple of the input
        # Check if result / vector is constant (ignoring zeros)
        mask = vector != 0
        ratios = result[mask] / vector[mask]
        assert torch.allclose(ratios, ratios[0], atol=1e-6)

    def test_normalize_zero_vector_raises(self):
        """Test that normalizing a zero vector raises a ValueError."""
        vector = torch.tensor([0.0, 0.0, 0.0])
        
        with pytest.raises(ValueError, match="zero or near-zero norm"):
            normalize_vector(vector)

    def test_normalize_near_zero_vector_raises(self):
        """Test that normalizing a near-zero vector raises a ValueError."""
        vector = torch.tensor([1e-15, 1e-15, 1e-15])
        
        with pytest.raises(ValueError, match="zero or near-zero norm"):
            normalize_vector(vector)

    def test_normalize_type_error(self):
        """Test that passing a non-tensor raises a TypeError."""
        with pytest.raises(TypeError):
            normalize_vector([1.0, 2.0, 3.0])

    def test_normalize_high_dimension_vector(self):
        """Test normalization with a high-dimensional vector (simulating hidden state)."""
        hidden_size = 4096
        vector = torch.randn(hidden_size)
        
        result = normalize_vector(vector)
        
        assert result.shape == (hidden_size,)
        assert torch.allclose(torch.linalg.norm(result), torch.tensor(1.0), atol=1e-6)
