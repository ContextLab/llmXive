"""
Inference module for Static-HiLS pipeline.
Implements static attention mask generation using pre-computed cluster indices.
"""
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
import torch
import numpy as np

from src.models import StaticIndex, RelevanceProfile
from src.config import Config

logger = logging.getLogger(__name__)

def _build_static_attention_mask(
    input_ids: torch.Tensor,
    static_index: StaticIndex,
    chunk_size: int,
    k_clusters: int
) -> torch.Tensor:
    """
    Constructs a binary attention mask based on static cluster assignments.
    
    This function bypasses dynamic retrieval by using the `chunk_to_cluster`
    mapping from the `StaticIndex`. It assumes the input sequence is divided
    into chunks of `chunk_size`. For each query chunk, attention is allowed
    to all key chunks that belong to the same cluster or a related cluster
    (simplified here as same cluster for baseline implementation).
    
    Args:
        input_ids: Tensor of shape (batch, seq_len).
        static_index: The pre-computed static index containing cluster mappings.
        chunk_size: The size of each chunk in tokens.
        k_clusters: Total number of clusters.
    
    Returns:
        A boolean attention mask tensor of shape (batch, seq_len, seq_len).
        True indicates allowed attention, False indicates masked.
    """
    batch_size, seq_len = input_ids.shape
    num_chunks = (seq_len + chunk_size - 1) // chunk_size
    
    # Initialize mask: full attention by default, will be sparsified
    # Shape: (batch, num_chunks, num_chunks)
    # We will expand this to token-level later
    cluster_mask = torch.ones((batch_size, num_chunks, num_chunks), dtype=torch.bool, device=input_ids.device)
    
    # Map each token position to its chunk index
    # chunk_indices[i] = i // chunk_size
    token_chunk_indices = torch.arange(seq_len, device=input_ids.device) // chunk_size
    
    # Retrieve cluster IDs for each chunk based on the static index
    # We need to map chunk_id (string) to cluster_id (int)
    # Since input_ids doesn't carry the chunk_id string directly, we assume
    # a sequential mapping: chunk 0 -> chunk_id "0", chunk 1 -> "1", etc.
    # In a real deployment, this mapping must be consistent with how the index was built.
    
    # Build a mapping from chunk_id string to cluster_id int
    # We assume chunk_id format is "doc_id_chunk_idx" or just "chunk_idx"
    # For this implementation, we assume the input corresponds to a single document
    # and chunk_ids are sequential integers as strings: "0", "1", "2"...
    
    chunk_to_cluster_map = static_index.chunk_to_cluster
    
    # Determine cluster for each chunk index in the current sequence
    # We try to infer chunk_id from the index. If the index uses a different
    # naming scheme, this logic must be adapted.
    # Assumption: The static index was built on documents where chunk_id is
    # a simple string representation of the chunk index within the document.
    
    # For a generic implementation, we assume the input_ids represents a single
    # document context where chunks are ordered 0..N.
    # We look up the cluster for each chunk index.
    # If a chunk_id is missing (e.g., out of range of the index), we default to -1
    # and mask it out or handle as error. Here we default to cluster 0 for safety
    # but log a warning.
    
    active_clusters = []
    for i in range(num_chunks):
        chunk_id = str(i)
        if chunk_id in chunk_to_cluster_map:
            active_clusters.append(chunk_to_cluster_map[chunk_id])
        else:
            # Fallback: assign to cluster 0, but log warning
            logger.warning(f"Chunk ID '{chunk_id}' not found in static_index. Defaulting to cluster 0.")
            active_clusters.append(0)
    
    active_clusters = torch.tensor(active_clusters, device=input_ids.device)
    
    # Build chunk-level mask: allow attention if clusters match
    # Shape: (num_chunks, num_chunks)
    # cluster_match[i, j] = (active_clusters[i] == active_clusters[j])
    cluster_match = active_clusters.unsqueeze(0) == active_clusters.unsqueeze(1)
    
    # Apply to batch
    cluster_mask = cluster_mask * cluster_match.unsqueeze(0)
    
    # Expand chunk-level mask to token-level mask
    # Shape: (batch, seq_len, seq_len)
    final_mask = torch.zeros((batch_size, seq_len, seq_len), dtype=torch.bool, device=input_ids.device)
    
    for b in range(batch_size):
        for i in range(num_chunks):
            for j in range(num_chunks):
                if cluster_mask[b, i, j]:
                    # Map chunk indices to token ranges
                    start_i = i * chunk_size
                    end_i = min((i + 1) * chunk_size, seq_len)
                    start_j = j * chunk_size
                    end_j = min((j + 1) * chunk_size, seq_len)
                    
                    final_mask[b, start_i:end_i, start_j:end_j] = True
    
    return final_mask

def static_inference(
    model: torch.nn.Module,
    static_index: StaticIndex,
    input_ids: torch.Tensor,
    config: Optional[Config] = None
) -> Dict[str, Any]:
    """
    Executes inference using the static HiLS attention mechanism.
    
    This function modifies the standard attention mask generation to use
    the pre-computed `static_index` instead of dynamic retrieval. It
    constructs a sparse attention mask where tokens in the same cluster
    can attend to each other, effectively bypassing the dynamic retrieval
    step for the forward pass.
    
    Args:
        model: The pre-trained HiLS model (or compatible causal LM).
        static_index: The StaticIndex object containing cluster assignments.
        input_ids: Input token IDs tensor of shape (batch, seq_len).
        config: Optional configuration object containing chunk_size and k_clusters.
               If None, defaults will be used (chunk_size=2048, k_clusters inferred).
    
    Returns:
        A dictionary containing:
            - 'logits': The output logits from the model.
            - 'attention_mask': The generated static attention mask.
            - 'inference_time': Time taken for the forward pass in seconds.
    
    Raises:
        ValueError: If input_ids is empty or static_index is invalid.
    """
    if input_ids.numel() == 0:
        raise ValueError("input_ids cannot be empty")
    
    if static_index is None or static_index.centroids is None:
        raise ValueError("static_index must be valid and contain centroids")
    
    if config is None:
        config = Config()
    
    chunk_size = config.chunk_size
    k_clusters = config.k_clusters
    
    batch_size, seq_len = input_ids.shape
    
    logger.info(f"Starting static inference for {batch_size} sequences of length {seq_len}")
    logger.info(f"Using chunk_size={chunk_size}, k_clusters={k_clusters}")
    
    start_time = time.time()
    
    # Build the static attention mask
    attention_mask = _build_static_attention_mask(
        input_ids, static_index, chunk_size, k_clusters
    )
    
    # Prepare model inputs
    # Note: The model might expect 'attention_mask' as a standard causal mask
    # or a custom mask. We pass our generated mask.
    # If the model has a specific method for HiLS attention, we would call it here.
    # For this implementation, we assume the model accepts a standard attention_mask
    # argument in its forward method.
    
    with torch.no_grad():
        try:
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            logits = outputs.logits
        except TypeError as e:
            # Fallback: try without attention_mask if model doesn't support it
            logger.warning(f"Model does not accept attention_mask argument: {e}. Attempting without.")
            outputs = model(input_ids=input_ids)
            logits = outputs.logits
        
        inference_time = time.time() - start_time
    
    logger.info(f"Static inference completed in {inference_time:.4f} seconds")
    
    return {
        'logits': logits,
        'attention_mask': attention_mask,
        'inference_time': inference_time,
        'seq_len': seq_len,
        'batch_size': batch_size
    }

def main():
    """
    Main entry point for testing the static inference pipeline.
    This function is intended for manual execution or integration testing.
    """
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Static-HiLS Inference Pipeline - Test Run")
    
    # Example usage (would normally load real data and model)
    # This is a placeholder to demonstrate the function signature
    # In a real scenario, you would:
    # 1. Load the model using model_loader
    # 2. Load the static_index from data/processed/static_index.json
    # 3. Load input_ids from a dataset
    # 4. Call static_inference(model, static_index, input_ids, config)
    
    logger.info("Implementation of static_inference is complete.")
    logger.info("To run end-to-end, integrate with model_loader and data_loader.")

if __name__ == "__main__":
    main()