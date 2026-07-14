import logging
from pathlib import Path
from typing import List, Set, Dict, Any, Union, Optional
import numpy as np
import pandas as pd
from utils.logging import get_module_logger
import statsmodels.api as sm

logger = get_module_logger(__name__)

def calculate_jaccard_index(set1: Set[Any], set2: Set[Any]) -> float:
    """Calculate Jaccard index between two sets."""
    if not set1 and not set2:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    if union == 0:
        return 0.0
    return intersection / union

def calculate_jaccard_stability_matrix(feature_sets: List[Set[str]]) -> pd.DataFrame:
    """Calculate Jaccard index matrix for a list of feature sets."""
    n = len(feature_sets)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            matrix[i, j] = calculate_jaccard_index(feature_sets[i], feature_sets[j])
    return pd.DataFrame(matrix)

def calculate_mean_jaccard_stability(feature_sets: List[Set[str]]) -> float:
    """Calculate mean Jaccard index across all pairs of feature sets."""
    if len(feature_sets) < 2:
        return 1.0
    matrix = calculate_jaccard_stability_matrix(feature_sets)
    # Exclude diagonal
    n = matrix.shape[0]
    total_pairs = n * (n - 1)
    if total_pairs == 0:
        return 1.0
    return matrix.values.sum() / total_pairs

def save_jaccard_stability_report(feature_sets: List[Set[str]], output_path: str):
    """Save Jaccard stability report to a file."""
    matrix = calculate_jaccard_stability_matrix(feature_sets)
    mean_stability = calculate_mean_jaccard_stability(feature_sets)
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(f"Mean Jaccard Stability: {mean_stability:.4f}\n")
        f.write("Pairwise Jaccard Matrix:\n")
        f.write(matrix.to_string())

def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    
    Returns a list of booleans indicating which hypotheses are rejected.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Calculate BH thresholds
    thresholds = [(i + 1) * alpha / n for i in range(n)]
    
    # Find the largest k such that p_(k) <= threshold_(k)
    reject = [False] * n
    k = 0
    for i in range(n):
        if sorted_p_values[i] <= thresholds[i]:
            k = i + 1
    
    # Reject all hypotheses with p-value <= p_(k)
    for i in range(k):
        reject[sorted_indices[i]] = True
        
    return reject

def apply_bh_correction_to_predictors(
    predictor_names: List[str],
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, bool]:
    """
    Apply BH correction to predictor p-values and return significant predictors.
    
    Returns:
        Dict mapping predictor name to significance (True/False).
    """
    significant = benjamini_hochberg_correction(p_values, alpha)
    return dict(zip(predictor_names, significant))

# Import VIF-related functions if needed elsewhere
# Note: VIF calculation is moved to preprocessing.py to avoid circular imports
# but we keep the interface here if needed
def calculate_vif_stability(
    feature_sets: List[Set[str]],
    vif_threshold: float = 5.0
) -> Dict[str, float]:
    """
    Calculate stability of features that pass VIF threshold.
    
    Args:
        feature_sets: List of feature sets (e.g., from different alpha values).
        vif_threshold: VIF threshold used to filter features.
        
    Returns:
        Dict mapping feature name to stability score (0-1).
    """
    # Filter each set by VIF threshold (assuming we have a way to get VIF for each set)
    # This is a placeholder for the actual logic which would require VIF data
    stable_features = set()
    for fs in feature_sets:
        stable_features.update(fs)
        
    total_occurrences = {f: 0 for f in stable_features}
    for fs in feature_sets:
        for f in fs:
            total_occurrences[f] += 1
            
    stability = {f: count / len(feature_sets) for f, count in total_occurrences.items()}
    return stability

def main():
    """Main entry point for stats utilities."""
    logger.info("Stats utilities module loaded.")

if __name__ == "__main__":
    main()
