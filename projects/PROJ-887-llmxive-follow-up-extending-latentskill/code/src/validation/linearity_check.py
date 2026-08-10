"""
Linearity Check Implementation (FR-007)

Calculates Pearson correlation between text-space and weight-space distances
for known task pairs to validate the linearity assumption of the latent skill space.

Outputs:
    data/results/linearity_check.json: {
        "correlation": float,
        "validity_flag": bool,
        "threshold": 0.6,
        "num_pairs": int
    }
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import yaml
from scipy.stats import pearsonr

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.config import get_project_root, get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
LINEARITY_THRESHOLD = 0.6
PAIRS_FILE_PATH = "data/processed/pairs.yaml"
SKILL_INDEX_PATH = "data/processed/skill_index.npz"
OUTPUT_PATH = "data/results/linearity_check.json"

def load_pairs(pairs_path: Path) -> List[Dict[str, Any]]:
    """Load the list of task pairs from YAML."""
    if not pairs_path.exists():
        raise FileNotFoundError(f"Pairs file not found: {pairs_path}")
    
    with open(pairs_path, 'r') as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {pairs_path}, got {type(data)}")
    
    return data

def load_skill_index(index_path: Path) -> Dict[str, np.ndarray]:
    """
    Load the skill index.
    Expected format: npz file containing arrays named '{task_id}_vector'.
    """
    if not index_path.exists():
        raise FileNotFoundError(f"Skill index not found: {index_path}")
    
    logger.info(f"Loading skill index from {index_path}")
    data = np.load(index_path, allow_pickle=True)
    
    # Convert to dict for easier access
    # np.load returns a NpzFile object, we need to extract arrays
    vectors = {}
    for key in data.files:
        # Handle potential nested structures if saved differently
        arr = data[key]
        if arr.ndim == 0:
            # If it's a 0-d array containing an object (like a dict), extract it
            if arr.dtype == object:
                vectors[key] = arr.item()
            else:
                vectors[key] = arr
        else:
            vectors[key] = arr
    
    return vectors

def get_vector_from_index(vectors: Dict[str, np.ndarray], task_id: str) -> np.ndarray:
    """Retrieve the flattened vector for a given task_id."""
    # Check for exact match first
    if task_id in vectors:
        return vectors[task_id]
    
    # Check for common naming conventions (e.g., 'task_id_vector')
    key = f"{task_id}_vector"
    if key in vectors:
        return vectors[key]
    
    # Fallback: search keys containing the task_id
    matches = [k for k in vectors.keys() if task_id in k]
    if len(matches) == 1:
        logger.warning(f"Found vector for '{task_id}' under key '{matches[0]}'")
        return vectors[matches[0]]
    
    if len(matches) > 1:
        raise KeyError(f"Ambiguous vector keys found for '{task_id}': {matches}")
    
    raise KeyError(f"Vector for task '{task_id}' not found in index.")

def compute_distances(pairs: List[Dict[str, Any]], vectors: Dict[str, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute text-space and weight-space distances for all pairs.
    
    Returns:
        text_distances: Array of cosine distances in text space (assumed to be in metadata or precomputed).
                        *Note*: Since T022c generates pairs.yaml, we assume it contains the text distance 
                        or we compute it from the task descriptions if embeddings are available.
                        For this implementation, we assume the 'pairs.yaml' contains 'text_distance' 
                        or we compute it if 'task_a_desc' and 'task_b_desc' are present.
        weight_distances: Array of cosine distances in weight space.
    """
    text_dists = []
    weight_dists = []

    logger.info(f"Processing {len(pairs)} task pairs...")

    for i, pair in enumerate(pairs):
        task_a_id = pair.get('task_a_id')
        task_b_id = pair.get('task_b_id')
        
        if not task_a_id or not task_b_id:
            logger.warning(f"Skipping pair {i}: missing task IDs in {pair}")
            continue

        # --- Weight Space Distance ---
        try:
            vec_a = get_vector_from_index(vectors, task_a_id)
            vec_b = get_vector_from_index(vectors, task_b_id)
            
            # Ensure same dimension
            if vec_a.shape != vec_b.shape:
                logger.error(f"Dimension mismatch for {task_a_id} vs {task_b_id}: {vec_a.shape} vs {vec_b.shape}")
                continue
            
            # Cosine distance: 1 - cosine_similarity
            # cosine_similarity = (a . b) / (||a|| ||b||)
            # Assuming vectors are L2 normalized from T013, ||a|| = ||b|| = 1
            # If not, we normalize on the fly to be safe
            norm_a = np.linalg.norm(vec_a)
            norm_b = np.linalg.norm(vec_b)
            
            if norm_a == 0 or norm_b == 0:
                logger.warning(f"Zero norm vector encountered for {task_a_id} or {task_b_id}")
                continue
            
            cos_sim = np.dot(vec_a, vec_b) / (norm_a * norm_b)
            # Clip to [-1, 1] to avoid numerical errors
            cos_sim = np.clip(cos_sim, -1.0, 1.0)
            weight_dist = 1.0 - cos_sim
            
            weight_dists.append(weight_dist)
        except KeyError as e:
            logger.error(f"Failed to retrieve weights for pair {i}: {e}")
            continue

        # --- Text Space Distance ---
        # The task description says "text-space distances". 
        # T022c generates pairs.yaml. We check if it has a precomputed distance.
        # If not, we assume it has descriptions and we compute text embeddings.
        # However, to avoid heavy dependencies in this specific validation script,
        # we first check for 'text_distance' in the pair.
        
        if 'text_distance' in pair:
            text_dist = pair['text_distance']
            text_dists.append(text_dist)
        elif 'task_a_desc' in pair and 'task_b_desc' in pair:
            # Fallback: Compute text distance if descriptions exist but distance is missing.
            # We use a simple heuristic or a lightweight embedding if available.
            # Since T019 uses 'all-MiniLM-L6-v2', we could use it here, but it adds a dependency.
            # Given the constraint of "extend, don't re-author", and the likelihood that
            # T022c should have populated this, we will raise a clear error if missing.
            raise ValueError(
                f"Pair {i} ({task_a_id}, {task_b_id}) missing 'text_distance'. "
                "Please ensure T022c generates text distances or includes them in pairs.yaml."
            )
        else:
            raise ValueError(
                f"Pair {i} ({task_a_id}, {task_b_id}) lacks 'text_distance' and descriptions."
            )

    if len(text_dists) != len(weight_dists):
        raise ValueError("Mismatch between number of valid text and weight distances.")

    return np.array(text_dists), np.array(weight_dists)

def calculate_correlation(text_dists: np.ndarray, weight_dists: np.ndarray) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(text_dists) < 2:
        logger.warning("Insufficient data points for correlation calculation.")
        return 0.0
    
    correlation, p_value = pearsonr(text_dists, weight_dists)
    logger.info(f"Pearson correlation: {correlation:.4f} (p-value: {p_value:.4f})")
    return float(correlation)

def save_results(correlation: float, validity_flag: bool, num_pairs: int, output_path: Path):
    """Save the results to JSON."""
    result = {
        "correlation": correlation,
        "validity_flag": validity_flag,
        "threshold": LINEARITY_THRESHOLD,
        "num_pairs": num_pairs
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for the linearity check."""
    try:
        root = get_project_root()
        pairs_path = root / PAIRS_FILE_PATH
        index_path = root / SKILL_INDEX_PATH
        output_path = root / OUTPUT_PATH

        # 1. Load Data
        logger.info("Loading task pairs...")
        pairs = load_pairs(pairs_path)
        
        logger.info("Loading skill index...")
        vectors = load_skill_index(index_path)

        # 2. Compute Distances
        logger.info("Computing distances...")
        text_dists, weight_dists = compute_distances(pairs, vectors)

        # 3. Calculate Correlation
        correlation = calculate_correlation(text_dists, weight_dists)

        # 4. Determine Validity
        validity_flag = correlation >= LINEARITY_THRESHOLD
        logger.info(f"Linearity check result: correlation={correlation:.4f}, valid={validity_flag}")

        # 5. Save Results
        save_results(correlation, validity_flag, len(text_dists), output_path)

        logger.info("Linearity check completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required file: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during linearity check: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
