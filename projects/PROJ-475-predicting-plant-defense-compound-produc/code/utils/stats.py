"""
Statistical Utilities Module for Plant Defense Compound Prediction Pipeline.

This module provides statistical functions for:
- Jaccard index calculations for feature stability
- Benjamini-Hochberg correction for multiple hypothesis testing
- Permutation test utilities
- Sensitivity analysis metrics
"""

import logging
import sys
from pathlib import Path
from typing import List, Set, Dict, Any, Union, Optional, Tuple
import numpy as np
import pandas as pd
import json

# Local imports
from utils.logging import get_module_logger

logger = get_module_logger(__name__)

def calculate_jaccard_index(set_a: Set[Any], set_b: Set[Any]) -> float:
    """
    Calculate the Jaccard index between two sets.
    
    The Jaccard index is the size of the intersection divided by the size 
    of the union of the sets.
    
    Args:
        set_a: First set of elements
        set_b: Second set of elements
        
    Returns:
        Jaccard index (0.0 to 1.0), or 0.0 if both sets are empty
    """
    if not set_a and not set_b:
        return 1.0  # Two empty sets are considered identical
    
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    if union == 0:
        return 0.0
    
    return intersection / union

def calculate_jaccard_index_from_lists(list_a: List[Any], list_b: List[Any]) -> float:
    """
    Calculate Jaccard index from two lists by converting to sets.
    
    Args:
        list_a: First list of elements
        list_b: Second list of elements
        
    Returns:
        Jaccard index (0.0 to 1.0)
    """
    return calculate_jaccard_index(set(list_a), set(list_b))

def calculate_jaccard_stability_matrix(feature_sets: List[Set[Any]]) -> np.ndarray:
    """
    Calculate a pairwise Jaccard stability matrix for multiple feature sets.
    
    Args:
        feature_sets: List of sets, each representing selected features
        
    Returns:
        2D numpy array of shape (n_sets, n_sets) with Jaccard indices
    """
    n = len(feature_sets)
    if n == 0:
        return np.array([]).reshape(0, 0)
    
    matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            matrix[i, j] = calculate_jaccard_index(feature_sets[i], feature_sets[j])
    
    return matrix

def calculate_mean_jaccard_stability(feature_sets: List[Set[Any]]) -> float:
    """
    Calculate the mean Jaccard stability across all pairwise comparisons.
    
    Args:
        feature_sets: List of sets, each representing selected features
        
    Returns:
        Mean Jaccard index across all unique pairs
    """
    if len(feature_sets) < 2:
        return 1.0 if len(feature_sets) == 1 else 0.0
    
    matrix = calculate_jaccard_stability_matrix(feature_sets)
    
    # Get upper triangle (excluding diagonal) for unique pairs
    upper_triangle = matrix[np.triu_indices(len(matrix), k=1)]
    
    if len(upper_triangle) == 0:
        return 1.0
    
    return float(np.mean(upper_triangle))

def compute_feature_stability_across_sweep(
    alpha_values: List[float],
    feature_selections: Dict[float, List[str]]
) -> Dict[str, Any]:
    """
    Compute feature stability metrics across a regularization parameter sweep.
    
    Args:
        alpha_values: List of alpha values tested
        feature_selections: Dictionary mapping alpha to list of selected features
        
    Returns:
        Dictionary with stability metrics including:
        - mean_jaccard: Mean pairwise Jaccard index
        - feature_frequency: How often each feature was selected
        - stable_features: Features selected in >80% of sweeps
    """
    if not feature_selections:
        return {
            "mean_jaccard": 0.0,
            "feature_frequency": {},
            "stable_features": [],
            "total_sweeps": 0
        }
    
    # Convert feature lists to sets
    feature_sets = [set(feature_selections[alpha]) for alpha in alpha_values]
    
    # Calculate mean Jaccard stability
    mean_jaccard = calculate_mean_jaccard_stability(feature_sets)
    
    # Calculate feature selection frequency
    all_features = set()
    for features in feature_selections.values():
        all_features.update(features)
    
    feature_frequency = {}
    total_sweeps = len(alpha_values)
    
    for feature in all_features:
        count = sum(1 for alpha in alpha_values if feature in feature_selections[alpha])
        feature_frequency[feature] = {
            "count": count,
            "frequency": count / total_sweeps if total_sweeps > 0 else 0.0
        }
    
    # Identify stable features (selected in >80% of sweeps)
    stable_features = [
        feature for feature, stats in feature_frequency.items()
        if stats["frequency"] > 0.8
    ]
    
    return {
        "mean_jaccard": float(mean_jaccard),
        "feature_frequency": feature_frequency,
        "stable_features": stable_features,
        "total_sweeps": total_sweeps
    }

def save_jaccard_stability_report(
    stability_metrics: Dict[str, Any],
    output_path: Union[str, Path]
) -> None:
    """
    Save Jaccard stability metrics to a JSON file.
    
    Args:
        stability_metrics: Dictionary of stability metrics
        output_path: Path to save the report
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(stability_metrics, f, indent=2)
    
    logger.info(f"Saved Jaccard stability report to {output_path}")

def benjamini_hochberg_correction(
    p_values: Union[List[float], np.ndarray],
    alpha: float = 0.05
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Benjamini-Hochberg correction for multiple hypothesis testing.
    
    Args:
        p_values: List or array of p-values
        alpha: Significance level (default 0.05)
        
    Returns:
        Tuple of (adjusted_p_values, boolean mask of significant results)
    """
    p_values = np.array(p_values)
    n = len(p_values)
    
    if n == 0:
        return np.array([]), np.array([], dtype=bool)
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate adjusted p-values
    # BH procedure: p_adj[i] = p[i] * n / (n - i)
    # But we need to ensure monotonicity (cumulative min from right)
    adjusted = np.zeros(n)
    for i in range(n):
        adjusted[i] = sorted_p_values[i] * n / (i + 1)
    
    # Enforce monotonicity: each adjusted p-value should be <= the next
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])
    
    # Clip to [0, 1]
    adjusted = np.clip(adjusted, 0, 1)
    
    # Map back to original order
    final_adjusted = np.zeros(n)
    final_adjusted[sorted_indices] = adjusted
    
    # Determine significance
    significant = final_adjusted < alpha
    
    return final_adjusted, significant

def main(*args, **kwargs) -> int:
    """
    Main entry point for stats module.
    
    Accepts flexible arguments to support various call patterns.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Demonstrate functionality with a simple test
        logger.info("Statistical utilities module loaded successfully.")
        
        # Test Jaccard index
        set_a = {"feature1", "feature2", "feature3"}
        set_b = {"feature2", "feature3", "feature4"}
        jaccard = calculate_jaccard_index(set_a, set_b)
        logger.info(f"Test Jaccard index: {jaccard}")
        
        # Test BH correction
        p_values = [0.01, 0.03, 0.04, 0.06, 0.10]
        adjusted, significant = benjamini_hochberg_correction(p_values)
        logger.info(f"Test BH correction: original={p_values}, adjusted={adjusted.tolist()}")
        
        return 0
    except Exception as e:
        logger.error(f"Stats module execution failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())