"""
Retrieval strategies for synthesizing LoRA adapters.

This module implements the logic to:
1. Retrieve nearest neighbors from the skill vector database.
2. Synthesize new LoRA adapters via unweighted mean or cosine-weighted averaging.
3. Save the synthesized adapters to disk as safetensors or standard PyTorch state dicts.

It does NOT apply the adapter to a model or run inference (deferred to T026).
"""
import os
import time
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import torch
import torch.nn.functional as F

# Import from local project structure
from ..utils.config import get_project_root, get_config
from ..utils.versioning import compute_artifact_hash

logger = logging.getLogger(__name__)

# Constants
SYNTHESIZED_ADAPTERS_DIR = "artifacts/synthesized_adapters"
SKILL_INDEX_PATH = "data/processed/skill_index.npz"

def load_skill_index() -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load the pre-computed skill index and metadata.

    Returns:
        Tuple of (vectors_array, metadata_dict)
    """
    index_path = os.path.join(get_project_root(), SKILL_INDEX_PATH)
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Skill index not found at {index_path}. "
                                "Run T014 (vector_db.py) first.")

    logger.info(f"Loading skill index from {index_path}")
    data = np.load(index_path, allow_pickle=True)

    # Handle both npz with arrays and dict structures
    if isinstance(data, np.lib.npyio.NpzFile):
        vectors = data['vectors']
        metadata = data['metadata'].item() if 'metadata' in data.files else {}
        data.close()
    else:
        # Fallback if loaded as dict directly
        vectors = data['vectors']
        metadata = data.get('metadata', {})

    return vectors, metadata

def retrieve_neighbors(
    query_vector: np.ndarray,
    vectors: np.ndarray,
    k: int = 3,
    metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve the k nearest neighbors for a given query vector.

    Args:
        query_vector: 1D numpy array of the query embedding.
        vectors: 2D numpy array of stored skill vectors (N, D).
        k: Number of neighbors to retrieve.
        metadata: Optional metadata dict mapping indices to task info.

    Returns:
        List of dicts containing neighbor info (index, similarity, task_id).
    """
    if vectors.ndim != 2:
        raise ValueError(f"Vectors must be 2D (N, D), got {vectors.ndim}")
    if query_vector.ndim != 1:
        query_vector = query_vector.reshape(1, -1)

    # Compute cosine similarity
    # Normalize vectors for cosine similarity
    norm_vectors = F.normalize(torch.tensor(vectors, dtype=torch.float32), p=2, dim=1)
    norm_query = F.normalize(torch.tensor(query_vector, dtype=torch.float32), p=2, dim=1)

    similarities = torch.matmul(norm_query, norm_vectors.T).squeeze()

    # Get top-k indices
    top_k_values, top_k_indices = torch.topk(similarities, k=min(k, len(vectors)))

    results = []
    for i, (idx, sim) in enumerate(zip(top_k_indices, top_k_values)):
        idx = int(idx)
        sim_val = float(sim)
        task_info = {
            "index": idx,
            "similarity": sim_val,
            "task_id": f"unknown_task_{idx}"
        }
        if metadata:
            # Try to map index to task_id
            if 'task_ids' in metadata:
                task_info["task_id"] = metadata['task_ids'][idx]
            elif 'indices' in metadata:
                # Handle case where metadata is a list of dicts
                task_info["task_id"] = metadata['indices'][idx].get('task_id', f"task_{idx}")
        results.append(task_info)

    return results

def synthesize_adapter_unweighted(
    neighbor_indices: List[int],
    a_matrices: Dict[int, np.ndarray],
    b_matrices: Dict[int, np.ndarray]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Synthesize a new adapter by taking the arithmetic mean of the A and B matrices
    of the retrieved neighbors.

    Args:
        neighbor_indices: List of indices of neighbors to combine.
        a_matrices: Dict mapping index -> A matrix (numpy array).
        b_matrices: Dict mapping index -> B matrix (numpy array).

    Returns:
        Tuple of (synthesized_A, synthesized_B) as numpy arrays.
    """
    if not neighbor_indices:
        raise ValueError("No neighbors provided for synthesis.")

    # Validate all matrices have same shape
    first_idx = neighbor_indices[0]
    if first_idx not in a_matrices or first_idx not in b_matrices:
        raise KeyError(f"Index {first_idx} not found in weight matrices.")

    target_shape_a = a_matrices[first_idx].shape
    target_shape_b = b_matrices[first_idx].shape

    # Accumulate sums
    sum_a = np.zeros(target_shape_a, dtype=np.float32)
    sum_b = np.zeros(target_shape_b, dtype=np.float32)

    valid_count = 0
    for idx in neighbor_indices:
        if idx in a_matrices and idx in b_matrices:
            if a_matrices[idx].shape != target_shape_a:
                logger.warning(f"Skipping index {idx}: A matrix shape mismatch. "
                               f"Expected {target_shape_a}, got {a_matrices[idx].shape}")
                continue
            if b_matrices[idx].shape != target_shape_b:
                logger.warning(f"Skipping index {idx}: B matrix shape mismatch. "
                               f"Expected {target_shape_b}, got {b_matrices[idx].shape}")
                continue

            sum_a += a_matrices[idx]
            sum_b += b_matrices[idx]
            valid_count += 1

    if valid_count == 0:
        raise ValueError("No valid matrices found for synthesis.")

    # Compute mean
    mean_a = sum_a / valid_count
    mean_b = sum_b / valid_count

    logger.info(f"Synthesized adapter via unweighted mean of {valid_count} neighbors.")
    return mean_a, mean_b

def synthesize_adapter_cosine_weighted(
    neighbor_indices: List[int],
    similarities: List[float],
    a_matrices: Dict[int, np.ndarray],
    b_matrices: Dict[int, np.ndarray]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Synthesize a new adapter by taking a weighted average of the A and B matrices,
    where weights are the cosine similarities to the query.

    Args:
        neighbor_indices: List of indices of neighbors.
        similarities: List of similarity scores corresponding to the indices.
        a_matrices: Dict mapping index -> A matrix.
        b_matrices: Dict mapping index -> B matrix.

    Returns:
        Tuple of (synthesized_A, synthesized_B).
    """
    if len(neighbor_indices) != len(similarities):
        raise ValueError("Neighbor indices and similarities must have same length.")

    if not neighbor_indices:
        raise ValueError("No neighbors provided for synthesis.")

    # Convert to tensors for weighted sum
    weights = torch.tensor(similarities, dtype=torch.float32)
    weights = F.normalize(weights, p=1, dim=0) # Normalize weights to sum to 1

    first_idx = neighbor_indices[0]
    if first_idx not in a_matrices or first_idx not in b_matrices:
        raise KeyError(f"Index {first_idx} not found in weight matrices.")

    target_shape_a = a_matrices[first_idx].shape
    target_shape_b = b_matrices[first_idx].shape

    # Accumulate weighted sums
    sum_a = np.zeros(target_shape_a, dtype=np.float32)
    sum_b = np.zeros(target_shape_b, dtype=np.float32)
    total_weight = 0.0

    for idx, sim in zip(neighbor_indices, similarities):
        if idx in a_matrices and idx in b_matrices:
            if a_matrices[idx].shape != target_shape_a:
                logger.warning(f"Skipping index {idx}: A matrix shape mismatch.")
                continue
            if b_matrices[idx].shape != target_shape_b:
                logger.warning(f"Skipping index {idx}: B matrix shape mismatch.")
                continue

            weight = float(sim)
            sum_a += a_matrices[idx] * weight
            sum_b += b_matrices[idx] * weight
            total_weight += weight

    if total_weight == 0:
        raise ValueError("Total weight is zero; cannot synthesize.")

    # Normalize by total weight
    mean_a = sum_a / total_weight
    mean_b = sum_b / total_weight

    logger.info(f"Synthesized adapter via cosine-weighted mean (total weight: {total_weight:.4f}).")
    return mean_a, mean_b

def load_lora_weights_from_index(
    metadata: Dict[str, Any],
    index_path: str
) -> Tuple[Dict[int, np.ndarray], Dict[int, np.ndarray]]:
    """
    Load the actual A and B matrices from the disk based on the index metadata.
    This assumes the weights are stored in a structure defined by T012/T013.
    For this implementation, we assume the index file contains the flattened vectors
    and we need to reconstruct the matrices if they aren't stored directly,
    OR the index file has a 'weights' key with the raw arrays.

    Since T013 flattens them, we assume the 'vectors' in the npz are flattened A/B.
    We need to know the original shapes to reconstruct.
    """
    # This is a simplified loader assuming the npz contains 'a_matrices' and 'b_matrices'
    # if they were stored, or we reconstruct from flattened data if shapes are known.
    # Given T013 flattens, we expect the 'vectors' to be the flattened versions.
    # However, for synthesis, we need the matrices.
    # We assume the metadata contains 'shapes' and the 'vectors' are concatenated A|B.
    # Or, more likely, the index generation (T014) stored the flattened vectors
    # and we must reconstruct.

    # Let's assume a standard structure for the npz:
    # 'vectors': (N, D) flattened vectors
    # 'metadata': dict with 'shapes' -> list of (a_shape, b_shape)
    # 'task_ids': list of task names

    # If the index was built by T014, it might have stored the original matrices
    # if memory allowed, or just the flattened vectors.
    # To be robust, we try to load 'a_matrices' and 'b_matrices' first.
    # If not present, we reconstruct from 'vectors' and 'shapes'.

    data = np.load(index_path, allow_pickle=True)

    if 'a_matrices' in data.files and 'b_matrices' in data.files:
        # Direct storage
        a_list = data['a_matrices']
        b_list = data['b_matrices']
        a_dict = {i: arr for i, arr in enumerate(a_list)}
        b_dict = {i: arr for i, arr in enumerate(b_list)}
    else:
        # Reconstruction from flattened vectors
        if 'vectors' not in data.files or 'shapes' not in data.files:
            raise ValueError("Index file missing required 'vectors' and 'shapes' for reconstruction.")

        vectors = data['vectors']
        shapes = data['shapes'] # List of tuples (a_shape, b_shape)

        a_dict = {}
        b_dict = {}

        for i, (a_shape, b_shape) in enumerate(shapes):
            if i >= len(vectors):
                break
            flat_vec = vectors[i]
            total_size = a_shape[0] * a_shape[1] + b_shape[0] * b_shape[1]
            if flat_vec.size != total_size:
                raise ValueError(f"Vector size mismatch at index {i}: expected {total_size}, got {flat_vec.size}")

            a_flat = flat_vec[:a_shape[0] * a_shape[1]]
            b_flat = flat_vec[a_shape[0] * a_shape[1]:]

            a_dict[i] = a_flat.reshape(a_shape)
            b_dict[i] = b_flat.reshape(b_shape)

    return a_dict, b_dict

def save_synthesized_adapter(
    a_matrix: np.ndarray,
    b_matrix: np.ndarray,
    output_path: str,
    query_info: Dict[str, Any]
) -> str:
    """
    Save the synthesized A and B matrices to disk.

    Args:
        a_matrix: The synthesized A matrix.
        b_matrix: The synthesized B matrix.
        output_path: Full path to save the file.
        query_info: Metadata about the query (task, k, strategy, etc.).

    Returns:
        The path to the saved file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Prepare state dict
    state_dict = {
        "lora_A.weight": torch.tensor(a_matrix, dtype=torch.float32),
        "lora_B.weight": torch.tensor(b_matrix, dtype=torch.float32),
        "metadata": query_info
    }

    # Save as .safetensors if available, else .pt
    try:
        from safetensors.torch import save_file
        safe_path = output_path.replace(".pt", ".safetensors")
        save_file(state_dict, safe_path)
        logger.info(f"Saved synthesized adapter to {safe_path}")
        return safe_path
    except ImportError:
        logger.warning("safetensors not available, falling back to torch.save")
        torch.save(state_dict, output_path)
        logger.info(f"Saved synthesized adapter to {output_path}")
        return output_path

def execute_synthesis(
    query_vector: np.ndarray,
    k: int = 3,
    strategy: str = "unweighted",
    query_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main entry point to execute the synthesis pipeline.

    1. Load index.
    2. Retrieve neighbors.
    3. Load weights for neighbors.
    4. Synthesize.
    5. Save to disk.

    Args:
        query_vector: 1D numpy array.
        k: Number of neighbors.
        strategy: "unweighted" or "cosine_weighted".
        query_metadata: Optional dict with query info (e.g., task_id).

    Returns:
        Dict containing paths, stats, and metadata.
    """
    start_time = time.time()

    # 1. Load Index
    vectors, index_metadata = load_skill_index()

    # 2. Retrieve Neighbors
    neighbors = retrieve_neighbors(query_vector, vectors, k, index_metadata)
    if not neighbors:
        raise ValueError("No neighbors found for query.")

    neighbor_indices = [n["index"] for n in neighbors]
    similarities = [n["similarity"] for n in neighbors]

    # 3. Load Weights
    a_matrices, b_matrices = load_lora_weights_from_index(index_metadata, 
                                                          os.path.join(get_project_root(), SKILL_INDEX_PATH))

    # 4. Synthesize
    if strategy == "unweighted":
        syn_a, syn_b = synthesize_adapter_unweighted(neighbor_indices, a_matrices, b_matrices)
    elif strategy == "cosine_weighted":
        syn_a, syn_b = synthesize_adapter_cosine_weighted(
            neighbor_indices, similarities, a_matrices, b_matrices
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    # 5. Save
    query_id = query_metadata.get("task_id", f"query_{int(time.time())}")
    filename = f"{query_id}_{strategy}_k{k}.pt"
    output_path = os.path.join(get_project_root(), SYNTHESIZED_ADAPTERS_DIR, filename)

    save_info = {
        "query_id": query_id,
        "strategy": strategy,
        "k": k,
        "neighbors": neighbor_indices,
        "similarities": similarities,
        "synthesis_time": time.time() - start_time,
        "output_path": output_path
    }

    save_synthesized_adapter(syn_a, syn_b, output_path, save_info)

    return save_info