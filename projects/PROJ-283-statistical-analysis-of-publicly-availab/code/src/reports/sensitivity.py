import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Set
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

def calculate_jaccard_index(set1: Set[str], set2: Set[str]) -> float:
    """Calculate Jaccard index between two sets."""
    if len(set1) == 0 and len(set2) == 0:
        return 1.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0

def get_significant_predictors(
    p_values: Dict[str, float],
    threshold: float
) -> Set[str]:
    """Get set of predictors with p-value below threshold."""
    return {
        predictor for predictor, p_value in p_values.items()
        if p_value < threshold
    }

def perform_threshold_sweep(
    p_values: Dict[str, float],
    thresholds: List[float] = [0.005, 0.01, 0.05]
) -> Dict[str, Any]:
    """
    Perform threshold sweep analysis.
    
    Args:
        p_values: Dictionary of predictor p-values
        thresholds: List of p-value thresholds to test
    
    Returns:
        Dictionary with sweep results including Jaccard indices
    """
    results = {
        'thresholds': thresholds,
        'significant_counts': {},
        'significant_predictors': {},
        'jaccard_indices': {}
    }
    
    # Get significant predictors for each threshold
    for threshold in thresholds:
        sig_preds = get_significant_predictors(p_values, threshold)
        results['significant_counts'][str(threshold)] = len(sig_preds)
        results['significant_predictors'][str(threshold)] = sorted(list(sig_preds))
    
    # Calculate pairwise Jaccard indices
    jaccard_results = {}
    for i, t1 in enumerate(thresholds):
        for j, t2 in enumerate(thresholds):
            if i < j:
                set1 = set(results['significant_predictors'][str(t1)])
                set2 = set(results['significant_predictors'][str(t2)])
                
                jaccard = calculate_jaccard_index(set1, set2)
                key = f"Jaccard({t1}, {t2})"
                jaccard_results[key] = jaccard
    
    results['jaccard_indices'] = jaccard_results
    
    # Calculate delta (variation) in counts
    counts = [results['significant_counts'][str(t)] for t in thresholds]
    results['count_variation'] = {
        'min': min(counts),
        'max': max(counts),
        'delta': max(counts) - min(counts)
    }
    
    return results

def generate_sensitivity_report(
    model_results_path: Path,
    output_path: Path,
    thresholds: List[float] = [0.005, 0.01, 0.05]
):
    """
    Generate sensitivity analysis report.
    
    Args:
        model_results_path: Path to model metrics JSON
        output_path: Path to save sensitivity report
        thresholds: List of p-value thresholds
    """
    # Load model results
    with open(model_results_path, 'r') as f:
        model_results = json.load(f)
    
    # Analyze Beta model (primary)
    beta_p_values = model_results.get('beta', {}).get('p_values', {})
    
    if not beta_p_values:
        logger.warning("No p-values found in model results")
        beta_results = {'thresholds': [], 'significant_counts': {}, 'jaccard_indices': {}}
    else:
        beta_results = perform_threshold_sweep(beta_p_values, thresholds)
    
    # Analyze Ridge model if available
    ridge_results = None
    if 'ridge' in model_results and 'p_values' in model_results['ridge']:
        ridge_p_values = model_results['ridge']['p_values']
        ridge_results = perform_threshold_sweep(ridge_p_values, thresholds)
    
    # Build report
    report = {
        'beta_model': beta_results,
        'thresholds': thresholds,
        'sweep_range': {'min': min(thresholds), 'max': max(thresholds)}
    }
    
    if ridge_results:
        report['ridge_model'] = ridge_results
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity report saved to {output_path}")

def main():
    """Main entry point for sensitivity analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate sensitivity analysis report')
    parser.add_argument('--model-results', type=str, required=True, help='Path to model metrics JSON')
    parser.add_argument('--output', type=str, required=True, help='Path to save sensitivity report')
    
    args = parser.parse_args()
    
    generate_sensitivity_report(
        model_results_path=Path(args.model_results),
        output_path=Path(args.output)
    )
    
    logger.info("Sensitivity analysis complete")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
