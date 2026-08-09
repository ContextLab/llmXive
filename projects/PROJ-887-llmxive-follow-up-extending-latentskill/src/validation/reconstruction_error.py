"""
Reconstruction Error Calculator (Task T022d)

Calculates the cosine distance (reconstruction error) between synthesized LoRA weights
(from T022b) and the ground truth composite weights (from T022c).

Outputs the error value to data/results/reconstruction_error.json.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "synthesized_adapters"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Input paths (defined by dependencies T022b and T022c)
SYNTHESIZED_ADAPTER_PATH = ARTIFACTS_DIR / "composite_task_adapter.npz"
GROUND_TRUTH_PATH = PROCESSED_DIR / "composite_ground_truth.npz"
OUTPUT_PATH = DATA_RESULTS_DIR / "reconstruction_error.json"


def load_npz_safe(path: Path) -> Dict[str, np.ndarray]:
    """Load an NPZ file and return a dictionary of arrays."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    
    try:
        data = np.load(path, allow_pickle=True)
        return {key: data[key] for key in data.files}
    except Exception as e:
        raise RuntimeError(f"Failed to load {path}: {e}")


def calculate_cosine_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine distance between two vectors.
    Cosine Distance = 1 - Cosine Similarity
    """
    if vec1.shape != vec2.shape:
        raise ValueError(f"Shape mismatch: {vec1.shape} vs {vec2.shape}")
    
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        logger.warning("One of the vectors has zero norm. Returning distance 1.0.")
        return 1.0
    
    dot_product = np.dot(vec1, vec2)
    cosine_similarity = dot_product / (norm1 * norm2)
    
    # Clamp to [-1, 1] to avoid numerical issues with arccos or direct subtraction
    cosine_similarity = np.clip(cosine_similarity, -1.0, 1.0)
    
    cosine_distance = 1.0 - cosine_similarity
    return float(cosine_distance)


def flatten_matrices(data: Dict[str, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Flatten A and B matrices from the loaded data into single vectors.
    Expects keys 'A' and 'B' or similar structure.
    """
    # Identify A and B keys
    a_keys = [k for k in data.keys() if k.lower() == 'a']
    b_keys = [k for k in data.keys() if k.lower() == 'b']
    
    if not a_keys or not b_keys:
        # Fallback: assume first key is A, second is B if not explicitly named
        keys = sorted(data.keys())
        if len(keys) >= 2:
            a_key, b_key = keys[0], keys[1]
        else:
            raise ValueError(f"Could not identify A and B matrices in {data.keys()}")
    else:
        a_key, b_key = a_keys[0], b_keys[0]
    
    mat_a = data[a_key]
    mat_b = data[b_key]
    
    # Flatten and concatenate
    vec_a = mat_a.flatten()
    vec_b = mat_b.flatten()
    
    return np.concatenate([vec_a, vec_b]), np.concatenate([vec_a, vec_b])


def compute_reconstruction_error(
    synthesized_path: Path,
    ground_truth_path: Path
) -> Dict[str, Any]:
    """
    Main logic to compute reconstruction error.
    """
    logger.info(f"Loading synthesized adapter from: {synthesized_path}")
    syn_data = load_npz_safe(synthesized_path)
    
    logger.info(f"Loading ground truth from: {ground_truth_path}")
    gt_data = load_npz_safe(ground_truth_path)
    
    # Flatten both
    syn_vec = np.concatenate([syn_data[k].flatten() for k in syn_data.keys()])
    gt_vec = np.concatenate([gt_data[k].flatten() for k in gt_data.keys()])
    
    logger.info(f"Synthesized vector shape: {syn_vec.shape}")
    logger.info(f"Ground truth vector shape: {gt_vec.shape}")
    
    # Calculate error
    error = calculate_cosine_distance(syn_vec, gt_vec)
    
    return {
        "reconstruction_error": error,
        "synthesized_path": str(synthesized_path),
        "ground_truth_path": str(ground_truth_path),
        "metric": "cosine_distance",
        "vector_dimension": int(syn_vec.shape[0])
    }


def main():
    """
    Entry point for T022d.
    Ensures output directory exists, computes error, and saves JSON.
    """
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Check inputs exist
        if not SYNTHESIZED_ADAPTER_PATH.exists():
            raise FileNotFoundError(
                f"Synthesized adapter not found. "
                f"Expected at: {SYNTHESIZED_ADAPTER_PATH}. "
                f"Ensure T022b has run successfully."
            )
        if not GROUND_TRUTH_PATH.exists():
            raise FileNotFoundError(
                f"Ground truth not found. "
                f"Expected at: {GROUND_TRUTH_PATH}. "
                f"Ensure T022c has run successfully."
            )
        
        result = compute_reconstruction_error(SYNTHESIZED_ADAPTER_PATH, GROUND_TRUTH_PATH)
        
        # Save result
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Reconstruction error calculated: {result['reconstruction_error']:.6f}")
        logger.info(f"Result saved to: {OUTPUT_PATH}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to compute reconstruction error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
