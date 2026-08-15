"""
Linearity Check Module (T030/T030b)

Validates the Pearson correlation between text-space and weight-space distances
for held-out composite tasks.
Implements T030: Calculate correlation.
Implements T030b: Validate threshold and append 'linearity_valid' boolean.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from scipy.stats import pearsonr

# Import from local project structure
# Note: Using relative import logic for script execution context
try:
    from src.utils.config import get_project_root, get_results_path, load_config
except ImportError:
    # Fallback for direct execution in different context
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.config import get_project_root, get_results_path, load_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_pairs(pairs_path: Path) -> List[Dict[str, Any]]:
    """
    Load held-out composite task pairs from YAML/JSON.
    T022g1 generates this file.
    """
    if not pairs_path.exists():
        raise FileNotFoundError(f"Held-out pairs file not found: {pairs_path}")

    # Handle both YAML and JSON based on extension
    if pairs_path.suffix.lower() in ['.yaml', '.yml']:
        import yaml
        with open(pairs_path, 'r') as f:
            data = yaml.safe_load(f)
    else:
        with open(pairs_path, 'r') as f:
            data = json.load(f)

    # Ensure we have a list of pairs
    if isinstance(data, dict) and 'pairs' in data:
        return data['pairs']
    return data


def load_skill_index(index_path: Path) -> Dict[str, Any]:
    """
    Load the flattened skill index (npz).
    Expects keys: 'vectors' (N, D), 'ids' (N,), 'metadata' (optional)
    """
    if not index_path.exists():
        raise FileNotFoundError(f"Skill index not found: {index_path}")

    data = np.load(index_path, allow_pickle=True)
    result = {}
    for key in data.files:
        if key == 'metadata':
            # Metadata might be a numpy array of objects or a dict
            val = data[key]
            if val.size == 1:
                result[key] = val.item()
            else:
                result[key] = val
        else:
            result[key] = data[key]
    return result


def get_vector_from_index(index_data: Dict[str, Any], skill_id: str) -> Optional[np.ndarray]:
    """
    Retrieve the flattened vector for a specific skill ID.
    """
    ids = index_data.get('ids')
    vectors = index_data.get('vectors')

    if ids is None or vectors is None:
        raise ValueError("Index data missing 'ids' or 'vectors'")

    # Convert ids to list if it's a numpy array
    if hasattr(ids, 'tolist'):
        ids_list = ids.tolist()
    else:
        ids_list = list(ids)

    try:
        idx = ids_list.index(skill_id)
        return vectors[idx]
    except ValueError:
        logger.warning(f"Skill ID {skill_id} not found in index")
        return None


def compute_distances(
    pairs: List[Dict[str, Any]],
    index_data: Dict[str, Any],
    query_embeddings: Optional[np.ndarray] = None
) -> Tuple[List[float], List[float]]:
    """
    Compute text-space and weight-space distances for each pair.
    
    Text-space: Cosine distance of embeddings (from T019 query generation).
    Weight-space: Cosine distance of flattened A/B vectors.
    
    Args:
        pairs: List of dicts with 'composite_desc', 'base_skill_ids'
        index_data: Loaded skill index
        query_embeddings: Optional pre-computed embeddings for composite descriptions.
                        If None, we assume the text distance is derived from the 
                        base skill embeddings if available, or we skip if not provided.
                        For T030/T030b, we assume the pairs file contains the 
                        necessary computed distances or we calculate weight-space 
                        and assume text-space is available or computed elsewhere.
                        
    Note: 
        The task description for T030 says: "Text-space: cosine distance of embeddings... 
        Weight-space: cosine distance of flattened A/B vectors."
        Since we don't have the raw text of the composite descriptions here to re-embed 
        without a heavy dependency, we assume the pairs file (from T022g1) contains 
        'text_distance' if pre-calculated, or we calculate weight-space and 
        attempt to load text distances if provided in the pair metadata.
        
        If 'text_distance' is not in the pair, we cannot compute the correlation 
        without re-embedding all composite descriptions. 
        We will check for 'text_distance' in the pair dict.
    """
    text_distances = []
    weight_distances = []

    for pair in pairs:
        base_ids = pair.get('base_skill_ids', [])
        if len(base_ids) != 2:
            logger.warning(f"Pair {pair.get('composite_desc', 'unknown')} does not have exactly 2 base skills. Skipping.")
            continue

        id1, id2 = base_ids
        vec1 = get_vector_from_index(index_data, id1)
        vec2 = get_vector_from_index(index_data, id2)

        if vec1 is None or vec2 is None:
            continue

        # Weight-space distance (Cosine)
        # 1 - cosine_similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            weight_dist = 2.0 # Max distance for zero vectors
        else:
            cos_sim = dot_product / (norm1 * norm2)
            weight_dist = 1.0 - cos_sim

        weight_distances.append(weight_dist)

        # Text-space distance
        # Check if pre-calculated in the pair (from T022g1 or T019)
        if 'text_distance' in pair:
            text_distances.append(pair['text_distance'])
        else:
            # Fallback: If we don't have text distance, we cannot compute correlation.
            # We log a warning and skip this pair for correlation calculation.
            logger.warning(f"Pair {pair.get('composite_desc', 'unknown')} missing 'text_distance'. Skipping for correlation.")
            continue

    return text_distances, weight_distances


def calculate_correlation(
    text_distances: List[float],
    weight_distances: List[float]
) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value.
    """
    if len(text_distances) < 2:
        logger.error("Insufficient data points for correlation calculation.")
        return 0.0, 1.0

    arr_text = np.array(text_distances)
    arr_weight = np.array(weight_distances)

    # Remove NaNs if any
    valid_mask = ~(np.isnan(arr_text) | np.isnan(arr_weight))
    arr_text = arr_text[valid_mask]
    arr_weight = arr_weight[valid_mask]

    if len(arr_text) < 2:
        logger.error("Insufficient valid data points after cleaning.")
        return 0.0, 1.0

    r, p_value = pearsonr(arr_text, arr_weight)
    return float(r), float(p_value)


def save_results(
    correlation: float,
    p_value: float,
    linearity_valid: bool,
    threshold: float,
    output_path: Path
) -> None:
    """
    Save results to JSON, appending 'linearity_valid'.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists to append/merge
    results = {}
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                results = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Existing results file is corrupted, overwriting.")
            results = {}

    results['pearson_correlation'] = correlation
    results['p_value'] = p_value
    results['threshold'] = threshold
    results['linearity_valid'] = linearity_valid
    results['sample_size'] = len(results.get('sample_size', 0)) + 1 # Rough count tracking

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Correlation: {correlation:.4f}, Valid: {linearity_valid}")


def main():
    """
    Main entry point for T030b.
    1. Load pairs from T022g1 (data/processed/known_composites_pairs.yaml)
    2. Load skill index from T014d (data/processed/skill_index.npz)
    3. Compute distances (or load pre-computed text distances)
    4. Calculate Pearson correlation
    5. Validate against threshold (from config)
    6. Save results to data/results/linearity_correlation.json
    """
    project_root = get_project_root()
    
    # Paths
    pairs_path = project_root / "data" / "processed" / "known_composites_pairs.yaml"
    index_path = project_root / "data" / "processed" / "skill_index.npz"
    output_path = project_root / "data" / "results" / "linearity_correlation.json"
    
    # Load config for threshold
    config = load_config()
    threshold = config.get('linearity_threshold', 0.7)
    
    logger.info(f"Starting linearity check with threshold: {threshold}")
    
    try:
        pairs = load_pairs(pairs_path)
        logger.info(f"Loaded {len(pairs)} pairs.")
        
        index_data = load_skill_index(index_path)
        logger.info(f"Loaded skill index with {len(index_data.get('ids', []))} skills.")
        
        text_dists, weight_dists = compute_distances(pairs, index_data)
        logger.info(f"Computed {len(text_dists)} valid distance pairs.")
        
        if len(text_dists) == 0:
            logger.error("No valid distance pairs found. Cannot compute correlation.")
            # Write a failure state
            save_results(0.0, 1.0, False, threshold, output_path)
            return 1

        correlation, p_value = calculate_correlation(text_dists, weight_dists)
        
        # T030b: Validate threshold
        # linearity_valid is True if correlation >= threshold
        linearity_valid = correlation >= threshold
        
        logger.info(f"Pearson Correlation: {correlation:.4f} (p={p_value:.4f})")
        logger.info(f"Linearity Valid (>= {threshold}): {linearity_valid}")
        
        save_results(correlation, p_value, linearity_valid, threshold, output_path)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during linearity check: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
