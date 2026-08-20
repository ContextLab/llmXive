import os
import sys
import json
import time
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import random

# Local imports matching project API surface
from utils.logging_config import get_logger, info, error, warning, critical
from utils.schema_validation import validate_rsa_output
from config import get_config

logger = get_logger(__name__)

def load_story_embeddings(text_dir: Path) -> np.ndarray:
    """Load story embeddings from text directory."""
    embeddings_file = text_dir / "story_embeddings.npy"
    if not embeddings_file.exists():
        raise FileNotFoundError(f"Story embeddings not found at {embeddings_file}")
    return np.load(embeddings_file)

def load_event_averages(processed_dir: Path) -> pd.DataFrame:
    """Load event averages from processed directory."""
    averages_file = processed_dir / "event_averages.csv"
    if not averages_file.exists():
        raise FileNotFoundError(f"Event averages not found at {averages_file}")
    return pd.read_csv(averages_file)

def compute_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Compute cosine similarity matrix for embeddings."""
    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # Avoid division by zero
    normalized = embeddings / norms
    return np.dot(normalized, normalized.T)

def compute_rsa_distance(neural_sim: np.ndarray, story_sim: np.ndarray) -> float:
    """Compute RSA distance (Kendall's tau correlation) between matrices."""
    # Flatten upper triangles (excluding diagonal)
    n = neural_sim.shape[0]
    idx = np.triu_indices(n, k=1)
    neural_vec = neural_sim[idx]
    story_vec = story_sim[idx]
    
    # Compute Kendall's tau correlation
    from scipy.stats import kendalltau
    tau, p_value = kendalltau(neural_vec, story_vec)
    return float(tau)

def aggregate_neural_similarity(event_averages: pd.DataFrame) -> np.ndarray:
    """Aggregate neural similarity from event averages."""
    # Group by subject and event_id
    subjects = event_averages['subject_id'].unique()
    n_subjects = len(subjects)
    n_events = event_averages['event_id'].nunique()
    
    # Create subject-event matrix for each ROI
    roi_matrices = {}
    for roi in event_averages['roi'].unique():
        roi_data = event_averages[event_averages['roi'] == roi]
        pivot = roi_data.pivot(index='subject_id', columns='event_id', values='mean_signal')
        roi_matrices[roi] = pivot.values
    
    # Average across ROIs
    all_rois = list(roi_matrices.values())
    if len(all_rois) == 1:
        neural_matrix = all_rois[0]
    else:
        neural_matrix = np.mean(all_rois, axis=0)
    
    # Compute neural similarity matrix (correlation)
    from scipy.spatial.distance import pdist, squareform
    neural_dist = squareform(pdist(neural_matrix, metric='correlation'))
    neural_sim = 1 - neural_dist  # Convert distance to similarity
    
    return neural_sim

def run_permutation_test(
    neural_sim: np.ndarray,
    story_sim: np.ndarray,
    max_permutations: int = 10000,
    convergence_threshold: float = 0.001,
    convergence_window: int = 1000,
    timeout_hours: float = 2.0,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run permutation test until convergence or timeout.
    
    Convergence criteria: p-value variance < threshold over final window permutations.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    n_permutations = 0
    p_values = []
    observed_distance = compute_rsa_distance(neural_sim, story_sim)
    
    start_time = time.time()
    timeout_seconds = timeout_hours * 3600
    
    logger.info(f"Starting permutation test with observed distance: {observed_distance:.4f}")
    
    while n_permutations < max_permutations:
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.warning(f"Timeout reached after {n_permutations} permutations ({elapsed:.1f}s)")
            converged = False
            break
        
        # Permute story similarity matrix (shuffle rows/cols)
        perm_idx = np.random.permutation(story_sim.shape[0])
        permuted_story_sim = story_sim[np.ix_(perm_idx, perm_idx)]
        
        # Compute distance for permuted data
        permuted_distance = compute_rsa_distance(neural_sim, permuted_story_sim)
        
        # Track p-value: proportion of permuted distances >= observed
        p_values.append((n_permutations + 1, permuted_distance, p_values[-1][2] if p_values else 0))
        
        # Update cumulative p-value
        count_ge = sum(1 for _, d, _ in p_values if d >= observed_distance)
        current_p = count_ge / len(p_values)
        p_values[-1] = (n_permutations + 1, permuted_distance, current_p)
        
        n_permutations += 1
        
        # Check convergence
        if len(p_values) >= convergence_window:
            recent_p_values = [p[2] for p in p_values[-convergence_window:]]
            variance = np.var(recent_p_values)
            
            if variance < convergence_threshold:
                logger.info(f"Convergence reached at permutation {n_permutations} with variance {variance:.6f}")
                converged = True
                break
        
        # Log progress every 1000 permutations
        if n_permutations % 1000 == 0:
            logger.info(f"Permutation {n_permutations}: p-value = {current_p:.4f}")
    
    # Final p-value
    final_p = p_values[-1][2] if p_values else 0.0
    
    result = {
        "observed_distance": observed_distance,
        "final_p_value": final_p,
        "total_permutations": n_permutations,
        "converged": converged if 'converged' in locals() else False,
        "timeout_reached": not converged if 'converged' in locals() else True,
        "elapsed_seconds": time.time() - start_time,
        "p_values_over_time": [
            {"permutation": p[0], "distance": p[1], "p_value": p[2]} 
            for p in p_values
        ]
    }
    
    return result

def run_rsa_analysis(
    data_dir: Path,
    output_dir: Path
) -> Dict[str, Any]:
    """Run full RSA analysis pipeline."""
    text_dir = data_dir / "text"
    processed_dir = data_dir / "processed"
    results_dir = output_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info("Loading story embeddings...")
    story_embeddings = load_story_embeddings(text_dir)
    
    logger.info("Loading event averages...")
    event_averages = load_event_averages(processed_dir)
    
    # Compute similarity matrices
    logger.info("Computing story similarity matrix...")
    story_sim = compute_similarity_matrix(story_embeddings)
    
    logger.info("Computing neural similarity matrix...")
    neural_sim = aggregate_neural_similarity(event_averages)
    
    # Run permutation test
    logger.info("Running permutation test...")
    config = get_config()
    permutation_result = run_permutation_test(
        neural_sim,
        story_sim,
        timeout_hours=config.get('max_permutation_hours', 2.0),
        seed=config.get('random_seed', 42)
    )
    
    # Save results
    results = {
        "rsa_distance": permutation_result["observed_distance"],
        "permutation_test": permutation_result,
        "converged": permutation_result["converged"],
        "borderline": not permutation_result["converged"] and permutation_result["timeout_reached"]
    }
    
    output_file = results_dir / "permutation_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"RSA analysis complete. Results saved to {output_file}")
    
    # Validate output
    if not validate_rsa_output(output_file):
        logger.warning("RSA output validation failed")
    
    return results

def save_rsa_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save RSA results to file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """Main entry point for RSA analysis."""
    config = get_config()
    data_dir = Path("data")
    output_dir = Path("data")
    
    try:
        results = run_rsa_analysis(data_dir, output_dir)
        info("RSA analysis completed successfully")
    except FileNotFoundError as e:
        error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        error(f"RSA analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()