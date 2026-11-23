"""
Statistical analysis utilities for model evaluation.

Implements One-way ANOVA, Tukey HSD, and degradation rate calculations.
"""
import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional

def compute_one_way_anova(
    groups: Dict[str, np.ndarray]
) -> Tuple[float, float]:
    """
    Perform One-way ANOVA test on groups of errors.
    
    Args:
        groups: Dictionary mapping group names to arrays of error values
        
    Returns:
        Tuple of (F-statistic, p-value)
    """
    group_arrays = list(groups.values())
    f_stat, p_value = stats.f_oneway(*group_arrays)
    return f_stat, p_value

def compute_tukey_hsd(
    groups: Dict[str, np.ndarray]
) -> Dict[str, Dict[str, float]]:
    """
    Perform Tukey HSD post-hoc test.
    
    Args:
        groups: Dictionary mapping group names to arrays of error values
        
    Returns:
        Dictionary of pairwise comparisons with p-values
    """
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    
    # Flatten data for statsmodels
    all_values = []
    all_groups = []
    
    for group_name, values in groups.items():
        all_values.extend(values)
        all_groups.extend([group_name] * len(values))
    
    # Perform Tukey HSD
    tukey = pairwise_tukeyhsd(endog=all_values, groups=all_groups, alpha=0.05)
    
    # Extract results
    results = {}
    for i, row in enumerate(tukey.summary().data[1:]):
        group1, group2, diff, reject, p_val = row
        key = f"{group1}_vs_{group2}"
        results[key] = {
            'difference': float(diff),
            'p_value': float(p_val),
            'significant': bool(reject)
        }
    
    return results

def compute_degradation_rate(
    densities: np.ndarray,
    errors: np.ndarray,
    max_training_density: float
) -> float:
    """
    Calculate degradation rate for out-of-distribution densities.
    
    Args:
        densities: Array of inclusion densities
        errors: Array of prediction errors (MAE)
        max_training_density: Maximum density in training set
        
    Returns:
        Degradation rate (slope of MAE vs density for OOD samples)
    """
    # Filter OOD samples (densities > max_training_density)
    ood_mask = densities > max_training_density
    ood_densities = densities[ood_mask]
    ood_errors = errors[ood_mask]
    
    if len(ood_densities) < 2:
        logger.warning("Not enough OOD samples to compute degradation rate")
        return 0.0
    
    # Linear regression to find slope
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        ood_densities, ood_errors
    )
    
    return float(slope)

def main(args) -> int:
    """
    Main entry point for statistical analysis.
    
    Args:
        args: Namespace with predictions_file, ground_truth_file, metadata_file
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import logging
    import json
    from pathlib import Path
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Load data
        with open(args.predictions_file, 'r') as f:
            predictions = json.load(f)
        
        with open(args.ground_truth_file, 'r') as f:
            ground_truth = json.load(f)
        
        with open(args.metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Compute errors
        errors = []
        densities = []
        
        for i, pred in enumerate(predictions):
            true_val = ground_truth[i]
            error = np.abs(pred - true_val)
            errors.append(error)
            densities.append(metadata[i]['inclusion_density'])
        
        errors = np.array(errors)
        densities = np.array(densities)
        
        # Group by density bin
        density_bins = ['low', 'medium', 'high']
        bin_thresholds = [0.2, 0.4]
        
        groups = {}
        for i, density in enumerate(densities):
            if density < bin_thresholds[0]:
                bin_name = 'low'
            elif density < bin_thresholds[1]:
                bin_name = 'medium'
            else:
                bin_name = 'high'
            
            if bin_name not in groups:
                groups[bin_name] = []
            groups[bin_name].append(errors[i])
        
        # Convert to numpy arrays
        groups = {k: np.array(v) for k, v in groups.items()}
        
        # Perform ANOVA
        f_stat, p_value = compute_one_way_anova(groups)
        logger.info(f"One-way ANOVA: F={f_stat:.4f}, p={p_value:.4f}")
        
        # Perform Tukey HSD
        tukey_results = compute_tukey_hsd(groups)
        logger.info(f"Tukey HSD comparisons: {len(tukey_results)} pairs")
        
        # Compute degradation rate (if max density available)
        max_density = max(metadata, key=lambda x: x['inclusion_density'])['inclusion_density']
        degradation_rate = compute_degradation_rate(densities, errors, max_density)
        logger.info(f"Degradation rate: {degradation_rate:.4f}")
        
        # Save results
        results = {
            'anova': {'f_statistic': f_stat, 'p_value': p_value},
            'tukey_hsd': tukey_results,
            'degradation_rate': degradation_rate,
            'n_samples': len(errors)
        }
        
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Statistical analysis for model evaluation")
    parser.add_argument("--predictions_file", type=str, default="data/processed/predictions.json")
    parser.add_argument("--ground_truth_file", type=str, default="data/processed/ground_truth.json")
    parser.add_argument("--metadata_file", type=str, default="data/raw/metadata.json")
    parser.add_argument("--output_file", type=str, default="data/processed/stats_results.json")
    args = parser.parse_args()
    exit(main(args))
