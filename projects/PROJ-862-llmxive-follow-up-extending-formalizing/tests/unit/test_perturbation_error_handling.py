"""
Unit tests for error handling in perturbation.py
"""
import pytest
import torch
import numpy as np
from code.perturbation import inject_and_project, ProjectionError

class TestProjectionErrorHandling:
    """Tests to ensure ProjectionError is raised on invalid inputs."""

    def test_raises_on_none_embeddings(self):
        """Test that None input embeddings raise ProjectionError."""
        with pytest.raises(ProjectionError, match="Input embeddings cannot be None"):
            inject_and_project(
                input_embeddings=None,
                sigma=0.1,
                model_embedding_matrix=torch.randn(100, 768)
            )

    def test_raises_on_none_embedding_matrix(self):
        """Test that None model embedding matrix raises ProjectionError."""
        embeddings = torch.randn(2, 10, 768)
        with pytest.raises(ProjectionError, match="Model embedding matrix cannot be None"):
            inject_and_project(
                input_embeddings=embeddings,
                sigma=0.1,
                model_embedding_matrix=None
            )

    def test_raises_on_dimension_mismatch(self):
        """Test that mismatched hidden dimensions raise ProjectionError."""
        # Embeddings: (batch, seq, hidden=768)
        embeddings = torch.randn(2, 10, 768)
        # Embedding Matrix: (vocab, hidden=512) -> Mismatch!
        embedding_matrix = torch.randn(1000, 512)
        
        with pytest.raises(ProjectionError, match="Dimension mismatch"):
            inject_and_project(
                input_embeddings=embeddings,
                sigma=0.1,
                model_embedding_matrix=embedding_matrix
            )

    def test_raises_on_empty_embedding_matrix(self):
        """Test that empty embedding matrix raises ProjectionError."""
        embeddings = torch.randn(2, 10, 768)
        # Empty matrix: (0, 768)
        embedding_matrix = torch.empty(0, 768)
        
        with pytest.raises(ProjectionError, match="Model embedding matrix is empty"):
            inject_and_project(
                input_embeddings=embeddings,
                sigma=0.1,
                model_embedding_matrix=embedding_matrix
            )

    def test_raises_on_invalid_padding_mask_shape(self):
        """Test that mismatched padding mask shape raises ProjectionError."""
        embeddings = torch.randn(2, 10, 768)
        embedding_matrix = torch.randn(1000, 768)
        # Wrong shape mask: (2, 5) instead of (2, 10)
        padding_mask = torch.zeros(2, 5, dtype=torch.bool)
        
        with pytest.raises(ProjectionError, match="Padding mask shape"):
            inject_and_project(
                input_embeddings=embeddings,
                sigma=0.1,
                model_embedding_matrix=embedding_matrix,
                padding_mask=padding_mask
            )

    def test_successful_projection_with_valid_inputs(self):
        """Test that valid inputs do NOT raise an error."""
        batch_size, seq_len, hidden_dim = 2, 10, 768
        vocab_size = 1000
        
        embeddings = torch.randn(batch_size, seq_len, hidden_dim)
        embedding_matrix = torch.randn(vocab_size, hidden_dim)
        
        # This should run without raising ProjectionError
        try:
            token_ids, projected_embeddings = inject_and_project(
                input_embeddings=embeddings,
                sigma=0.1,
                model_embedding_matrix=embedding_matrix
            )
            assert token_ids.shape == (batch_size, seq_len)
            assert projected_embeddings.shape == (batch_size, seq_len, hidden_dim)
        except ProjectionError:
            pytest.fail("ProjectionError raised unexpectedly for valid inputs.")

    def test_successful_projection_with_padding_mask(self):
        """Test that valid inputs with valid padding mask work correctly."""
        batch_size, seq_len, hidden_dim = 2, 10, 768
        vocab_size = 1000
        
        embeddings = torch.randn(batch_size, seq_len, hidden_dim)
        embedding_matrix = torch.randn(vocab_size, hidden_dim)
        padding_mask = torch.zeros(batch_size, seq_len, dtype=torch.bool)
        
        try:
            token_ids, projected_embeddings = inject_and_project(
                input_embeddings=embeddings,
                sigma=0.1,
                model_embedding_matrix=embedding_matrix,
                padding_mask=padding_mask
            )
            assert token_ids.shape == (batch_size, seq_len)
        except ProjectionError:
            pytest.fail("ProjectionError raised unexpectedly for valid inputs with mask.")