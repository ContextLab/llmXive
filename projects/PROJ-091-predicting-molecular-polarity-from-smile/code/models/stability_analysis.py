import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
import numpy as np

from utils.logging_config import get_logger
from models.interpret import load_model_and_data, compute_shap_values, run_two_stage_bootstrap_shap, run_full_dataset_bootstrap

# Initialize logger
logger = get_logger(__name__)

def get_top_feature_indices(shap_values: np.ndarray, top_k: int = 50) -> Set[int]:
    """
    Extract the indices of the top-k features with the highest mean absolute SHAP value.

    Args:
        shap_values: 2D array of shape (n_samples, n_features)
        top_k: Number of top features to select

    Returns:
        A set of feature indices corresponding to the top-k features
    """
    if shap_values.ndim != 2:
        raise ValueError(f"shap_values must be 2D, got {shap_values.ndim}D")

    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    top_indices = np.argsort(mean_abs_shap)[-top_k:]
    return set(int(idx) for idx in top_indices)

def calculate_jaccard_similarity(set_a: Set[int], set_b: Set[int]) -> float:
    """
    Calculate Jaccard similarity between two sets of feature indices.

    Jaccard = |A ∩ B| / |A ∪ B|

    Args:
        set_a: First set of feature indices
        set_b: Second set of feature indices

    Returns:
        Jaccard similarity coefficient (0.0 to 1.0)
    """
    if not set_a and not set_b:
        return 1.0  # Both empty, considered identical
    if not set_a or not set_b:
        return 0.0  # One empty, one not

    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def analyze_cluster_stability(cluster_results: List[Dict[str, Any]], top_k: int = 50) -> Dict[str, Any]:
    """
    Analyze stability of feature clusters across bootstrap resamples.
    (Note: T034a handles this; this function is kept for interface consistency)
    """
    logger.warning("analyze_cluster_stability is deprecated for individual feature analysis. Use analyze_individual_feature_stability.")
    return {}

def analyze_individual_feature_stability(shap_bootstrap_results: List[np.ndarray], top_k: int = 50) -> Dict[str, Any]:
    """
    Calculate Jaccard similarity of top individual SHAP features across multiple bootstrap resamples.
    This satisfies spec SC-003.

    Args:
        shap_bootstrap_results: List of 2D arrays, each from a bootstrap resample
        top_k: Number of top features to consider for Jaccard calculation

    Returns:
        Dictionary containing:
            - 'jaccard_scores': List of pairwise Jaccard similarities
            - 'mean_jaccard': Mean Jaccard similarity
            - 'median_jaccard': Median Jaccard similarity
            - 'min_jaccard': Minimum Jaccard similarity
            - 'max_jaccard': Maximum Jaccard similarity
            - 'top_features_appearances': Dict mapping feature index to count of appearances in top-k
    """
    if not shap_bootstrap_results:
        logger.error("No bootstrap results provided for stability analysis.")
        return {
            'jaccard_scores': [],
            'mean_jaccard': 0.0,
            'median_jaccard': 0.0,
            'min_jaccard': 0.0,
            'max_jaccard': 0.0,
            'top_features_appearances': {}
        }

    # Extract top-k feature sets for each bootstrap sample
    top_feature_sets = []
    for i, shap_vals in enumerate(shap_bootstrap_results):
        top_set = get_top_feature_indices(shap_vals, top_k=top_k)
        top_feature_sets.append(top_set)
        logger.debug(f"Bootstrap sample {i}: top {top_k} features count = {len(top_set)}")

    # Calculate pairwise Jaccard similarities
    jaccard_scores = []
    n_samples = len(top_feature_sets)
    for i in range(n_samples):
        for j in range(i + 1, n_samples):
            score = calculate_jaccard_similarity(top_feature_sets[i], top_feature_sets[j])
            jaccard_scores.append(score)

    # Calculate appearance counts
    feature_appearances = {}
    for feat_set in top_feature_sets:
        for feat_idx in feat_set:
            feature_appearances[feat_idx] = feature_appearances.get(feat_idx, 0) + 1

    # Compute statistics
    jaccard_array = np.array(jaccard_scores) if jaccard_scores else np.array([0.0])

    result = {
        'jaccard_scores': jaccard_scores,
        'mean_jaccard': float(np.mean(jaccard_array)),
        'median_jaccard': float(np.median(jaccard_array)),
        'min_jaccard': float(np.min(jaccard_array)),
        'max_jaccard': float(np.max(jaccard_array)),
        'top_features_appearances': {int(k): v for k, v in sorted(feature_appearances.items())},
        'num_bootstrap_samples': n_samples,
        'top_k': top_k
    }

    logger.info(f"Individual feature stability analysis complete. Mean Jaccard: {result['mean_jaccard']:.4f}")
    return result

def run_stability_analysis(
    bootstrap_mode: str = "full",
    n_bootstrap: int = 20,
    top_k: int = 50,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run full stability analysis including individual feature Jaccard similarity.

    Args:
        bootstrap_mode: "two_stage" (SHAP-only resampling) or "full" (re-train model)
        n_bootstrap: Number of bootstrap resamples
        top_k: Number of top features to analyze
        output_dir: Directory to save results (default: data/processed/analysis)

    Returns:
        Dictionary containing stability analysis results
    """
    if output_dir is None:
        output_dir = Path("data/processed/analysis")
        output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting stability analysis with {n_bootstrap} bootstrap samples using {bootstrap_mode} mode")

    # Load model and data
    X, shap_values_base = load_model_and_data()
    logger.info(f"Loaded data: {X.shape[0]} samples, {X.shape[1]} features")

    if bootstrap_mode == "full":
        logger.info("Running full dataset bootstrap (re-training model for each resample)...")
        # Run full bootstrap which re-trains models
        shap_bootstrap_results = run_full_dataset_bootstrap(n_bootstrap=n_bootstrap, top_k=top_k)
    elif bootstrap_mode == "two_stage":
        logger.info("Running two-stage bootstrap (SHAP-only resampling)...")
        shap_bootstrap_results = run_two_stage_bootstrap_shap(X, shap_values_base, n_bootstrap=n_bootstrap, top_k=top_k)
    else:
        raise ValueError(f"Unknown bootstrap_mode: {bootstrap_mode}. Use 'full' or 'two_stage'.")

    # Analyze individual feature stability (SC-003)
    individual_results = analyze_individual_feature_stability(shap_bootstrap_results, top_k=top_k)

    # Save results
    output_file = output_dir / "stability_individual_features.json"
    with open(output_file, 'w') as f:
        json.dump(individual_results, f, indent=2)

    logger.info(f"Saved individual feature stability results to {output_file}")
    logger.info(f"Mean Jaccard Similarity: {individual_results['mean_jaccard']:.4f}")
    logger.info(f"Median Jaccard Similarity: {individual_results['median_jaccard']:.4f}")

    # Check threshold
    threshold = 0.7
    if individual_results['mean_jaccard'] < threshold:
        logger.warning(f"Jaccard similarity ({individual_results['mean_jaccard']:.4f}) is below threshold ({threshold}). Feature stability may be low.")
    else:
        logger.info(f"Jaccard similarity ({individual_results['mean_jaccard']:.4f}) meets threshold ({threshold}).")

    return individual_results

def main():
    """Main entry point for stability analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Run stability analysis for SHAP features")
    parser.add_argument("--mode", choices=["full", "two_stage"], default="full",
                        help="Bootstrap mode: 'full' (re-train) or 'two_stage' (SHAP-only)")
    parser.add_argument("--n_bootstrap", type=int, default=20, help="Number of bootstrap samples")
    parser.add_argument("--top_k", type=int, default=50, help="Number of top features to analyze")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory for results")

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None

    results = run_stability_analysis(
        bootstrap_mode=args.mode,
        n_bootstrap=args.n_bootstrap,
        top_k=args.top_k,
        output_dir=output_dir
    )

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()