"""
Sensitivity Analysis for k in {1, 3, 5, 10}.

This module implements the sensitivity analysis logic (SC-004) by sweeping
the number of top-k skills used for interpolation. It loads the skill index,
known composite pairs, and evaluates the reconstruction error for each k.

Dependencies:
- T022a: Retrieval strategies (unweighted_mean, cosine_weighted_average)
- T022g: Known composite pairs (data/processed/known_composites_pairs.yaml)
- T014d: Skill index (data/processed/skill_index.npz)
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import yaml

# Import project configuration
from src.utils.config import get_project_root, get_data_path, get_results_path, set_seed

# Import retrieval strategies (T022a)
from src.retrieval.strategies import (
    load_skill_index,
    load_query_embeddings,
    get_skill_metadata,
    unweighted_mean,
    cosine_weighted_average,
    reconstruct_matrices
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_known_composites_pairs(pairs_path: Path) -> List[Dict[str, Any]]:
    """
    Load the synthetic known composite pairs from T022g.
    
    Args:
        pairs_path: Path to known_composites_pairs.yaml
        
    Returns:
        List of dictionaries containing task pairs and their ground truth weights.
    """
    if not pairs_path.exists():
        raise FileNotFoundError(f"Known composites pairs file not found: {pairs_path}")
    
    with open(pairs_path, 'r') as f:
        data = yaml.safe_load(f)
        
    return data.get('pairs', [])

def load_true_weights(weights_path: Path) -> Dict[str, np.ndarray]:
    """
    Load the ground truth synthesized weights from T022g.
    
    Args:
        weights_path: Path to known_composites_true_weights.npz
        
    Returns:
        Dictionary mapping pair_id to ground truth weight vector.
    """
    if not weights_path.exists():
        raise FileNotFoundError(f"True weights file not found: {weights_path}")
    
    data = np.load(weights_path, allow_pickle=True)
    return {str(key): data[key] for key in data.files}

def run_sensitivity_sweep(
    k_values: List[int] = [1, 3, 5, 10],
    index_path: Optional[Path] = None,
    pairs_path: Optional[Path] = None,
    true_weights_path: Optional[Path] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Execute the sensitivity analysis sweep for different k values.
    
    For each k, it:
    1. Loads the skill index.
    2. Iterates through known composite pairs.
    3. Retrieves top-k skills for each component task.
    4. Synthesizes weights via interpolation (unweighted mean).
    5. Calculates reconstruction error against ground truth.
    6. Aggregates mean and max error for the current k.
    
    Args:
        k_values: List of k values to sweep (default: [1, 3, 5, 10])
        index_path: Path to skill_index.npz (auto-resolved if None)
        pairs_path: Path to known_composites_pairs.yaml (auto-resolved if None)
        true_weights_path: Path to known_composites_true_weights.npz (auto-resolved if None)
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing sensitivity analysis results.
    """
    set_seed(seed)
    root = get_project_root()
    
    if index_path is None:
        index_path = root / "data" / "processed" / "skill_index.npz"
    if pairs_path is None:
        pairs_path = root / "data" / "processed" / "known_composites_pairs.yaml"
    if true_weights_path is None:
        true_weights_path = root / "data" / "processed" / "known_composites_true_weights.npz"
        
    logger.info(f"Loading skill index from {index_path}")
    skill_index = load_skill_index(index_path)
    
    logger.info(f"Loading known composite pairs from {pairs_path}")
    pairs = load_known_composites_pairs(pairs_path)
    
    logger.info(f"Loading true weights from {true_weights_path}")
    true_weights = load_true_weights(true_weights_path)
    
    results = {
        "k_values": k_values,
        "sweep_results": [],
        "summary": {}
    }
    
    for k in k_values:
        logger.info(f"--- Processing k={k} ---")
        start_time = time.time()
        
        errors = []
        pair_details = []
        
        for pair in pairs:
            pair_id = pair['id']
            task_a_id = pair['task_a_id']
            task_b_id = pair['task_b_id']
            
            # Retrieve top-k skills for Task A
            # Assuming the pair structure contains query text or we derive it from task IDs
            # For this implementation, we assume the 'pairs' file contains the necessary query text
            # or we map task_id -> query_text. If not, we use the task_id as a proxy for retrieval.
            # Based on T022g, pairs usually contain the synthetic task descriptions.
            
            # Retrieve neighbors for Task A
            # We need to get the embedding for the task description.
            # If the pair doesn't have direct embedding, we assume a mapping exists or use the task_id
            # to fetch a pre-computed embedding if available.
            # For robustness, we assume the pair dict has 'task_a_desc' and 'task_b_desc'.
            
            desc_a = pair.get('task_a_desc', task_a_id)
            desc_b = pair.get('task_b_desc', task_b_id)
            
            # In a real scenario, we would generate embeddings here using T019 logic.
            # However, to keep this task focused on the sweep logic and avoid duplicating
            # the embedding generation code, we assume the retrieval function can handle
            # the description or we fetch embeddings if they were cached.
            # Since T022g generated synthetic pairs, we assume they have descriptions.
            
            # NOTE: The strategies module expects query embeddings.
            # We will simulate the retrieval step by assuming we can get top-k indices
            # based on the task description.
            
            # For the sake of this specific task (T031a), we assume the 'load_skill_index'
            # provides enough metadata or we use a simple mock retrieval if embeddings are missing.
            # However, the strict requirement is to use the real logic.
            # Let's assume we have a helper to get embeddings or the pairs have them.
            # If not, we must implement the embedding generation here or import it.
            # Importing from src.retrieval.query is better.
            
            try:
                from src.retrieval.query import generate_query_embedding
                query_vec_a = generate_query_embedding(desc_a)
                query_vec_b = generate_query_embedding(desc_b)
            except ImportError:
                # Fallback if query module is not fully integrated or missing
                logger.warning("Could not import query generation. Using task_id as proxy.")
                # This is a placeholder; in a real run, this would fail or need proper embeddings.
                # For the sweep to run, we assume the pairs have embeddings or we generate them.
                # Let's assume we generate them. If the model is not loaded, this will fail loudly.
                raise RuntimeError("Embedding generation required for sensitivity sweep.")

            # Retrieve top-k
            # We need to find the indices in the skill index that match these queries.
            # Since load_skill_index returns the data, we need to compute distances.
            # The strategies module has 'single_nearest_neighbor' but we need top-k.
            # We will implement a simple top-k retrieval here using numpy.
            
            index_vectors = skill_index['vectors'] # Shape: (N, D)
            
            # Compute cosine similarity
            # Normalize query vectors
            q_a_norm = query_vec_a / np.linalg.norm(query_vec_a)
            q_b_norm = query_vec_b / np.linalg.norm(query_vec_b)
            
            # Normalize index vectors (pre-computed or on fly)
            if 'norms' in skill_index:
                index_norms = skill_index['norms']
            else:
                index_norms = np.linalg.norm(index_vectors, axis=1)
                # Avoid division by zero
                index_norms[index_norms == 0] = 1e-9
                
            index_normalized = index_vectors / index_norms[:, np.newaxis]
            
            sims_a = np.dot(index_normalized, q_a_norm)
            sims_b = np.dot(index_normalized, q_b_norm)
            
            # Get top-k indices
            top_k_idx_a = np.argsort(sims_a)[-k:][::-1]
            top_k_idx_b = np.argsort(sims_b)[-k:][::-1]
            
            # Get vectors
            vecs_a = index_vectors[top_k_idx_a]
            vecs_b = index_vectors[top_k_idx_b]
            
            # Synthesize: Unweighted Mean of top-k for A and B, then average them?
            # The T022g logic for "known composite" implies the ground truth is the
            # average of the synthesized weights of A and B.
            # So we synthesize A, synthesize B, then average them.
            
            syn_a = unweighted_mean(vecs_a)
            syn_b = unweighted_mean(vecs_b)
            
            # Composite synthesis
            synthesized_vec = unweighted_mean(np.vstack([syn_a, syn_b]))
            
            # Get ground truth
            true_vec = true_weights.get(pair_id)
            if true_vec is None:
                logger.warning(f"True weights missing for pair {pair_id}, skipping.")
                continue
            
            # Calculate reconstruction error (Cosine Distance)
            # Cosine Distance = 1 - Cosine Similarity
            if np.linalg.norm(synthesized_vec) == 0 or np.linalg.norm(true_vec) == 0:
                error = 1.0 # Maximum error
            else:
                sim = np.dot(synthesized_vec, true_vec) / (np.linalg.norm(synthesized_vec) * np.linalg.norm(true_vec))
                error = 1.0 - sim
            
            errors.append(error)
            pair_details.append({
                "pair_id": pair_id,
                "k": k,
                "error": float(error)
            })
        
        elapsed = time.time() - start_time
        mean_error = float(np.mean(errors)) if errors else 0.0
        max_error = float(np.max(errors)) if errors else 0.0
        
        logger.info(f"k={k}: Mean Error={mean_error:.4f}, Max Error={max_error:.4f}, Time={elapsed:.2f}s")
        
        results["sweep_results"].append({
            "k": k,
            "mean_error": mean_error,
            "max_error": max_error,
            "num_pairs": len(errors),
            "elapsed_time_seconds": elapsed,
            "details": pair_details
        })
        
    # Summary
    results["summary"] = {
        "best_k": min(results["sweep_results"], key=lambda x: x["mean_error"])["k"],
        "worst_k": max(results["sweep_results"], key=lambda x: x["mean_error"])["k"],
        "total_pairs_processed": len(pairs)
    }
    
    return results

def save_sensitivity_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save the sensitivity analysis results to a YAML file.
    
    Args:
        results: The dictionary of results from run_sensitivity_sweep.
        output_path: Path to save the results.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(results, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Results saved to {output_path}")

def main() -> None:
    """
    Main entry point for the sensitivity analysis sweep.
    """
    root = get_project_root()
    output_path = root / "data" / "results" / "sensitivity.yaml"
    
    logger.info("Starting Sensitivity Analysis Sweep (T031a)")
    
    try:
        results = run_sensitivity_sweep(
            k_values=[1, 3, 5, 10],
            seed=42
        )
        save_sensitivity_results(results, output_path)
        logger.info("Sensitivity analysis completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during sensitivity sweep: {e}")
        raise

if __name__ == "__main__":
    main()