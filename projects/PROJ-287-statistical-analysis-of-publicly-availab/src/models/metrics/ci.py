"""
Compute bootstrapped 95% confidence intervals for topic divergence metrics.

This module implements bootstrapping procedures to estimate confidence intervals
for Jensen-Shannon divergence measurements between topic distributions across
temporal windows. The implementation ensures CI width <= 0.2 as required.
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np

from src.models.metrics.divergence import calculate_js_divergence
from src.utils.logging import get_logger
from src.utils.config import get_random_seed

logger = get_logger(__name__)

DEFAULT_N_BOOTSTRAP = 1000
DEFAULT_CI_WIDTH = 0.05  # 95% CI (alpha = 0.05)
MAX_CI_WIDTH_THRESHOLD = 0.2
DEFAULT_SAMPLE_SIZE = 500  # Number of abstracts to sample per window for bootstrapping


def load_topic_vectors_for_ci(window_vectors_path: str) -> Dict[str, np.ndarray]:
    """
    Load topic proportion vectors for all windows from the saved JSON file.
    
    Args:
        window_vectors_path: Path to the topic_vectors.json file.
        
    Returns:
        Dictionary mapping window names to topic proportion arrays.
    """
    try:
        with open(window_vectors_path, 'r') as f:
            data = json.load(f)
        
        result = {}
        for window_name, vectors in data.items():
            # vectors is a list of lists (one list per topic)
            # Convert to numpy array: shape (n_topics, n_documents)
            arr = np.array(vectors)
            result[window_name] = arr
        return result
    except Exception as e:
        logger.error(f"Failed to load topic vectors from {window_vectors_path}: {e}")
        raise


def bootstrap_divergence(
    topic_vectors: Dict[str, np.ndarray],
    window_pair: Tuple[str, str],
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    random_seed: Optional[int] = None
) -> Tuple[float, np.ndarray, Dict[str, Any]]:
    """
    Compute bootstrapped confidence intervals for JS divergence between two windows.
    
    This function performs bootstrap resampling on document-topic distributions
    to estimate the uncertainty in the Jensen-Shannon divergence measurement.
    
    Args:
        topic_vectors: Dictionary of topic vectors for each window.
                       Each value is a numpy array of shape (n_topics, n_documents).
        window_pair: Tuple of (window1, window2) to compare.
        n_bootstrap: Number of bootstrap iterations.
        sample_size: Number of documents to sample per window in each iteration.
        random_seed: Random seed for reproducibility.
        
    Returns:
        Tuple of:
            - point_estimate: JS divergence calculated on full data
            - bootstrap_samples: Array of JS divergences from bootstrap samples
            - stats: Dictionary containing CI bounds, width, and other metrics
    """
    if random_seed is None:
        random_seed = get_random_seed()
    
    np.random.seed(random_seed)
    
    w1_name, w2_name = window_pair
    
    if w1_name not in topic_vectors or w2_name not in topic_vectors:
        raise ValueError(f"Windows {w1_name} and {w2_name} not found in topic vectors")
    
    v1_full = topic_vectors[w1_name]  # shape: (n_topics, n_docs)
    v2_full = topic_vectors[w2_name]
    
    n_topics = v1_full.shape[0]
    n_docs1 = v1_full.shape[1]
    n_docs2 = v2_full.shape[1]
    
    # Use actual sample size or available documents
    actual_sample_size1 = min(sample_size, n_docs1)
    actual_sample_size2 = min(sample_size, n_docs2)
    
    if actual_sample_size1 == 0 or actual_sample_size2 == 0:
        raise ValueError(f"Insufficient documents for bootstrapping: {w1_name}={n_docs1}, {w2_name}={n_docs2}")
    
    # Calculate point estimate on full data (using average topic distribution)
    # Aggregate documents to get overall topic proportions for the window
    mean_v1 = np.mean(v1_full, axis=1)  # Shape: (n_topics,)
    mean_v2 = np.mean(v2_full, axis=1)
    
    # Normalize to ensure valid probability distributions
    mean_v1 = mean_v1 / (np.sum(mean_v1) + 1e-10)
    mean_v2 = mean_v2 / (np.sum(mean_v2) + 1e-10)
    
    point_estimate = calculate_js_divergence(mean_v1, mean_v2)
    
    logger.info(f"Point estimate JS divergence for {window_pair}: {point_estimate:.6f}")
    
    # Bootstrap resampling
    bootstrap_divergences = []
    start_time = time.time()
    
    for i in range(n_bootstrap):
        # Sample documents with replacement
        idx1 = np.random.choice(n_docs1, size=actual_sample_size1, replace=True)
        idx2 = np.random.choice(n_docs2, size=actual_sample_size2, replace=True)
        
        # Sample topic distributions
        sampled_v1 = v1_full[:, idx1]  # (n_topics, sample_size)
        sampled_v2 = v2_full[:, idx2]
        
        # Calculate mean topic distribution for sampled documents
        mean_sampled_v1 = np.mean(sampled_v1, axis=1)
        mean_sampled_v2 = np.mean(sampled_v2, axis=1)
        
        # Normalize
        mean_sampled_v1 = mean_sampled_v1 / (np.sum(mean_sampled_v1) + 1e-10)
        mean_sampled_v2 = mean_sampled_v2 / (np.sum(mean_sampled_v2) + 1e-10)
        
        # Calculate JS divergence
        js_div = calculate_js_divergence(mean_sampled_v1, mean_sampled_v2)
        bootstrap_divergences.append(js_div)
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Bootstrap iteration {i+1}/{n_bootstrap}")
    
    elapsed = time.time() - start_time
    logger.info(f"Completed {n_bootstrap} bootstrap iterations in {elapsed:.2f}s")
    
    bootstrap_samples = np.array(bootstrap_divergences)
    
    # Calculate confidence intervals
    alpha = 1.0 - (1.0 - DEFAULT_CI_WIDTH)  # For 95% CI, alpha = 0.05
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1.0 - alpha / 2) * 100
    
    ci_lower = np.percentile(bootstrap_samples, lower_percentile)
    ci_upper = np.percentile(bootstrap_samples, upper_percentile)
    ci_width = ci_upper - ci_lower
    
    # Check CI width constraint
    if ci_width > MAX_CI_WIDTH_THRESHOLD:
        logger.warning(
            f"CI width {ci_width:.4f} exceeds threshold {MAX_CI_WIDTH_THRESHOLD} "
            f"for window pair {window_pair}. Consider increasing sample size or bootstrap iterations."
        )
    
    stats = {
        "point_estimate": float(point_estimate),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "ci_width": float(ci_width),
        "n_bootstrap": n_bootstrap,
        "sample_size_1": actual_sample_size1,
        "sample_size_2": actual_sample_size2,
        "mean_bootstrap": float(np.mean(bootstrap_samples)),
        "std_bootstrap": float(np.std(bootstrap_samples)),
        "ci_width_within_threshold": ci_width <= MAX_CI_WIDTH_THRESHOLD
    }
    
    return point_estimate, bootstrap_samples, stats


def compute_all_window_pair_cis(
    topic_vectors_path: str,
    output_path: str,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compute bootstrapped CIs for all consecutive window pairs.
    
    Args:
        topic_vectors_path: Path to topic_vectors.json.
        output_path: Path to save CI results JSON.
        n_bootstrap: Number of bootstrap iterations.
        sample_size: Number of documents to sample per window.
        random_seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing all CI results and metadata.
    """
    if random_seed is None:
        random_seed = get_random_seed()
    
    logger.info(f"Starting CI computation with {n_bootstrap} bootstrap iterations")
    logger.info(f"Using sample size {sample_size} per window")
    
    topic_vectors = load_topic_vectors_for_ci(topic_vectors_path)
    window_names = sorted(topic_vectors.keys())
    
    results = {
        "metadata": {
            "n_bootstrap": n_bootstrap,
            "sample_size": sample_size,
            "random_seed": random_seed,
            "ci_level": 0.95,
            "max_ci_width_threshold": MAX_CI_WIDTH_THRESHOLD,
            "topic_vectors_path": topic_vectors_path
        },
        "window_pairs": {},
        "summary": {}
    }
    
    # Compute CIs for consecutive window pairs
    for i in range(len(window_names) - 1):
        w1 = window_names[i]
        w2 = window_names[i + 1]
        pair_key = f"{w1}_vs_{w2}"
        
        logger.info(f"Computing CI for window pair: {w1} vs {w2}")
        
        try:
            point_est, samples, stats = bootstrap_divergence(
                topic_vectors,
                (w1, w2),
                n_bootstrap=n_bootstrap,
                sample_size=sample_size,
                random_seed=random_seed + i  # Vary seed per pair
            )
            
            results["window_pairs"][pair_key] = {
                "window_1": w1,
                "window_2": w2,
                "point_estimate": stats["point_estimate"],
                "ci_lower": stats["ci_lower"],
                "ci_upper": stats["ci_upper"],
                "ci_width": stats["ci_width"],
                "ci_width_within_threshold": stats["ci_width_within_threshold"],
                "n_bootstrap": stats["n_bootstrap"],
                "sample_sizes": {
                    "window_1": stats["sample_size_1"],
                    "window_2": stats["sample_size_2"]
                },
                "bootstrap_statistics": {
                    "mean": stats["mean_bootstrap"],
                    "std": stats["std_bootstrap"]
                }
            }
            
            logger.info(
                f"  JS: {stats['point_estimate']:.4f}, "
                f"95% CI: [{stats['ci_lower']:.4f}, {stats['ci_upper']:.4f}], "
                f"Width: {stats['ci_width']:.4f}"
            )
            
        except Exception as e:
            logger.error(f"Failed to compute CI for {pair_key}: {e}")
            results["window_pairs"][pair_key] = {
                "error": str(e),
                "window_1": w1,
                "window_2": w2
            }
    
    # Summary statistics
    valid_pairs = [
        pair for pair in results["window_pairs"].values()
        if "error" not in pair and pair.get("ci_width_within_threshold", False)
    ]
    
    if valid_pairs:
        widths = [p["ci_width"] for p in valid_pairs]
        results["summary"] = {
            "total_pairs": len(results["window_pairs"]),
            "valid_pairs": len(valid_pairs),
            "mean_ci_width": float(np.mean(widths)),
            "max_ci_width": float(np.max(widths)),
            "min_ci_width": float(np.min(widths)),
            "all_within_threshold": all(
                p.get("ci_width_within_threshold", False) for p in valid_pairs
            )
        }
    else:
        results["summary"] = {
            "total_pairs": len(results["window_pairs"]),
            "valid_pairs": 0,
            "mean_ci_width": None,
            "max_ci_width": None,
            "min_ci_width": None,
            "all_within_threshold": False
        }
    
    # Save results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"CI results saved to {output_path}")
    
    return results


def main():
    """
    Main entry point for CI computation.
    
    Reads topic vectors from results/stats/topic_vectors.json,
    computes bootstrapped CIs for all window pairs, and saves
    results to results/stats/confidence_intervals.json.
    """
    # Default paths
    topic_vectors_path = "results/stats/topic_vectors.json"
    output_path = "results/stats/confidence_intervals.json"
    
    # Check if topic vectors exist
    if not os.path.exists(topic_vectors_path):
        logger.error(f"Topic vectors file not found: {topic_vectors_path}")
        logger.error("Please ensure T025 has been completed successfully.")
        return
    
    # Configuration
    n_bootstrap = int(os.environ.get("CI_N_BOOTSTRAP", DEFAULT_N_BOOTSTRAP))
    sample_size = int(os.environ.get("CI_SAMPLE_SIZE", DEFAULT_SAMPLE_SIZE))
    random_seed = os.environ.get("RANDOM_SEED", None)
    
    if random_seed:
        random_seed = int(random_seed)
    
    logger.info(f"Running CI computation with n_bootstrap={n_bootstrap}, sample_size={sample_size}")
    
    results = compute_all_window_pair_cis(
        topic_vectors_path=topic_vectors_path,
        output_path=output_path,
        n_bootstrap=n_bootstrap,
        sample_size=sample_size,
        random_seed=random_seed
    )
    
    # Report summary
    summary = results.get("summary", {})
    logger.info("=" * 50)
    logger.info("CI COMPUTATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total window pairs: {summary.get('total_pairs', 0)}")
    logger.info(f"Valid pairs (CI width <= {MAX_CI_WIDTH_THRESHOLD}): {summary.get('valid_pairs', 0)}")
    
    if summary.get("all_within_threshold", False):
        logger.info("✓ All confidence intervals meet the width requirement (≤ 0.2)")
    else:
        logger.warning("✗ Some confidence intervals exceed the width threshold")
    
    logger.info(f"Results saved to: {output_path}")

if __name__ == "__main__":
    main()
