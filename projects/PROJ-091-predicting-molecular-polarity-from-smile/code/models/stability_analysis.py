"""
Stability analysis module for bootstrap resampling of SHAP features.
Implements Jaccard similarity calculation for top individual features.

Conflict Note: This module implements spec SC-003 (individual feature stability)
which contradicts the plan.md's "cluster-only" metric stance.
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any, Optional
import numpy as np
import pandas as pd

from utils.logging_config import get_logger

logger = get_logger(__name__)


def get_top_feature_indices(shap_values: np.ndarray, top_k: int = 20) -> np.ndarray:
    """
    Extract indices of the top K features based on mean absolute SHAP values.
    
    Args:
        shap_values: Array of SHAP values (n_samples, n_features)
        top_k: Number of top features to return
        
    Returns:
        Array of feature indices for the top K features
    """
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    top_indices = np.argsort(mean_abs_shap)[::-1][:top_k]
    return top_indices


def calculate_jaccard_similarity(set_a: Set[int], set_b: Set[int]) -> float:
    """
    Calculate Jaccard similarity between two sets of feature indices.
    
    Jaccard = |A ∩ B| / |A ∪ B|
    
    Args:
        set_a: First set of feature indices
        set_b: Second set of feature indices
        
    Returns:
        Jaccard similarity score (0.0 to 1.0)
    """
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
        
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    if union == 0:
        return 0.0
        
    return intersection / union


def analyze_individual_feature_stability(
    bootstrap_results: List[Dict[str, Any]],
    top_k: int = 20
) -> Dict[str, Any]:
    """
    Calculate Jaccard similarity of top individual SHAP features across bootstrap resamples.
    
    This implements spec SC-003 which requires stability analysis of individual features,
    contradicting the plan.md's "cluster-only" approach.
    
    Args:
        bootstrap_results: List of dictionaries containing 'shap_values' and 'feature_names'
        top_k: Number of top features to consider for stability analysis
        
    Returns:
        Dictionary containing:
            - 'jaccard_scores': List of pairwise Jaccard similarities
            - 'mean_jaccard': Mean Jaccard similarity
            - 'std_jaccard': Standard deviation of Jaccard similarity
            - 'top_features': List of top feature names
            - 'stability_passed': Boolean indicating if mean_jaccard >= 0.7
    """
    if len(bootstrap_results) < 2:
        logger.warning("Less than 2 bootstrap resamples available. Cannot compute pairwise stability.")
        return {
            'jaccard_scores': [],
            'mean_jaccard': 0.0,
            'std_jaccard': 0.0,
            'top_features': [],
            'stability_passed': False,
            'error': 'Insufficient bootstrap resamples'
        }
    
    # Extract top feature indices for each resample
    top_feature_sets = []
    feature_names = None
    
    for i, result in enumerate(bootstrap_results):
        shap_vals = result['shap_values']
        if feature_names is None:
            feature_names = result.get('feature_names', [f"Feature_{j}" for j in range(shap_vals.shape[1])])
        
        top_indices = get_top_feature_indices(shap_vals, top_k=top_k)
        top_feature_sets.append(set(top_indices))
        logger.debug(f"Bootstrap {i}: Top {top_k} features extracted")
    
    # Calculate pairwise Jaccard similarities
    jaccard_scores = []
    for i in range(len(top_feature_sets)):
        for j in range(i + 1, len(top_feature_sets)):
            score = calculate_jaccard_similarity(top_feature_sets[i], top_feature_sets[j])
            jaccard_scores.append(score)
            logger.debug(f"Jaccard({i}, {j}) = {score:.4f}")
    
    mean_jaccard = np.mean(jaccard_scores) if jaccard_scores else 0.0
    std_jaccard = np.std(jaccard_scores) if jaccard_scores else 0.0
    
    # Get top feature names from the first resample (they should be consistent)
    top_indices = get_top_feature_indices(bootstrap_results[0]['shap_values'], top_k=top_k)
    top_features = [feature_names[idx] for idx in top_indices]
    
    # Check stability threshold (SC-003 requires >= 0.7)
    stability_passed = mean_jaccard >= 0.7
    
    if not stability_passed:
        logger.warning(
            f"Individual feature stability FAILED: mean Jaccard={mean_jaccard:.4f} < 0.7. "
            f"Spec SC-003 requirement not met."
        )
    else:
        logger.info(
            f"Individual feature stability PASSED: mean Jaccard={mean_jaccard:.4f} >= 0.7. "
            f"Spec SC-003 requirement met."
        )
    
    return {
        'jaccard_scores': jaccard_scores,
        'mean_jaccard': float(mean_jaccard),
        'std_jaccard': float(std_jaccard),
        'top_features': top_features,
        'stability_passed': stability_passed,
        'num_resamples': len(bootstrap_results),
        'top_k': top_k
    }


def run_stability_analysis(
    bootstrap_results_path: str,
    top_k: int = 20,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run full stability analysis including individual feature Jaccard similarity.
    
    Args:
        bootstrap_results_path: Path to the pickle file containing bootstrap results
        top_k: Number of top features to analyze
        output_dir: Directory to save analysis results (optional)
        
    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"Loading bootstrap results from {bootstrap_results_path}")
    
    if not os.path.exists(bootstrap_results_path):
        raise FileNotFoundError(f"Bootstrap results file not found: {bootstrap_results_path}")
    
    with open(bootstrap_results_path, 'rb') as f:
        bootstrap_results = pickle.load(f)
    
    logger.info(f"Loaded {len(bootstrap_results)} bootstrap resamples")
    
    # Analyze individual feature stability (SC-003)
    individual_analysis = analyze_individual_feature_stability(bootstrap_results, top_k=top_k)
    
    results = {
        'individual_feature_stability': individual_analysis,
        'config': {
            'top_k': top_k,
            'num_resamples': len(bootstrap_results)
        }
    }
    
    if output_dir:
        output_path = Path(output_dir) / "individual_stability_results.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Individual stability results saved to {output_path}")
    
    return results


def main():
    """Main entry point for stability analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run stability analysis on bootstrap results")
    parser.add_argument(
        "--bootstrap-results",
        type=str,
        default="data/processed/analysis/bootstrap_results.pkl",
        help="Path to bootstrap results pickle file"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="Number of top features to analyze"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed/analysis",
        help="Directory to save results"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_stability_analysis(
            bootstrap_results_path=args.bootstrap_results,
            top_k=args.top_k,
            output_dir=args.output_dir
        )
        
        print("\n" + "="*60)
        print("INDIVIDUAL FEATURE STABILITY ANALYSIS (SC-003)")
        print("="*60)
        print(f"Top K Features: {results['config']['top_k']}")
        print(f"Number of Resamples: {results['config']['num_resamples']}")
        print(f"Mean Jaccard Similarity: {results['individual_feature_stability']['mean_jaccard']:.4f}")
        print(f"Std Jaccard Similarity: {results['individual_feature_stability']['std_jaccard']:.4f}")
        print(f"Stability Threshold (0.7): {'PASSED' if results['individual_feature_stability']['stability_passed'] else 'FAILED'}")
        print(f"Top {results['config']['top_k']} Features:")
        for i, feat in enumerate(results['individual_feature_stability']['top_features'], 1):
            print(f"  {i}. {feat}")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Stability analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()