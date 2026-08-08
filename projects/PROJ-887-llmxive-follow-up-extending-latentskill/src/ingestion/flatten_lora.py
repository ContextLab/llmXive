"""
Ingestion module for flattening LoRA weights into normalized skill vectors.

This module implements FR-001: Load A/B matrices from LoRA adapters,
flatten them to 1D, apply L2 normalization, and validate dimensions.
It also implements T016: Logging for ingestion metrics.
"""

import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import yaml

from ..utils.config import get_project_root, load_config

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_lora_weights(adapter_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load LoRA A and B matrices from a saved adapter directory.

    Args:
        adapter_path: Path to the adapter directory containing 'adapter_model.safetensors'
                      or 'adapter_model.bin'.

    Returns:
        Tuple of (A_matrix, B_matrix) as numpy arrays.
    """
    logger.info(f"Loading weights from: {adapter_path}")
    
    # Try safetensors first (preferred), then bin
    safe_path = os.path.join(adapter_path, "adapter_model.safetensors")
    bin_path = os.path.join(adapter_path, "adapter_model.bin")
    
    if os.path.exists(safe_path):
        try:
            from safetensors.torch import load_file
            state_dict = load_file(safe_path)
        except ImportError:
            logger.warning("safetensors not installed, falling back to torch for .safetensors")
            import torch
            state_dict = torch.load(safe_path, map_location="cpu")
    elif os.path.exists(bin_path):
        import torch
        state_dict = torch.load(bin_path, map_location="cpu")
    else:
        raise FileNotFoundError(f"No weight files found in {adapter_path}")
    
    # Extract A and B matrices
    # LoRA typically stores weights as keys like 'base_model.model.layer.X.self_attn.q_proj.lora_A.weight'
    # We need to find the corresponding A and B pairs
    a_matrices = []
    b_matrices = []
    
    for key, value in state_dict.items():
        if "lora_A" in key:
            # Convert torch tensor to numpy
            if hasattr(value, 'numpy'):
                a_matrices.append(value.numpy())
            else:
                a_matrices.append(np.array(value))
        elif "lora_B" in key:
            if hasattr(value, 'numpy'):
                b_matrices.append(value.numpy())
            else:
                b_matrices.append(np.array(value))
    
    if not a_matrices or not b_matrices:
        # Fallback for proxy data or different format
        logger.warning("Standard LoRA keys not found. Checking for proxy format or alternate structure.")
        # If this is a proxy (from T012), it might be stored as 'A' and 'B' directly
        if "A" in state_dict:
            a_matrices.append(state_dict["A"])
        if "B" in state_dict:
            b_matrices.append(state_dict["B"])
        
        if not a_matrices or not b_matrices:
            raise ValueError(f"Could not extract A/B matrices from {adapter_path}. Keys: {list(state_dict.keys())}")
    
    # Concatenate all A and B matrices into single arrays
    # Flatten and concatenate to handle multiple layers
    A_flat = np.concatenate([m.flatten() for m in a_matrices])
    B_flat = np.concatenate([m.flatten() for m in b_matrices])
    
    return A_flat, B_flat


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    """
    Apply L2 normalization to a vector.

    Args:
        vector: Input 1D numpy array.

    Returns:
        L2 normalized vector.
    """
    norm = np.linalg.norm(vector)
    if norm == 0:
        logger.warning("Zero norm vector encountered, returning zeros")
        return vector
    return vector / norm


def validate_dimensions(vectors: List[np.ndarray], expected_dim: Optional[int] = None) -> bool:
    """
    Validate that all vectors have consistent dimensions.

    Args:
        vectors: List of 1D numpy arrays.
        expected_dim: Optional expected dimension to check against.

    Returns:
        True if validation passes, False otherwise.
    """
    if not vectors:
        return True
    
    first_dim = len(vectors[0])
    for i, vec in enumerate(vectors):
        if len(vec) != first_dim:
            logger.error(f"Dimension mismatch at index {i}: expected {first_dim}, got {len(vec)}")
            return False
    
    if expected_dim is not None and first_dim != expected_dim:
        logger.error(f"Dimension mismatch: expected {expected_dim}, got {first_dim}")
        return False
    
    logger.info(f"Dimension validation passed: all vectors have dimension {first_dim}")
    return True


def process_adapters(
    adapter_paths: List[str],
    output_path: str,
    config_path: Optional[str] = None
) -> Dict:
    """
    Process multiple LoRA adapters into a normalized skill vector database.

    Implements FR-001 and T016 (logging metrics).

    Args:
        adapter_paths: List of paths to adapter directories.
        output_path: Path to save the resulting .npz index file.
        config_path: Optional path to config file for metadata.

    Returns:
        Dictionary containing ingestion metrics.
    """
    start_time = time.time()
    
    # Load config if provided
    config = {}
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    
    vectors = []
    metadata = []
    dimensions = []
    
    for i, path in enumerate(adapter_paths):
        logger.info(f"Processing adapter {i+1}/{len(adapter_paths)}: {path}")
        
        try:
            A, B = load_lora_weights(path)
            
            # Concatenate A and B for the skill vector representation
            # Option 1: Concatenate A and B directly
            skill_vector = np.concatenate([A, B])
            
            # Apply L2 normalization
            normalized_vector = normalize_vector(skill_vector)
            
            vectors.append(normalized_vector)
            dimensions.append(len(normalized_vector))
            
            # Extract metadata
            task_name = os.path.basename(path)
            adapter_meta = {
                "name": task_name,
                "path": path,
                "vector_dim": len(normalized_vector),
                "is_proxy": config.get("is_proxy", False) if config else False
            }
            metadata.append(adapter_meta)
            
            logger.info(f"  - Processed {task_name}: vector dim = {len(normalized_vector)}")
            
        except Exception as e:
            logger.error(f"Failed to process {path}: {str(e)}")
            raise
    
    # Validate dimensions (FR-001 requirement)
    if not validate_dimensions(vectors):
        raise ValueError("Dimension validation failed")
    
    # Calculate index size
    total_size_bytes = sum(v.nbytes for v in vectors)
    total_size_mb = total_size_bytes / (1024 * 1024)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to .npz format
    logger.info(f"Saving index to {output_path}")
    np.savez(
        output_path,
        vectors=np.array(vectors),
        metadata=metadata,
        dimensions=np.array(dimensions)
    )
    
    # Calculate metrics
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    metrics = {
        "vectors_processed": len(vectors),
        "index_size_bytes": total_size_bytes,
        "index_size_mb": round(total_size_mb, 2),
        "vector_dimension": dimensions[0] if dimensions else 0,
        "processing_time_seconds": round(elapsed_time, 2),
        "output_path": output_path,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Log final metrics (T016 requirement)
    logger.info("=" * 50)
    logger.info("INGESTION METRICS SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Vectors processed: {metrics['vectors_processed']}")
    logger.info(f"Index size: {metrics['index_size_mb']} MB ({metrics['index_size_bytes']} bytes)")
    logger.info(f"Vector dimension: {metrics['vector_dimension']}")
    logger.info(f"Processing time: {metrics['processing_time_seconds']} seconds")
    logger.info(f"Output saved to: {metrics['output_path']}")
    logger.info("=" * 50)
    
    return metrics


def main():
    """
    Main entry point for the ingestion script.
    """
    project_root = get_project_root()
    
    # Default paths
    config_path = os.path.join(project_root, "data_sources.yaml")
    output_path = os.path.join(project_root, "data/processed/skill_index.npz")
    
    # Load adapter paths from data_sources.yaml or use defaults
    adapter_paths = []
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data_sources = yaml.safe_load(f)
        
        # Extract paths for ALFWorld and Search-QA weights
        for source in data_sources.get("sources", []):
            if source.get("type") in ["alfworld", "searchqa"]:
                path = source.get("path")
                if path and os.path.exists(path):
                    adapter_paths.append(path)
    
    # If no paths found in config, use default locations (for proxy data)
    if not adapter_paths:
        default_paths = [
            os.path.join(project_root, "data/raw/alfworld_weights"),
            os.path.join(project_root, "data/raw/searchqa_weights")
        ]
        adapter_paths = [p for p in default_paths if os.path.exists(p)]
    
    if not adapter_paths:
        logger.error("No adapter paths found. Please ensure weights are downloaded.")
        raise FileNotFoundError("No LoRA weight adapters found to process")
    
    logger.info(f"Found {len(adapter_paths)} adapter(s) to process")
    
    # Process adapters
    metrics = process_adapters(adapter_paths, output_path, config_path)
    
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    import json
    main()