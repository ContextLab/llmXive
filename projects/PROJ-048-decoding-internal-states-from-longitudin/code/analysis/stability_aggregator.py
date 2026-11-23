"""
Aggregates NMF results from multiple seeds to verify stability.

Calculates cosine similarity between components across different random seeds.
Verifies that the stability threshold (>= 0.95) is met (SC-004).
Writes a detailed stability report to code/analysis/stability_report.json.
"""
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from utils.logger import get_logger, log_stage_start, log_stage_end, log_memory_usage
from config import get_config_value, get_random_seed
from analysis.nmf_engine import NMFError, run_parallel_seed_sweep

logger = get_logger(__name__)

STABILITY_THRESHOLD = 0.95
REPORT_PATH = Path("code/analysis/stability_report.json")

class StabilityError(Exception):
    """Raised when stability analysis fails or thresholds are not met."""
    pass

def calculate_cosine_similarity_matrix(components_list: List[np.ndarray]) -> np.ndarray:
    """
    Calculates pairwise cosine similarity between component vectors across seeds.
    
    Args:
        components_list: List of 2D numpy arrays (n_components, n_features) from each seed.
    
    Returns:
        2D array of mean pairwise similarities between corresponding components.
    """
    if len(components_list) < 2:
        logger.warning("Less than 2 seeds provided, cannot calculate cross-seed similarity.")
        return np.array([])
    
    n_seeds = len(components_list)
    n_components = components_list[0].shape[0]
    
    # Normalize components to unit length for cosine similarity
    normalized_components = []
    for W in components_list:
        norms = np.linalg.norm(W, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.where(norms == 0, 1, norms)
        normalized_components.append(W / norms)
    
    # Calculate pairwise similarity for corresponding components
    # For simplicity, we compare component i of seed A with component i of seed B
    # This assumes components are somewhat aligned or we are checking rank stability
    # A more robust method would involve Hungarian algorithm for optimal matching,
    # but for stability threshold check, direct index matching is a common first step.
    similarity_matrix = np.zeros((n_seeds, n_seeds))
    
    for i in range(n_seeds):
        for j in range(i, n_seeds):
            # Cosine similarity between W_i and W_j
            # W shapes: (n_components, n_features)
            dot_product = np.dot(normalized_components[i], normalized_components[j].T)
            # Average similarity across all component pairs
            mean_sim = np.mean(dot_product)
            similarity_matrix[i, j] = mean_sim
            similarity_matrix[j, i] = mean_sim
    
    return similarity_matrix

def aggregate_stability_results(
    results_dir: Path,
    seeds: List[int],
    k_values: List[int]
) -> Dict[str, Any]:
    """
    Aggregates NMF results from multiple seeds and calculates stability metrics.
    
    Args:
        results_dir: Directory containing NMF result files from T023.
        seeds: List of random seeds used in the sweep.
        k_values: List of rank values (k) used in the sweep.
    
    Returns:
        Dictionary containing stability metrics and pass/fail status.
    """
    log_stage_start(logger, "Stability Aggregation")
    log_memory_usage(logger)
    
    report = {
        "threshold": STABILITY_THRESHOLD,
        "status": "PENDING",
        "seeds_analyzed": seeds,
        "k_values_analyzed": k_values,
        "details": []
    }
    
    all_similarities = []
    
    for k in k_values:
        logger.info(f"Analyzing stability for k={k}")
        
        # Collect component matrices for this k across all seeds
        components_for_k = []
        for seed in seeds:
            # Expected file path pattern based on T023 output
            result_file = results_dir / f"nmf_results_k{k}_seed{seed}.npz"
            if not result_file.exists():
                raise StabilityError(f"Result file not found: {result_file}")
            
            try:
                data = np.load(result_file)
                W = data['W']  # Component matrix
                components_for_k.append(W)
                logger.debug(f"Loaded components for k={k}, seed={seed}, shape={W.shape}")
            except Exception as e:
                raise StabilityError(f"Failed to load {result_file}: {e}")
        
        if len(components_for_k) < 2:
            logger.warning(f"Not enough seeds for k={k} to calculate stability.")
            continue
        
        # Calculate similarity matrix
        sim_matrix = calculate_cosine_similarity_matrix(components_for_k)
        mean_similarity = np.mean(sim_matrix)
        min_similarity = np.min(sim_matrix)
        max_similarity = np.max(sim_matrix)
        
        # Check if this k meets the threshold
        # We use the mean similarity as the primary metric, but also check min
        k_status = "PASS" if mean_similarity >= STABILITY_THRESHOLD else "FAIL"
        if min_similarity < STABILITY_THRESHOLD:
            # Even if mean passes, if min is very low, it might indicate instability
            logger.warning(f"k={k} has low minimum similarity: {min_similarity:.4f}")
        
        k_result = {
            "k": k,
            "mean_similarity": float(mean_similarity),
            "min_similarity": float(min_similarity),
            "max_similarity": float(max_similarity),
            "status": k_status,
            "similarity_matrix": sim_matrix.tolist()
        }
        
        report["details"].append(k_result)
        all_similarities.append(mean_similarity)
    
    # Overall status: PASS only if ALL k values pass
    if not all_similarities:
        report["status"] = "FAIL"
        report["reason"] = "No valid results to analyze"
    elif all(s >= STABILITY_THRESHOLD for s in all_similarities):
        report["status"] = "PASS"
        report["overall_mean_similarity"] = float(np.mean(all_similarities))
    else:
        report["status"] = "FAIL"
        report["overall_mean_similarity"] = float(np.mean(all_similarities))
        failed_k = [d["k"] for d in report["details"] if d["status"] == "FAIL"]
        report["reason"] = f"Stability threshold not met for k={failed_k}"
    
    log_stage_end(logger, "Stability Aggregation", report["status"])
    return report

def write_stability_report(report: Dict[str, Any], output_path: Path) -> None:
    """Writes the stability report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Stability report written to {output_path}")

def main():
    """
    Main entry point for the stability aggregation script.
    Runs the aggregation and writes the report.
    """
    logger.info("Starting stability aggregation for NMF results")
    
    # Get configuration
    try:
        seeds = [int(s) for s in get_config_value("NMF_SEEDS", default="42,123,456").split(",")]
        k_values = [int(k) for k in get_config_value("NMF_K_VALUES", default="5,10,15").split(",")]
        results_dir = Path(get_config_value("NMF_RESULTS_DIR", default="data/nmf_results"))
    except Exception as e:
        logger.error(f"Failed to read configuration: {e}")
        raise StabilityError(f"Configuration error: {e}")
    
    # Ensure results directory exists
    if not results_dir.exists():
        raise StabilityError(f"Results directory not found: {results_dir}. "
                           "Please run T023 (parallel seed sweep) first.")
    
    try:
        report = aggregate_stability_results(results_dir, seeds, k_values)
        write_stability_report(report, REPORT_PATH)
        
        # Exit with appropriate code
        if report["status"] == "PASS":
            logger.info("Stability check PASSED. Threshold >= 0.95 met.")
            return 0
        else:
            logger.error(f"Stability check FAILED. Reason: {report.get('reason', 'Unknown')}")
            return 1
    except StabilityError as e:
        logger.error(f"Stability aggregation failed: {e}")
        # Write a failure report if possible
        failure_report = {
            "status": "ERROR",
            "reason": str(e),
            "threshold": STABILITY_THRESHOLD
        }
        write_stability_report(failure_report, REPORT_PATH)
        return 2
    except Exception as e:
        logger.exception(f"Unexpected error during stability aggregation: {e}")
        return 3

if __name__ == "__main__":
    import sys
    sys.exit(main())
