"""
Unit tests for the perturbation module.
"""
import torch
import pytest
from perturbation import inject_and_project


def test_inject_and_project_basic():
    """Test basic functionality with known inputs."""
    # Setup: Create a simple embedding and embedding matrix
    batch_size = 2
    hidden_dim = 4
    vocab_size = 10
    
    # Create a deterministic embedding matrix (identity-like for simplicity)
    model_embedding_matrix = torch.eye(vocab_size, hidden_dim)
    
    # Create input embeddings (first two rows of identity for predictability)
    embedding = torch.eye(hidden_dim)[:batch_size]
    
    sigma = 0.1
    random_seed = 42
    
    # Act
    perturbed_token_ids, perturbed_embeddings = inject_and_project(
        embedding, sigma, model_embedding_matrix, random_seed
    )
    
    # Assert
    assert perturbed_token_ids.shape == (batch_size,), "Token IDs shape mismatch"
    assert perturbed_embeddings.shape == (batch_size, hidden_dim), "Perturbed embeddings shape mismatch"
    assert torch.all(perturbed_token_ids >= 0) and torch.all(perturbed_token_ids < vocab_size), \
        "Token IDs out of range"
    
    # Verify that perturbed embeddings match the embedding matrix rows
    for i in range(batch_size):
        token_id = perturbed_token_ids[i].item()
        expected_embedding = model_embedding_matrix[token_id]
        assert torch.allclose(perturbed_embeddings[i], expected_embedding), \
            f"Perturbed embedding {i} does not match token {token_id} embedding"


def test_inject_and_project_sigma_zero():
    """Test that sigma=0 returns the original nearest token (no noise)."""
    batch_size = 2
    hidden_dim = 4
    vocab_size = 10
    
    model_embedding_matrix = torch.eye(vocab_size, hidden_dim)
    embedding = torch.eye(hidden_dim)[:batch_size]
    
    sigma = 0.0
    random_seed = 42
    
    perturbed_token_ids, perturbed_embeddings = inject_and_project(
        embedding, sigma, model_embedding_matrix, random_seed
    )
    
    # With sigma=0, the nearest token should be the one corresponding to the input
    # Since input is row 0 and 1 of identity, and matrix is identity, 
    # nearest should be token 0 and 1 respectively
    assert perturbed_token_ids[0].item() == 0
    assert perturbed_token_ids[1].item() == 1


def test_inject_and_project_negative_sigma():
    """Test that negative sigma raises ValueError."""
    embedding = torch.randn(1, 4)
    model_embedding_matrix = torch.randn(10, 4)
    
    with pytest.raises(ValueError, match="Sigma must be non-negative"):
        inject_and_project(embedding, -0.1, model_embedding_matrix)


def test_inject_and_project_dimension_mismatch():
    """Test that dimension mismatch raises ValueError."""
    embedding = torch.randn(1, 4)
    model_embedding_matrix = torch.randn(10, 5)  # Different hidden dim
    
    with pytest.raises(ValueError, match="Embedding dimension mismatch"):
        inject_and_project(embedding, 0.1, model_embedding_matrix)


def test_inject_and_project_reproducibility():
    """Test that same seed produces same results."""
    batch_size = 2
    hidden_dim = 4
    vocab_size = 10
    
    model_embedding_matrix = torch.randn(vocab_size, hidden_dim)
    embedding = torch.randn(batch_size, hidden_dim)
    sigma = 0.5
    random_seed = 123
    
    # First run
    ids1, emb1 = inject_and_project(embedding, sigma, model_embedding_matrix, random_seed)
    
    # Second run with same seed
    ids2, emb2 = inject_and_project(embedding, sigma, model_embedding_matrix, random_seed)
    
    assert torch.equal(ids1, ids2), "Token IDs not reproducible with same seed"
    assert torch.allclose(emb1, emb2), "Perturbed embeddings not reproducible with same seed"