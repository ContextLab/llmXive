"""
Linearity Check Implementation (T030)

Calculates Pearson correlation between text-space and weight-space distances
for a held-out set of known task pairs.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy.stats import pearsonr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
SKILL_INDEX_PATH = DATA_PROCESSED / "skill_index.npz"
PAIRS_PATH = DATA_PROCESSED / "pairs.yaml"
OUTPUT_PATH = DATA_RESULTS / "linearity_check.json"

# Ensure output directory exists
DATA_RESULTS.mkdir(parents=True, exist_ok=True)


def load_skill_index() -> Dict[str, np.ndarray]:
    """
    Load the flattened skill index from disk.
    Expected format: npz file with keys mapping to flattened weight vectors.
    """
    if not SKILL_INDEX_PATH.exists():
        raise FileNotFoundError(
            f"Skill index not found at {SKILL_INDEX_PATH}. "
            "Please run T014b to generate the index first."
        )
    
    logger.info(f"Loading skill index from {SKILL_INDEX_PATH}")
    data = np.load(SKILL_INDEX_PATH, allow_pickle=True)
    
    # Convert to dictionary if loaded as an npz object
    result = {}
    for key in data.files:
        result[key] = data[key]
    
    logger.info(f"Loaded {len(result)} skill vectors")
    return result


def load_pairs() -> List[Dict[str, Any]]:
    """
    Load the held-out task pairs from YAML.
    Expected format: list of dicts with 'task_a', 'task_b', 'alpha', 'text_a', 'text_b'.
    """
    if not PAIRS_PATH.exists():
        raise FileNotFoundError(
            f"Pairs file not found at {PAIRS_PATH}. "
            "Please ensure T022c has generated the ground truth and pairs file."
        )
    
    import yaml
    logger.info(f"Loading pairs from {PAIRS_PATH}")
    with open(PAIRS_PATH, 'r') as f:
        pairs = yaml.safe_load(f)
    
    if not isinstance(pairs, list):
        raise ValueError(f"Pairs file must contain a list, got {type(pairs)}")
    
    logger.info(f"Loaded {len(pairs)} task pairs")
    return pairs


def get_text_embeddings(task_ids: List[str]) -> np.ndarray:
    """
    Generate text embeddings for a list of task IDs/descriptions.
    Uses the same embedding model as T019 (all-MiniLM-L6-v2).
    """
    from sentence_transformers import SentenceTransformer
    
    logger.info("Loading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Extract descriptions from task_ids (assuming task_ids are actually descriptions or map to them)
    # In the context of T022c, pairs likely contain text descriptions directly or IDs that map to them.
    # We assume the 'pairs.yaml' contains 'text_a' and 'text_b' fields directly.
    # If task_ids are just IDs, we would need a mapping. For now, we assume the caller passes descriptions.
    # However, the function signature takes task_ids. Let's assume the pairs list contains the text.
    # This function is a helper to get embeddings for the text parts of the pairs.
    return model.encode(task_ids, convert_to_numpy=True)


def compute_weight_distance(w1: np.ndarray, w2: np.ndarray) -> float:
    """
    Compute the cosine distance between two weight vectors.
    """
    # Ensure vectors are 1D
    v1 = w1.flatten()
    v2 = w2.flatten()
    
    # Normalize
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 1.0  # Maximum distance if one is zero vector
    
    cosine_sim = np.dot(v1, v2) / (norm1 * norm2)
    # Clip to avoid numerical errors
    cosine_sim = np.clip(cosine_sim, -1.0, 1.0)
    
    return 1.0 - cosine_sim


def compute_text_distance(t1: np.ndarray, t2: np.ndarray) -> float:
    """
    Compute the cosine distance between two text embedding vectors.
    """
    cosine_sim = np.dot(t1, t2) / (np.linalg.norm(t1) * np.linalg.norm(t2))
    cosine_sim = np.clip(cosine_sim, -1.0, 1.0)
    return 1.0 - cosine_sim


def calculate_linearity_correlation(skill_index: Dict[str, np.ndarray], pairs: List[Dict[str, Any]]) -> Tuple[float, float, List[Dict]]:
    """
    Calculate Pearson correlation between text-space and weight-space distances.
    
    Returns:
        correlation: Pearson correlation coefficient
        p_value: P-value for the correlation
        details: List of detailed results for each pair
    """
    text_distances = []
    weight_distances = []
    details = []
    
    logger.info("Computing distances for each pair...")
    
    # We need text embeddings for all unique tasks first
    unique_texts = set()
    for pair in pairs:
        if 'text_a' in pair and 'text_b' in pair:
            unique_texts.add(pair['text_a'])
            unique_texts.add(pair['text_b'])
        elif 'task_a' in pair and 'task_b' in pair:
            # If only IDs are present, we assume the IDs map to descriptions in the index keys
            # or we need a separate mapping. For this implementation, we assume text fields exist.
            # If not, we fall back to using the key itself if it's in the skill_index keys.
            pass
    
    # Map text to embedding
    text_to_embedding = {}
    if unique_texts:
        embeddings = get_text_embeddings(list(unique_texts))
        for i, text in enumerate(unique_texts):
            text_to_embedding[text] = embeddings[i]
    
    for pair in pairs:
        try:
            # Get weight vectors
            # Assuming pair has keys 'task_a' and 'task_b' that correspond to keys in skill_index
            # OR 'id_a' and 'id_b'. Let's check common patterns.
            # Based on T022c, pairs likely have 'task_a' and 'task_b' as identifiers.
            id_a = pair.get('task_a') or pair.get('id_a')
            id_b = pair.get('task_b') or pair.get('id_b')
            
            if id_a not in skill_index:
                logger.warning(f"Task ID '{id_a}' not found in skill index, skipping pair.")
                continue
            if id_b not in skill_index:
                logger.warning(f"Task ID '{id_b}' not found in skill index, skipping pair.")
                continue
            
            w_a = skill_index[id_a]
            w_b = skill_index[id_b]
            
            # Compute weight distance
            w_dist = compute_weight_distance(w_a, w_b)
            weight_distances.append(w_dist)
            
            # Compute text distance
            text_a = pair.get('text_a', id_a) # Fallback to ID if text not found
            text_b = pair.get('text_b', id_b)
            
            if text_a in text_to_embedding and text_b in text_to_embedding:
                t_dist = compute_text_distance(text_to_embedding[text_a], text_to_embedding[text_b])
            else:
                # Fallback: if text embeddings not available, use 0 distance or skip?
                # We'll skip if we can't compute text distance to avoid noise
                logger.warning(f"Text embeddings missing for pair {id_a}-{id_b}, skipping.")
                continue
                
            text_distances.append(t_dist)
            
            details.append({
                'pair': f"{id_a}-{id_b}",
                'text_distance': float(t_dist),
                'weight_distance': float(w_dist)
            })
            
        except Exception as e:
            logger.error(f"Error processing pair {pair}: {e}")
            continue
    
    if len(text_distances) < 2:
        logger.warning("Not enough valid pairs to compute correlation.")
        return 0.0, 1.0, details
    
    # Compute Pearson correlation
    correlation, p_value = pearsonr(text_distances, weight_distances)
    
    logger.info(f"Calculated Pearson correlation: {correlation:.4f} (p-value: {p_value:.4f})")
    
    return float(correlation), float(p_value), details


def main():
    """
    Main entry point for the linearity check.
    """
    try:
        # Load data
        skill_index = load_skill_index()
        pairs = load_pairs()
        
        # Calculate correlation
        correlation, p_value, details = calculate_linearity_correlation(skill_index, pairs)
        
        # Determine validity flag (True if >= 0.6)
        validity_flag = correlation >= 0.6
        
        # Prepare output
        result = {
            'correlation': correlation,
            'p_value': p_value,
            'validity_flag': validity_flag,
            'threshold': 0.6,
            'num_pairs_analyzed': len(details),
            'details': details
        }
        
        # Write output
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Linearity check complete. Results saved to {OUTPUT_PATH}")
        logger.info(f"Correlation: {correlation:.4f}, Validity Flag: {validity_flag}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during linearity check: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
