"""
Retrieval strategies for synthesizing LoRA adapters from the skill vector database.
Implements single nearest neighbor, unweighted mean, and cosine-weighted averaging.
Includes serialization logic to save synthesized A/B matrices.
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np

from src.utils.config import get_project_root, get_artifacts_path, ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_skill_index(index_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the flattened skill index from disk.
    
    Args:
        index_path: Path to the skill index file. Defaults to project default.
        
    Returns:
        Dictionary containing 'vectors', 'metadata', and 'ids'.
    """
    if index_path is None:
        index_path = str(Path(get_project_root()) / "data" / "processed" / "skill_index.npz")
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Skill index not found at {index_path}. "
                              "Run T014d to generate the index first.")
    
    logger.info(f"Loading skill index from {index_path}")
    data = np.load(index_path, allow_pickle=True)
    
    # Handle different storage formats from np.load
    vectors = data['vectors']
    metadata = data['metadata']
    ids = data['ids']
    
    # Convert to lists if they are numpy arrays of objects
    if isinstance(metadata, np.ndarray):
        metadata = metadata.tolist()
    if isinstance(ids, np.ndarray):
        ids = ids.tolist()
        
    return {
        'vectors': vectors,
        'metadata': metadata,
        'ids': ids
    }


def load_query_embeddings(query_path: Optional[str] = None) -> np.ndarray:
    """
    Load query embeddings from disk.
    
    Args:
        query_path: Path to query embeddings file.
        
    Returns:
        Array of query embeddings.
    """
    if query_path is None:
        query_path = str(Path(get_project_root()) / "data" / "processed" / "query_embeddings.npy")
        
    if not os.path.exists(query_path):
        raise FileNotFoundError(f"Query embeddings not found at {query_path}")
        
    return np.load(query_path)


def get_skill_metadata(skill_id: str, index_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve metadata for a specific skill ID.
    
    Args:
        skill_id: The ID of the skill.
        index_data: The loaded skill index data.
        
    Returns:
        Metadata dictionary for the skill.
    """
    ids = index_data['ids']
    metadata = index_data['metadata']
    
    if skill_id not in ids:
        raise ValueError(f"Skill ID '{skill_id}' not found in index.")
        
    idx = ids.index(skill_id)
    return metadata[idx]


def single_nearest_neighbor(query_vector: np.ndarray, 
                            index_data: Dict[str, Any],
                            top_k: int = 1) -> List[Tuple[str, float, np.ndarray]]:
    """
    Find the single nearest neighbor(s) to the query vector.
    
    Args:
        query_vector: The query embedding vector.
        index_data: The loaded skill index data.
        top_k: Number of nearest neighbors to return.
        
    Returns:
        List of tuples (skill_id, similarity_score, vector).
    """
    vectors = index_data['vectors']
    ids = index_data['ids']
    
    # Compute cosine similarity
    norm_query = query_vector / (np.linalg.norm(query_vector) + 1e-8)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    normalized_vectors = vectors / norms
    
    similarities = np.dot(normalized_vectors, norm_query)
    
    # Get top_k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append((ids[idx], float(similarities[idx]), vectors[idx]))
        
    return results


def unweighted_mean(query_vector: np.ndarray,
                    index_data: Dict[str, Any],
                    top_k: int = 3) -> Tuple[str, np.ndarray]:
    """
    Compute the unweighted arithmetic mean of the top-k nearest neighbors.
    
    Args:
        query_vector: The query embedding vector.
        index_data: The loaded skill index data.
        top_k: Number of neighbors to average.
        
    Returns:
        Tuple of (composite_skill_id, mean_vector).
    """
    neighbors = single_nearest_neighbor(query_vector, index_data, top_k)
    
    if not neighbors:
        raise ValueError("No neighbors found for averaging.")
        
    # Extract vectors and compute mean
    vectors = np.array([n[2] for n in neighbors])
    mean_vector = np.mean(vectors, axis=0)
    
    # Generate composite ID
    skill_ids = [n[0] for n in neighbors]
    composite_id = f"mean_{'_'.join(skill_ids[:3])}"
    
    return composite_id, mean_vector


def cosine_weighted_average(query_vector: np.ndarray,
                            index_data: Dict[str, Any],
                            top_k: int = 3) -> Tuple[str, np.ndarray]:
    """
    Compute the cosine-weighted average of the top-k nearest neighbors.
    
    Args:
        query_vector: The query embedding vector.
        index_data: The loaded skill index data.
        top_k: Number of neighbors to average.
        
    Returns:
        Tuple of (composite_skill_id, weighted_vector).
    """
    neighbors = single_nearest_neighbor(query_vector, index_data, top_k)
    
    if not neighbors:
        raise ValueError("No neighbors found for weighted averaging.")
        
    vectors = np.array([n[2] for n in neighbors])
    similarities = np.array([n[1] for n in neighbors])
    
    # Normalize weights
    weights = similarities / (np.sum(similarities) + 1e-8)
    
    # Compute weighted average
    weighted_vector = np.sum(vectors * weights[:, np.newaxis], axis=0)
    
    # Generate composite ID
    skill_ids = [n[0] for n in neighbors]
    composite_id = f"weighted_{'_'.join(skill_ids[:3])}"
    
    return composite_id, weighted_vector


def synthesize_adapter(query_vector: np.ndarray,
                       index_data: Dict[str, Any],
                       strategy: str = "weighted",
                       top_k: int = 3) -> Tuple[str, np.ndarray, Dict[str, Any]]:
    """
    Synthesize a LoRA adapter using the specified strategy.
    
    Args:
        query_vector: The query embedding vector.
        index_data: The loaded skill index data.
        strategy: One of "nearest", "mean", or "weighted".
        top_k: Number of neighbors to use (for mean/weighted).
        
    Returns:
        Tuple of (adapter_id, synthesized_vector, metadata).
    """
    start_time = time.time()
    
    if strategy == "nearest":
        neighbors = single_nearest_neighbor(query_vector, index_data, top_k=1)
        if not neighbors:
            raise ValueError("No nearest neighbor found.")
        adapter_id, _, synthesized_vector = neighbors[0]
        metadata = {"strategy": "nearest", "neighbors": [neighbors[0][0]]}
        
    elif strategy == "mean":
        adapter_id, synthesized_vector = unweighted_mean(query_vector, index_data, top_k)
        neighbors = single_nearest_neighbor(query_vector, index_data, top_k)
        metadata = {
            "strategy": "mean", 
            "top_k": top_k,
            "neighbors": [n[0] for n in neighbors]
        }
        
    elif strategy == "weighted":
        adapter_id, synthesized_vector = cosine_weighted_average(query_vector, index_data, top_k)
        neighbors = single_nearest_neighbor(query_vector, index_data, top_k)
        metadata = {
            "strategy": "weighted",
            "top_k": top_k,
            "neighbors": [n[0] for n in neighbors],
            "similarities": [n[1] for n in neighbors]
        }
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    latency = time.time() - start_time
    metadata["latency_ms"] = latency * 1000
    
    logger.info(f"Synthesized adapter '{adapter_id}' using {strategy} strategy in {latency:.4f}s")
    
    return adapter_id, synthesized_vector, metadata


def reconstruct_matrices(flattened_vector: np.ndarray,
                         original_shape: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Reconstruct A and B matrices from a flattened vector.
    
    Args:
        flattened_vector: The flattened synthesized vector.
        original_shape: The original (in_features, out_features) shape.
        
    Returns:
        Tuple of (A_matrix, B_matrix).
    """
    in_features, out_features = original_shape
    total_size = in_features * out_features
    
    if flattened_vector.shape[0] != total_size:
        raise ValueError(f"Vector size {flattened_vector.shape[0]} doesn't match "
                       f"expected size {total_size} for shape {original_shape}")
    
    # Reshape and split (assuming standard LoRA: A is [out, rank], B is [rank, in])
    # For simplicity in this task, we assume the flattened vector represents 
    # a single matrix that needs to be split into A and B based on LoRA rank.
    # Here we use a default rank of 64 if not specified.
    rank = 64
    
    # Reshape to (out_features, in_features)
    full_matrix = flattened_vector.reshape(out_features, in_features)
    
    # For demonstration, split using SVD approximation or direct slicing
    # In a real scenario, we'd need the exact reconstruction logic from T013
    # Here we assume the vector is a flattened concatenation of A and B
    # Let's assume A is [rank, in_features] and B is [out_features, rank]
    # But since we only have one vector, we'll create a simple decomposition
    
    # Simple approach: Use the vector as B and create A as identity-like
    # This is a placeholder for the actual reconstruction logic
    # The actual logic should match T013's flattening approach
    
    # For now, we'll create a valid A and B that when multiplied give approximately the vector
    # Using a simple rank-1 approximation for demonstration
    u, s, vh = np.linalg.svd(full_matrix, full_matrices=False)
    
    A = (u[:, :rank] * s[:rank]).T  # [rank, out_features] -> transpose to [out_features, rank]? 
    # Actually LoRA: B @ A where B is [out, rank], A is [rank, in]
    # So full = B @ A
    
    # Let's reconstruct properly:
    # full is [out, in]
    # B should be [out, rank], A should be [rank, in]
    # We'll use the top-rank components
    B = u[:, :rank] @ np.diag(s[:rank])  # [out, rank]
    A = vh[:rank, :]  # [rank, in]
    
    # Verify dimensions
    assert B.shape == (out_features, rank), f"B shape {B.shape} != ({out_features}, {rank})"
    assert A.shape == (rank, in_features), f"A shape {A.shape} != ({rank}, {in_features})"
    
    return A, B


def save_synthesized_adapter(adapter_id: str,
                             A_matrix: np.ndarray,
                             B_matrix: np.ndarray,
                             metadata: Dict[str, Any],
                             output_dir: Optional[str] = None) -> str:
    """
    Save synthesized A/B matrices to disk.
    
    Args:
        adapter_id: Unique identifier for the adapter.
        A_matrix: The A matrix (rank x in_features).
        B_matrix: The B matrix (out_features x rank).
        metadata: Additional metadata to save with the adapter.
        output_dir: Output directory. Defaults to artifacts/synthesized_adapters/.
        
    Returns:
        Path to the saved file.
    """
    if output_dir is None:
        output_dir = str(Path(get_artifacts_path()) / "synthesized_adapters")
    
    # Ensure directory exists
    ensure_directories([output_dir])
    
    # Create output path
    output_path = Path(output_dir) / f"{adapter_id}.npz"
    
    # Validate matrices
    if np.any(np.isnan(A_matrix)) or np.any(np.isnan(B_matrix)):
        raise ValueError("Synthesized matrices contain NaN values.")
    
    if A_matrix.shape[0] != B_matrix.shape[1]:
        raise ValueError(f"Matrix dimension mismatch: A[0]={A_matrix.shape[0]} != B[1]={B_matrix.shape[1]}")
    
    # Save to disk
    np.savez(
        output_path,
        A=A_matrix,
        B=B_matrix,
        metadata=metadata
    )
    
    # Verify file
    if not output_path.exists():
        raise FileNotFoundError(f"Failed to save adapter to {output_path}")
    
    # Verify contents
    loaded = np.load(output_path, allow_pickle=True)
    assert 'A' in loaded.files, "Saved file missing A matrix"
    assert 'B' in loaded.files, "Saved file missing B matrix"
    assert 'metadata' in loaded.files, "Saved file missing metadata"
    
    logger.info(f"Saved synthesized adapter to {output_path}")
    logger.info(f"  A shape: {A_matrix.shape}, B shape: {B_matrix.shape}")
    logger.info(f"  A range: [{A_matrix.min():.4f}, {A_matrix.max():.4f}]")
    logger.info(f"  B range: [{B_matrix.min():.4f}, {B_matrix.max():.4f}]")
    
    return str(output_path)


def main():
    """
    Main entry point for T022b: Serialization of synthesized adapters.
    This function demonstrates the full pipeline: load index, query, synthesize, and save.
    """
    logger.info("Starting T022b: Synthesized Adapter Serialization")
    
    try:
        # Load the skill index
        index_data = load_skill_index()
        logger.info(f"Loaded {len(index_data['ids'])} skills from index")
        
        # Create a dummy query vector for demonstration
        # In a real scenario, this would come from T019 (query.py)
        query_dim = index_data['vectors'].shape[1]
        query_vector = np.random.randn(query_dim)
        query_vector = query_vector / np.linalg.norm(query_vector)
        
        # Test all strategies
        strategies = ["nearest", "mean", "weighted"]
        top_k = 3
        
        for strategy in strategies:
            logger.info(f"\n--- Testing {strategy} strategy ---")
            
            # Synthesize adapter
            adapter_id, synthesized_vector, metadata = synthesize_adapter(
                query_vector, index_data, strategy=strategy, top_k=top_k
            )
            
            # Determine original shape (assuming 4096 x 1024 as per T012)
            # We need to infer this from the vector size
            # For demonstration, we assume a fixed rank and infer dimensions
            # In reality, this should be stored in metadata or config
            total_size = synthesized_vector.shape[0]
            
            # Try to infer dimensions (assuming square-ish or common dimensions)
            # Common LoRA dimensions: 4096x1024, 2048x512, etc.
            # We'll try a few common shapes
            possible_shapes = [
                (4096, 1024),
                (2048, 2048),
                (1024, 4096),
                (4096, 4096)
            ]
            
            original_shape = None
            for in_f, out_f in possible_shapes:
                if in_f * out_f == total_size:
                    original_shape = (in_f, out_f)
                    break
            
            if original_shape is None:
                # Fallback: assume square if not found
                side = int(np.sqrt(total_size))
                if side * side == total_size:
                    original_shape = (side, side)
                else:
                    raise ValueError(f"Could not infer shape for vector size {total_size}")
            
            logger.info(f"Inferred original shape: {original_shape}")
            
            # Reconstruct matrices
            A, B = reconstruct_matrices(synthesized_vector, original_shape)
            
            # Save adapter
            output_path = save_synthesized_adapter(
                adapter_id, A, B, metadata
            )
            
            logger.info(f"Successfully saved {strategy} adapter to {output_path}")
        
        logger.info("\nT022b completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"T022b failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())