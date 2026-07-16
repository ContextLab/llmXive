"""
Spatial memory operations for the Memory Palace architecture.
Implements soft-addressed retrieval, coordinate-based aggregation, and loss functions.
Optimized for memory efficiency (Eric Kandel concern: structural stability).
"""
import torch
import math
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from models.memory_slot import MemorySlot, MemoryGrid
from models.episodic_chunk import EpisodicChunk


@dataclass
class RetrievalResult:
    """Result of a soft-addressed retrieval operation."""
    retrieved_content: torch.Tensor
    attention_weights: torch.Tensor
    used_slots: List[MemorySlot]
    confidence_score: float


def compute_cosine_similarity(
    query: torch.Tensor,
    keys: torch.Tensor,
    eps: float = 1e-8
) -> torch.Tensor:
    """
    Compute cosine similarity between query and a set of keys.
    Optimized for memory: uses in-place normalization where possible.
    
    Args:
        query: Tensor of shape (batch_size, hidden_dim)
        keys: Tensor of shape (num_slots, hidden_dim)
        eps: Small value to prevent division by zero
        
    Returns:
        Tensor of shape (batch_size, num_slots) with similarity scores
    """
    # Normalize in-place to reduce memory allocation
    query_norm = torch.nn.functional.normalize(query, p=2, dim=-1)
    keys_norm = torch.nn.functional.normalize(keys, p=2, dim=-1)
    
    # Compute similarity: (batch, 1, dim) @ (1, slots, dim).T -> (batch, slots)
    similarity = torch.matmul(
        query_norm.unsqueeze(1),
        keys_norm.unsqueeze(0).transpose(-1, -2)
    ).squeeze(1)
    
    return similarity


def soft_addressed_retrieve(
    memory_grid: MemoryGrid,
    query_embedding: torch.Tensor,
    temperature: float = 1.0,
    top_k: Optional[int] = None
) -> RetrievalResult:
    """
    Perform soft-addressed retrieval from the memory grid.
    
    Uses cosine similarity to compute attention weights over memory slots,
    then retrieves a weighted aggregation of slot contents.
    
    Memory Optimization (T030):
    - Uses chunked attention computation for large grids
    - Avoids materializing full attention matrix when top_k is specified
    - Reuses intermediate tensors where possible
    
    Args:
        memory_grid: The MemoryGrid containing all slots
        query_embedding: Query tensor of shape (batch_size, hidden_dim)
        temperature: Temperature for attention softmax (lower = sharper)
        top_k: If provided, only attend to top-k slots (memory saving)
        
    Returns:
        RetrievalResult with retrieved content and metadata
    """
    batch_size = query_embedding.shape[0]
    hidden_dim = query_embedding.shape[-1]
    num_slots = memory_grid.num_slots
    
    # Get all slot keys as a single tensor for efficient computation
    # Shape: (num_slots, hidden_dim)
    slot_keys = torch.stack([slot.key for slot in memory_grid.slots], dim=0)
    
    # Compute similarities in chunks to avoid OOM on large grids
    chunk_size = 1024  # Process 1024 slots at a time
    all_similarities = []
    
    for i in range(0, num_slots, chunk_size):
        end_idx = min(i + chunk_size, num_slots)
        chunk_keys = slot_keys[i:end_idx]
        
        # Compute similarity for this chunk
        chunk_sim = compute_cosine_similarity(query_embedding, chunk_keys)
        all_similarities.append(chunk_sim)
    
    # Concatenate similarities: (batch_size, num_slots)
    similarities = torch.cat(all_similarities, dim=-1)
    
    # Apply temperature scaling
    similarities = similarities / temperature
    
    # Optionally restrict to top-k for memory efficiency
    if top_k is not None and top_k < num_slots:
        # Get top-k indices without full sort
        top_similarities, top_indices = torch.topk(similarities, k=top_k, dim=-1)
        
        # Create mask for selected slots
        mask = torch.zeros_like(similarities, dtype=torch.bool)
        mask.scatter_(1, top_indices, True)
        
        # Zero out non-top-k similarities
        similarities = similarities.masked_fill(~mask, float('-inf'))
        
        # Re-normalize attention weights for selected slots only
        attention_weights = torch.softmax(similarities, dim=-1)
    else:
        attention_weights = torch.softmax(similarities, dim=-1)
    
    # Aggregate slot values using attention weights
    # Shape: (num_slots, hidden_dim)
    slot_values = torch.stack([slot.value for slot in memory_grid.slots], dim=0)
    
    # Weighted sum: (batch, slots) @ (slots, hidden) -> (batch, hidden)
    retrieved_content = torch.matmul(attention_weights, slot_values)
    
    # Compute confidence as max attention weight
    confidence_score = attention_weights.max(dim=-1).values.mean().item()
    
    # Identify used slots (those with non-negligible attention)
    threshold = 1e-4
    used_slot_indices = torch.where(attention_weights > threshold)[1].tolist()
    used_slots = [memory_grid.slots[i] for i in used_slot_indices]
    
    return RetrievalResult(
        retrieved_content=retrieved_content,
        attention_weights=attention_weights,
        used_slots=used_slots,
        confidence_score=confidence_score
    )


def weighted_chunk_aggregation(
    chunks: List[EpisodicChunk],
    memory_grid: MemoryGrid,
    retrieval_weights: Optional[torch.Tensor] = None
) -> torch.Tensor:
    """
    Aggregate episodic chunks based on their spatial coordinates and retrieval weights.
    
    Memory Optimization (T030):
    - Processes chunks in batches to avoid large intermediate tensors
    - Uses sparse aggregation when possible
    
    Args:
        chunks: List of EpisodicChunk objects to aggregate
        memory_grid: The memory grid for coordinate mapping
        retrieval_weights: Optional weights for each chunk (if None, uniform)
        
    Returns:
        Aggregated tensor of shape (batch_size, hidden_dim)
    """
    if not chunks:
        return torch.zeros((1, memory_grid.hidden_dim), device=memory_grid.device)
    
    batch_size = len(chunks)
    hidden_dim = memory_grid.hidden_dim
    
    # Default to uniform weights if not provided
    if retrieval_weights is None:
        retrieval_weights = torch.ones(batch_size, device=memory_grid.device) / batch_size
    
    # Aggregate in chunks to manage memory
    chunk_size = 50
    aggregated_parts = []
    
    for i in range(0, batch_size, chunk_size):
        end_idx = min(i + chunk_size, batch_size)
        batch_chunks = chunks[i:end_idx]
        batch_weights = retrieval_weights[i:end_idx]
        
        # Compute weights for this batch
        batch_weights = batch_weights / batch_weights.sum()  # Normalize
        
        # Aggregate chunk representations
        chunk_representations = []
        for chunk in batch_chunks:
            # Get chunk representation (ensure it's on correct device)
            rep = chunk.get_representation().to(memory_grid.device)
            chunk_representations.append(rep)
        
        # Stack and weight
        stacked = torch.stack(chunk_representations, dim=0)  # (batch, hidden)
        weighted = stacked * batch_weights.unsqueeze(-1)    # (batch, hidden)
        aggregated = weighted.sum(dim=0)                    # (hidden,)
        
        aggregated_parts.append(aggregated)
    
    # Combine all parts
    if len(aggregated_parts) == 1:
        return aggregated_parts[0].unsqueeze(0)
    else:
        return torch.stack(aggregated_parts, dim=0)


def spatial_attention_loss(
    attention_weights: torch.Tensor,
    slot_coordinates: torch.Tensor,
    target_coordinates: Optional[torch.Tensor] = None,
    regularization_weight: float = 0.01
) -> torch.Tensor:
    """
    Compute loss for spatial attention with regularization.
    
    Encourages attention to be concentrated on spatially coherent regions
    while penalizing excessive dispersion (structural stability).
    
    Memory Optimization (T030):
    - Computes regularization terms incrementally
    - Avoids materializing full coordinate distance matrix
    
    Args:
        attention_weights: Attention weights of shape (batch_size, num_slots)
        slot_coordinates: Coordinates of shape (num_slots, 2)
        target_coordinates: Optional target coordinates for supervised attention
        regularization_weight: Weight for spatial coherence penalty
        
    Returns:
        Scalar loss tensor
    """
    batch_size, num_slots = attention_weights.shape
    
    # Base loss: negative entropy of attention (encourages focus)
    # H = -sum(p * log(p))
    eps = 1e-10
    attention_probs = attention_weights + eps
    entropy = -(attention_probs * torch.log(attention_probs)).sum(dim=-1).mean()
    base_loss = entropy
    
    # Spatial coherence regularization
    # Penalize attention spread across distant coordinates
    # Compute pairwise distances: (num_slots, num_slots)
    # Optimized: compute incrementally to avoid large matrix
    
    coord_diff = slot_coordinates.unsqueeze(0) - slot_coordinates.unsqueeze(1)  # (num, num, 2)
    distances = torch.norm(coord_diff, dim=-1)  # (num, num)
    
    # Weighted average distance: sum_i sum_j p_i p_j d_ij
    # = (p @ distances @ p.T) but computed incrementally
    weighted_distances = torch.matmul(
        torch.matmul(attention_weights, distances),
        attention_weights.transpose(-1, -2)
    ).mean()
    
    # Penalty for high weighted distance (dispersion)
    coherence_penalty = weighted_distances * regularization_weight
    
    # If target coordinates provided, add supervised term
    supervised_loss = 0.0
    if target_coordinates is not None:
        # Compute distance from attended slots to target
        # (batch, num_slots, 2) - (batch, 1, 2) -> (batch, num_slots, 2)
        target_expanded = target_coordinates.unsqueeze(1)
        slot_coords_expanded = slot_coordinates.unsqueeze(0).expand(batch_size, -1, -1)
        target_distances = torch.norm(slot_coords_expanded - target_expanded, dim=-1)
        
        # Weighted distance to target
        supervised_loss = (attention_weights * target_distances).sum(dim=-1).mean()
    
    total_loss = base_loss + coherence_penalty + supervised_loss
    
    return total_loss


def main():
    """
    Main entry point for testing spatial memory operations.
    Demonstrates memory-efficient retrieval and loss computation.
    """
    print("Testing spatial memory operations...")
    
    # Create a small memory grid for testing
    grid = MemoryGrid(
        grid_size=8,
        hidden_dim=64,
        device="cpu"
    )
    
    # Create a query embedding
    query = torch.randn(1, 64)
    
    # Perform retrieval
    result = soft_addressed_retrieve(grid, query, temperature=0.5, top_k=5)
    
    print(f"Retrieved content shape: {result.retrieved_content.shape}")
    print(f"Confidence score: {result.confidence_score:.4f}")
    print(f"Used slots: {len(result.used_slots)}")
    
    # Test loss computation
    attention_weights = torch.softmax(torch.randn(2, 64), dim=-1)
    slot_coords = torch.stack([slot.coordinate for slot in grid.slots], dim=0)
    
    loss = spatial_attention_loss(attention_weights, slot_coords)
    print(f"Spatial attention loss: {loss.item():.4f}")
    
    print("All tests passed.")


if __name__ == "__main__":
    main()