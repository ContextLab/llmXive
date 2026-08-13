import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import yaml

import numpy as np
from scipy.stats import pearsonr

# Import config for path resolution
from src.utils.config import get_project_root, get_data_path, get_results_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_pairs(pairs_path: Path) -> List[Dict[str, Any]]:
    """
    Load the synthetic known composite task pairs from T022g.
    Input: data/processed/known_composites_pairs.yaml
    """
    if not pairs_path.exists():
        raise FileNotFoundError(f"Pairs file not found at {pairs_path}. "
                                "Ensure T022g has been executed successfully.")
    
    with open(pairs_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Expected structure: list of dicts with 'task_pair', 'text_embedding_1', 'text_embedding_2', 'weight_vector_1', 'weight_vector_2'
    # Or similar structure where text and weight vectors are available.
    # Based on T022g description: "synthetic known composite tasks ... true weights ... linear interpolation"
    # The pairs file should contain the ground truth pairs used for validation.
    
    logger.info(f"Loaded {len(data)} task pairs from {pairs_path}")
    return data

def load_skill_index(index_path: Path) -> np.ndarray:
    """
    Load the flattened skill index generated in T014d.
    Input: data/processed/skill_index.npz
    """
    if not index_path.exists():
        raise FileNotFoundError(f"Skill index not found at {index_path}. "
                                "Ensure T014d has been executed successfully.")
    
    data = np.load(index_path)
    # Assuming the index contains a 'vectors' key or similar array of flattened weights
    if 'vectors' in data:
        vectors = data['vectors']
    elif 'data' in data:
        vectors = data['data']
    else:
        # Fallback: try to load the first array found
        vectors = next(iter(data.values()))
    
    logger.info(f"Loaded skill index with shape {vectors.shape}")
    return vectors

def get_vector_from_index(index_vectors: np.ndarray, vector_id: str) -> np.ndarray:
    """
    Retrieve a specific vector from the index by ID.
    This assumes the index has a parallel metadata structure or ID mapping.
    For T022g synthetic pairs, the 'weight_vector_1' and 'weight_vector_2' 
    are likely already provided in the pairs file as the 'true weights' 
    generated via interpolation. 
    
    However, the task asks to calculate correlation between text-space and weight-space.
    If the pairs file contains the 'true weights' (which are the ground truth for the composite),
    we use those directly for weight-space distance.
    
    If the pairs file only contains task IDs and we need to look up the interpolated weights
    from the index, we would do so here.
    
    Given T022g generates 'known_composites_true_weights.npz' and 'known_composites_pairs.yaml',
    the pairs.yaml likely references the specific vectors or contains the interpolated weights directly.
    We will assume the pairs file contains the necessary vectors or IDs to retrieve them.
    """
    # If the vector is already in the pair dict, return it.
    # Otherwise, we might need to look it up by ID.
    # For this implementation, we assume the pairs file contains the vectors directly
    # or the logic is handled in the distance calculation.
    raise NotImplementedError("This function is a placeholder. The actual vector retrieval "
                              "depends on the exact schema of known_composites_pairs.yaml. "
                              "We will handle this in compute_distances.")

def compute_distances(pairs: List[Dict[str, Any]], skill_index: np.ndarray) -> Tuple[List[float], List[float]]:
    """
    Compute pairwise distances in text-space and weight-space for all pairs.
    
    Returns:
        text_distances: List of distances between text embeddings of the pair members.
        weight_distances: List of distances between weight vectors of the pair members.
    """
    text_distances = []
    weight_distances = []

    for pair in pairs:
        # Expected keys in pair: 'text_embedding_1', 'text_embedding_2', 'weight_vector_1', 'weight_vector_2'
        # Or: 'task_id_1', 'task_id_2' which map to vectors in skill_index.
        
        # Case 1: Vectors are directly provided in the pair dict (likely for synthetic ground truth)
        if 'text_embedding_1' in pair and 'text_embedding_2' in pair:
            t1 = np.array(pair['text_embedding_1'])
            t2 = np.array(pair['text_embedding_2'])
            # Cosine distance for text
            dist_t = 1 - np.dot(t1, t2) / (np.linalg.norm(t1) * np.linalg.norm(t2) + 1e-8)
            text_distances.append(dist_t)
        
        if 'weight_vector_1' in pair and 'weight_vector_2' in pair:
            w1 = np.array(pair['weight_vector_1'])
            w2 = np.array(pair['weight_vector_2'])
            # Cosine distance for weights
            dist_w = 1 - np.dot(w1, w2) / (np.linalg.norm(w1) * np.linalg.norm(w2) + 1e-8)
            weight_distances.append(dist_w)
        
        # Case 2: Only IDs are provided, need to look up in skill_index
        # This logic would be implemented if the pairs file only contains IDs.
        # For now, we assume T022g provides the vectors directly as "synthetic ground truth weights".
        # If not, we would need to reconstruct the logic to find the vectors in the index.
        # Given the task description "Use the held-out set of synthetic known task pairs generated in T022g",
        # and T022g generates "true weights", it's highly likely the vectors are in the pairs file.
        
        if len(text_distances) != len(weight_distances):
            raise ValueError("Mismatch in text and weight vector availability in pair data.")

    logger.info(f"Computed {len(text_distances)} distance pairs.")
    return text_distances, weight_distances

def calculate_correlation(text_distances: List[float], weight_distances: List[float]) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient between text-space and weight-space distances.
    
    Returns:
        correlation: Pearson r value.
        p_value: p-value for the correlation.
    """
    if len(text_distances) < 2:
        raise ValueError("Need at least 2 data points to calculate correlation.")
    
    r, p = pearsonr(text_distances, weight_distances)
    logger.info(f"Pearson correlation (r): {r:.4f}, p-value: {p:.4f}")
    return r, p

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save the linearity check results to a JSON file.
    Output: data/results/linearity_check.json
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main() -> None:
    """
    Main entry point for T030: Linearity Check.
    
    1. Load pairs from data/processed/known_composites_pairs.yaml (T022g).
    2. Load skill index from data/processed/skill_index.npz (T014d).
    3. Compute text-space and weight-space distances.
    4. Calculate Pearson correlation.
    5. Save results to data/results/linearity_check.json.
    """
    project_root = get_project_root()
    pairs_path = project_root / "data" / "processed" / "known_composites_pairs.yaml"
    index_path = project_root / "data" / "processed" / "skill_index.npz"
    output_path = project_root / "data" / "results" / "linearity_check.json"

    logger.info("Starting Linearity Check (T030)...")

    try:
        # 1. Load pairs
        pairs = load_pairs(pairs_path)
        if not pairs:
            raise ValueError("No pairs found in the input file.")

        # 2. Load skill index (potentially needed for lookup if not in pairs)
        skill_index = load_skill_index(index_path)

        # 3. Compute distances
        text_dists, weight_dists = compute_distances(pairs, skill_index)

        # 4. Calculate correlation
        r, p = calculate_correlation(text_dists, weight_dists)

        # 5. Prepare results
        results = {
            "task_id": "T030",
            "description": "Pearson correlation between text-space and weight-space distances",
            "num_pairs": len(text_dists),
            "pearson_r": float(r),
            "p_value": float(p),
            "interpretation": "Strong positive correlation supports linearity assumption." if r > 0.7 else 
                            "Moderate correlation suggests some non-linearity." if r > 0.3 else 
                            "Weak correlation indicates significant non-linearity."
        }

        # 6. Save results
        save_results(results, output_path)

        logger.info("Linearity Check completed successfully.")
        print(f"Linearity Check Result: r={r:.4f}, p={p:.4f}")

    except Exception as e:
        logger.error(f"Linearity Check failed: {e}")
        raise

if __name__ == "__main__":
    main()
