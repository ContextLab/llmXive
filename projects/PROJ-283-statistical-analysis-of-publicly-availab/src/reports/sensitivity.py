"""
Sensitivity analysis module.
"""
import numpy as np
from typing import List, Dict, Any, Set
from pathlib import Path
import json

def jaccard_index(set1: Set[str], set2: Set[str]) -> float:
    """
    Calculate Jaccard index between two sets.
    
    Args:
        set1: First set
        set2: Second set
    
    Returns:
        Jaccard index (intersection over union)
    """
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

def perform_threshold_sweep(pvalues: List[float], 
                           threshold_range: List[float],
                           feature_names: List[str]) -> Dict[str, Any]:
    """
    Perform threshold sweep analysis for sensitivity testing.
    
    Args:
        pvalues: List of p-values
        threshold_range: List of thresholds to test
        feature_names: List of feature names corresponding to p-values
    
    Returns:
        Analysis results dictionary
    """
    results = []
    significant_sets = []
    
    for threshold in threshold_range:
        significant = {name for name, p in zip(feature_names, pvalues) if p < threshold}
        significant_sets.append(significant)
        results.append({
            'threshold': threshold,
            'significant_count': len(significant),
            'significant_features': list(significant)
        })
    
    # Calculate Jaccard indices between consecutive thresholds
    jaccard_indices = []
    for i in range(len(significant_sets) - 1):
        jaccard = jaccard_index(significant_sets[i], significant_sets[i + 1])
        jaccard_indices.append({
            'threshold_from': threshold_range[i],
            'threshold_to': threshold_range[i + 1],
            'jaccard_index': jaccard
        })
    
    return {
        'threshold_sweep_results': results,
        'jaccard_indices': jaccard_indices
    }

def main():
    """Main entry point for CLI sensitivity analysis."""
    # Example usage
    pvalues = [0.001, 0.01, 0.03, 0.05, 0.10, 0.20, 0.30, 0.50]
    feature_names = ['f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8']
    threshold_range = [0.01, 0.05, 0.10, 0.20]
    
    result = perform_threshold_sweep(pvalues, threshold_range, feature_names)
    
    print("Threshold Sweep Results:")
    for res in result['threshold_sweep_results']:
        print(f"  Threshold {res['threshold']}: {res['significant_count']} significant features")
    
    print("\nJaccard Indices:")
    for ji in result['jaccard_indices']:
        print(f"  {ji['threshold_from']} -> {ji['threshold_to']}: {ji['jaccard_index']:.3f}")

if __name__ == "__main__":
    main()
