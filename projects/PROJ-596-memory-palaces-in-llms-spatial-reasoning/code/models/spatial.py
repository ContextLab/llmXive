"""
Spatial memory module for soft-addressed retrieval using cosine similarity.

Implements FR-002: Soft-addressed retrieval via cosine similarity between
query embeddings and spatial memory slot embeddings.
"""

import torch
import torch.nn.functional as F
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def compute_cosine_similarity(
    query: torch.Tensor,
    keys: torch.Tensor,
    eps: float = 1e-8
) -> torch.Tensor:
    """
    Compute cosine similarity between a query vector and a set of key vectors.
    
    Args:
        query: Query tensor of shape (hidden_dim,) or (batch_size, hidden_dim).
        keys: Key tensor of shape (num_slots, hidden_dim) or (batch_size, num_slots, hidden_dim).
        eps: Small epsilon value to avoid division by zero.
    
    Returns:
        Tensor of cosine similarities. Shape depends on input:
        - If query is (hidden_dim,) and keys is (num_slots, hidden_dim): (num_slots,)
        - If query is (batch_size, hidden_dim) and keys is (batch_size, num_slots, hidden_dim): (batch_size, num_slots)
    
    Raises:
        ValueError: If input shapes are incompatible.
    """
    # Normalize query and keys along the hidden dimension
    query_norm = F.normalize(query, p=2, dim=-1)
    keys_norm = F.normalize(keys, p=2, dim=-1)
    
    # Compute dot product to get cosine similarity
    # For 1D query and 2D keys: (hidden_dim,) @ (num_slots, hidden_dim).T -> (num_slots,)
    # For 2D query and 3D keys: (batch, hidden) @ (batch, num_slots, hidden).T -> (batch, num_slots)
    similarity = torch.sum(query_norm * keys_norm, dim=-1)
    
    return similarity


def soft_addressed_retrieve(
    query: torch.Tensor,
    memory_slots: torch.Tensor,
    temperature: float = 1.0,
    top_k: Optional[int] = None
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Perform soft-addressed retrieval from memory slots using cosine similarity.
    
    This implements the soft-attention mechanism where the query retrieves
    information from memory slots based on cosine similarity of their embeddings.
    
    Args:
        query: Query tensor of shape (hidden_dim,) or (batch_size, hidden_dim).
        memory_slots: Memory slot tensor of shape (num_slots, hidden_dim) or 
                     (batch_size, num_slots, hidden_dim).
        temperature: Temperature scaling for the attention weights. Higher values
                    make the distribution softer (more uniform).
        top_k: If provided, only return the top_k most similar slots. If None,
              return all slots.
    
    Returns:
        Tuple of (retrieved_content, attention_weights):
        - retrieved_content: Weighted sum of memory slots, same shape as memory_slots
        - attention_weights: Softmax-normalized similarity scores
    
    Raises:
        ValueError: If input shapes are incompatible or temperature <= 0.
    """
    if temperature <= 0:
        raise ValueError(f"Temperature must be positive, got {temperature}")
    
    # Ensure query and memory_slots have compatible batch dimensions
    if query.dim() == 1:
        query = query.unsqueeze(0)  # (1, hidden_dim)
        if memory_slots.dim() == 2:
            memory_slots = memory_slots.unsqueeze(0)  # (1, num_slots, hidden_dim)
        elif memory_slots.dim() != 3:
            raise ValueError(f"Expected memory_slots to be 2D or 3D, got {memory_slots.dim()}D")
    elif query.dim() == 2:
        if memory_slots.dim() == 2:
            memory_slots = memory_slots.unsqueeze(0).expand(query.size(0), -1, -1)
        elif memory_slots.dim() != 3:
            raise ValueError(f"Expected memory_slots to be 2D or 3D, got {memory_slots.dim()}D")
    else:
        raise ValueError(f"Query must be 1D or 2D, got {query.dim()}D")
    
    batch_size, num_slots, hidden_dim = memory_slots.shape
    
    if query.shape[0] != batch_size:
        raise ValueError(f"Batch dimension mismatch: query has {query.shape[0]}, memory_slots has {batch_size}")
    
    if query.shape[1] != hidden_dim:
        raise ValueError(f"Hidden dimension mismatch: query has {query.shape[1]}, memory_slots has {hidden_dim}")
    
    # Compute cosine similarities
    similarities = compute_cosine_similarity(query, memory_slots)  # (batch_size, num_slots)
    
    # Apply temperature scaling
    scaled_similarities = similarities / temperature
    
    # Compute attention weights via softmax
    attention_weights = F.softmax(scaled_similarities, dim=-1)  # (batch_size, num_slots)
    
    # Apply top-k filtering if requested
    if top_k is not None and top_k < num_slots:
        # Create mask for top-k
        _, top_indices = torch.topk(scaled_similarities, k=top_k, dim=-1)  # (batch_size, top_k)
        mask = torch.zeros_like(scaled_similarities, dtype=torch.bool)
        mask.scatter_(dim=-1, index=top_indices, value=True)
        attention_weights = attention_weights * mask
        # Renormalize to ensure weights sum to 1
        attention_weights = F.softmax(attention_weights / temperature, dim=-1)
    
    # Compute retrieved content as weighted sum of memory slots
    retrieved_content = torch.einsum('bs,bsh->bsh', attention_weights, memory_slots)
    
    # Squeeze batch dimension if original query was 1D
    if retrieved_content.shape[0] == 1 and query.dim() == 1:
        retrieved_content = retrieved_content.squeeze(0)
        attention_weights = attention_weights.squeeze(0)
    
    return retrieved_content, attention_weights


def compute_spatial_attention_loss(
    attention_weights: torch.Tensor,
    target_sparsity: float = 0.9,
    entropy_weight: float = 0.1
) -> torch.Tensor:
    """
    Compute a loss function to encourage sparse, focused attention on memory slots.
    
    This loss penalizes diffuse attention distributions, encouraging the model
    to focus on a small number of relevant memory slots (similar to how human
    memory retrieval focuses on specific locations).
    
    Args:
        attention_weights: Attention weight tensor of shape (batch_size, num_slots).
        target_sparsity: Target proportion of zero (or near-zero) weights.
        entropy_weight: Weight for the entropy regularization term.
    
    Returns:
        Scalar loss tensor.
    """
    # Sparsity loss: encourage attention to be concentrated
    # Using L1 norm of attention weights as a sparsity measure
    l1_norm = torch.sum(torch.abs(attention_weights), dim=-1)
    sparsity_loss = torch.mean(torch.abs(l1_norm - 1.0))  # Attention should sum to 1
    
    # Entropy regularization: encourage focused (low entropy) distributions
    # Higher entropy = more uniform (less focused)
    epsilon = 1e-10
    entropy = -torch.sum(attention_weights * torch.log(attention_weights + epsilon), dim=-1)
    entropy_loss = torch.mean(entropy)
    
    # Combined loss
    loss = sparsity_loss + entropy_weight * entropy_loss
    
    return loss


class SpatialMemoryRetriever(torch.nn.Module):
    """
    A module for soft-addressed retrieval from spatial memory slots.
    
    This module wraps the soft-addressed retrieval functionality and can be
    integrated into a larger model architecture.
    """
    
    def __init__(self, num_slots: int, hidden_dim: int, temperature: float = 1.0):
        """
        Initialize the spatial memory retriever.
        
        Args:
            num_slots: Number of memory slots in the grid.
            hidden_dim: Dimensionality of the hidden representations.
            temperature: Initial temperature for soft attention.
        """
        super().__init__()
        self.num_slots = num_slots
        self.hidden_dim = hidden_dim
        self.temperature = temperature
        
        # Initialize memory slots with small random values
        self.memory_slots = torch.nn.Parameter(
            torch.randn(num_slots, hidden_dim) * 0.02
        )
    
    def forward(
        self,
        query: torch.Tensor,
        temperature: Optional[float] = None,
        top_k: Optional[int] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Perform retrieval from memory slots given a query.
        
        Args:
            query: Query tensor.
            temperature: Override default temperature if provided.
            top_k: Optional top-k filtering.
        
        Returns:
            Tuple of (retrieved_content, attention_weights).
        """
        temp = temperature if temperature is not None else self.temperature
        return soft_addressed_retrieve(query, self.memory_slots, temp, top_k)
    
    def update_slots(self, new_slots: torch.Tensor):
        """
        Update the memory slots with new values.
        
        Args:
            new_slots: New slot values of shape (num_slots, hidden_dim).
        """
        if new_slots.shape != self.memory_slots.shape:
            raise ValueError(f"Shape mismatch: expected {self.memory_slots.shape}, got {new_slots.shape}")
        with torch.no_grad():
            self.memory_slots.copy_(new_slots)
    
    def get_slot_embeddings(self) -> torch.Tensor:
        """
        Get the current memory slot embeddings.
        
        Returns:
            Tensor of shape (num_slots, hidden_dim).
        """
        return self.memory_slots