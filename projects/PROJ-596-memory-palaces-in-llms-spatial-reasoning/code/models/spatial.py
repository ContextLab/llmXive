"""
Spatial memory module implementing soft-addressed retrieval via cosine similarity.

This module provides the core mathematical operations for the Memory Palace architecture,
specifically the calculation of similarity between query vectors and memory slot coordinates
to enable soft-addressed retrieval of episodic content.

Addresses FR-002: Soft-addressed retrieval using cosine similarity.
"""
import torch
import math
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

from models.memory_slot import MemorySlot, MemoryGrid
from models.episodic_chunk import EpisodicChunk


@dataclass
class RetrievalResult:
    """
    Result of a soft-addressed retrieval operation.
    
    Attributes:
        retrieved_chunks: List of EpisodicChunk objects retrieved, weighted by similarity.
        similarity_scores: Tensor of raw cosine similarity scores for each slot.
        normalized_weights: Tensor of softmax-normalized weights used for retrieval.
        top_k_indices: Indices of the top-k most similar slots.
    """
    retrieved_chunks: List[EpisodicChunk]
    similarity_scores: torch.Tensor
    normalized_weights: torch.Tensor
    top_k_indices: torch.Tensor


def compute_cosine_similarity(
    query: torch.Tensor,
    keys: torch.Tensor,
    epsilon: float = 1e-8
) -> torch.Tensor:
    """
    Compute cosine similarity between a query vector and a set of key vectors.
    
    This implements the soft-addressing mechanism for the memory palace. The query
    represents the current context or retrieval cue, and keys represent the spatial
    coordinates or content embeddings of memory slots.
    
    Args:
        query: Query tensor of shape (d,) or (1, d).
        keys: Key tensor of shape (n, d) where n is the number of slots.
        epsilon: Small constant for numerical stability in division.
    
    Returns:
        Tensor of shape (n,) containing cosine similarity scores.
    
    Raises:
        ValueError: If input dimensions are incompatible.
    """
    if query.dim() == 1:
        query = query.unsqueeze(0)
    
    if keys.dim() != 2:
        raise ValueError(f"Keys must be 2D tensor, got {keys.dim()}D")
    
    if query.shape[-1] != keys.shape[-1]:
        raise ValueError(
            f"Query and keys dimension mismatch: {query.shape[-1]} vs {keys.shape[-1]}"
        )
    
    # Normalize vectors
    query_norm = torch.norm(query, p=2, dim=-1, keepdim=True)
    keys_norm = torch.norm(keys, p=2, dim=-1, keepdim=True)
    
    query_normalized = query / (query_norm + epsilon)
    keys_normalized = keys / (keys_norm + epsilon)
    
    # Compute dot product for cosine similarity
    similarity = torch.matmul(query_normalized, keys_normalized.transpose(0, 1))
    
    return similarity.squeeze(0)


def soft_addressed_retrieve(
    memory_grid: MemoryGrid,
    query_vector: torch.Tensor,
    temperature: float = 1.0,
    top_k: Optional[int] = None,
    chunk_threshold: float = 0.0
) -> RetrievalResult:
    """
    Perform soft-addressed retrieval from the memory grid.
    
    This function computes the similarity between a query vector and all memory slots,
    normalizes the similarities using softmax (with temperature), and retrieves the
    associated episodic chunks weighted by these similarities.
    
    Args:
        memory_grid: The MemoryGrid containing slots with coordinates and chunks.
        query_vector: Tensor of shape (d,) representing the retrieval cue.
        temperature: Temperature parameter for softmax normalization. Higher values
                    make the distribution more uniform, lower values make it sharper.
        top_k: If provided, only consider the top-k most similar slots for retrieval.
        chunk_threshold: Minimum absolute similarity score required to include a chunk.
                       Chunks with similarity below this threshold are excluded.
    
    Returns:
        RetrievalResult containing retrieved chunks and associated metadata.
    """
    if not memory_grid.slots:
        return RetrievalResult(
            retrieved_chunks=[],
            similarity_scores=torch.tensor([]),
            normalized_weights=torch.tensor([]),
            top_k_indices=torch.tensor([])
        )
    
    # Extract coordinates from slots
    coordinates = torch.stack([slot.coordinate for slot in memory_grid.slots])
    
    # Compute cosine similarity
    similarity_scores = compute_cosine_similarity(query_vector, coordinates)
    
    # Apply top-k filtering if requested
    if top_k is not None and top_k < len(similarity_scores):
        _, top_k_indices = torch.topk(similarity_scores, top_k)
        similarity_scores = similarity_scores[top_k_indices]
    else:
        top_k_indices = torch.arange(len(similarity_scores))
    
    # Apply threshold filtering
    mask = similarity_scores.abs() >= chunk_threshold
    similarity_scores = similarity_scores[mask]
    top_k_indices = top_k_indices[mask]
    
    if len(similarity_scores) == 0:
        return RetrievalResult(
            retrieved_chunks=[],
            similarity_scores=torch.tensor([]),
            normalized_weights=torch.tensor([]),
            top_k_indices=torch.tensor([])
        )
    
    # Normalize with softmax and temperature
    weights = torch.softmax(similarity_scores / temperature, dim=0)
    
    # Retrieve associated chunks
    retrieved_chunks = []
    for idx in top_k_indices.tolist():
        slot = memory_grid.slots[idx]
        if slot.chunk is not None:
            retrieved_chunks.append(slot.chunk)
    
    return RetrievalResult(
        retrieved_chunks=retrieved_chunks,
        similarity_scores=similarity_scores,
        normalized_weights=weights,
        top_k_indices=top_k_indices
    )


def weighted_chunk_aggregation(
    retrieval_result: RetrievalResult,
    aggregation_fn: Optional[callable] = None
) -> torch.Tensor:
    """
    Aggregate retrieved chunk embeddings using weighted sum.
    
    Args:
        retrieval_result: Result from soft_addressed_retrieve.
        aggregation_fn: Optional custom aggregation function. If None, uses weighted sum.
    
    Returns:
        Aggregated embedding tensor.
    """
    if not retrieval_result.retrieved_chunks:
        return torch.tensor([])
    
    # Extract embeddings from chunks (assuming they have an 'embedding' attribute)
    embeddings = []
    weights = retrieval_result.normalized_weights
    
    for i, chunk in enumerate(retrieval_result.retrieved_chunks):
        if hasattr(chunk, 'embedding') and chunk.embedding is not None:
            embeddings.append(chunk.embedding)
    
    if not embeddings:
        return torch.tensor([])
    
    embeddings_tensor = torch.stack(embeddings)
    
    if aggregation_fn is None:
        # Weighted sum
        weights_expanded = weights.unsqueeze(1)
        aggregated = torch.sum(embeddings_tensor * weights_expanded, dim=0)
    else:
        aggregated = aggregation_fn(embeddings_tensor, weights)
    
    return aggregated


def spatial_attention_loss(
    query_vector: torch.Tensor,
    memory_grid: MemoryGrid,
    target_slot_index: int,
    temperature: float = 1.0
) -> torch.Tensor:
    """
    Compute a loss function to encourage attention to a specific target slot.
    
    This loss is used during training to teach the model to direct its spatial
    attention to the correct memory location for a given query.
    
    Args:
        query_vector: Query tensor of shape (d,).
        memory_grid: MemoryGrid containing the target slot.
        target_slot_index: Index of the target slot that should receive highest attention.
        temperature: Temperature for softmax normalization.
    
    Returns:
        Scalar tensor representing the cross-entropy loss.
    """
    if target_slot_index >= len(memory_grid.slots) or target_slot_index < 0:
        raise ValueError(f"Target slot index {target_slot_index} out of bounds")
    
    coordinates = torch.stack([slot.coordinate for slot in memory_grid.slots])
    similarity_scores = compute_cosine_similarity(query_vector, coordinates)
    
    # Apply softmax to get attention distribution
    attention_weights = torch.softmax(similarity_scores / temperature, dim=0)
    
    # Compute cross-entropy loss against one-hot target
    target_weights = torch.zeros_like(attention_weights)
    target_weights[target_slot_index] = 1.0
    
    # Avoid log(0)
    epsilon = 1e-8
    loss = -torch.sum(target_weights * torch.log(attention_weights + epsilon))
    
    return loss


def main():
    """
    Demonstration of spatial memory retrieval functionality.
    
    This function creates a sample memory grid, performs soft-addressed retrieval,
    and prints the results.
    """
    print("Initializing spatial memory demonstration...")
    
    # Create a sample memory grid
    grid = MemoryGrid(grid_size=5)
    
    # Add some sample slots with coordinates
    sample_coords = [
        torch.tensor([1.0, 2.0, 0.5]),
        torch.tensor([3.0, 1.0, 2.0]),
        torch.tensor([2.0, 3.0, 1.5]),
        torch.tensor([4.0, 4.0, 3.0]),
        torch.tensor([0.5, 0.5, 0.5])
    ]
    
    for i, coord in enumerate(sample_coords):
        # Normalize coordinate
        coord = coord / torch.norm(coord)
        grid.add_slot(coord, EpisodicChunk(content=f"Sample content {i}"))
    
    # Create a query vector
    query = torch.tensor([2.5, 2.5, 1.0])
    query = query / torch.norm(query)
    
    # Perform retrieval
    result = soft_addressed_retrieve(grid, query, temperature=0.5, top_k=3)
    
    print(f"\nQuery vector: {query.tolist()}")
    print(f"Retrieved {len(result.retrieved_chunks)} chunks")
    print(f"Similarity scores: {result.similarity_scores.tolist()}")
    print(f"Normalized weights: {result.normalized_weights.tolist()}")
    print(f"Top-k indices: {result.top_k_indices.tolist()}")
    
    for i, chunk in enumerate(result.retrieved_chunks):
        print(f"  Chunk {i}: {chunk.content} (weight: {result.normalized_weights[i].item():.4f})")
    
    # Test weighted aggregation
    aggregated = weighted_chunk_aggregation(result)
    print(f"\nAggregated embedding shape: {aggregated.shape if aggregated.numel() > 0 else 'empty'}")
    
    # Test attention loss
    loss = spatial_attention_loss(query, grid, target_slot_index=2)
    print(f"Attention loss for target slot 2: {loss.item():.4f}")
    
    print("\nSpatial memory demonstration complete.")

if __name__ == "__main__":
    main()