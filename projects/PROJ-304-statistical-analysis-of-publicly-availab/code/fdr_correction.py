import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from logger import get_logger, get_project_root

logger = get_logger(__name__)

def apply_benjamini_hochberg(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """
    Apply the Benjamini-Hochberg FDR correction to a 1D array of p-values.
    
    Args:
        p_values: 1D numpy array of p-values.
        alpha: Significance level (default 0.05).
        
    Returns:
        1D numpy array of booleans indicating which hypotheses are rejected (True = significant).
    """
    n = len(p_values)
    if n == 0:
        return np.array([], dtype=bool)
        
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate BH critical values
    # Rank starts at 1
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha
    
    # Find the largest k such that p_(k) <= critical_(k)
    # We need to find the largest index where this holds
    valid = sorted_p_values <= critical_values
    
    if not np.any(valid):
        # No rejections
        rejected = np.zeros(n, dtype=bool)
    else:
        # Find the largest rank k where condition holds
        # We iterate from the end to find the largest k
        k = n - 1
        while k >= 0:
            if valid[k]:
                break
            k -= 1
        
        # All p-values with rank <= k are rejected
        rejected_sorted = np.zeros(n, dtype=bool)
        rejected_sorted[:k+1] = True
        
        # Map back to original order
        rejected = np.zeros(n, dtype=bool)
        rejected[sorted_indices] = rejected_sorted
        
    return rejected

def apply_fdr_to_model_results(
    model_results: Dict[str, Dict[str, Dict[str, float]]], 
    primary_covariates: List[str], 
    alpha: float = 0.05
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values from model results.
    
    Args:
        model_results: Nested dict structure:
            {
                'model_type': {
                    'covariate_name': {
                        'coef': float,
                        'p_value': float,
                        'robust_p_value': float,
                        ...
                    }
                }
            }
        primary_covariates: List of covariate names to apply FDR correction to.
        alpha: Significance level (default 0.05).
        
    Returns:
        Updated model_results dict with 'fdr_rejected' (bool) and 'fdr_adjusted_p' (float) added.
    """
    logger.info(f"Applying Benjamini-Hochberg FDR correction (alpha={alpha}) to primary covariates: {primary_covariates}")
    
    for model_type, covariates in model_results.items():
        logger.debug(f"Processing model type: {model_type}")
        
        # Collect all robust p-values for primary covariates in this model
        p_vals = []
        covariate_list = []
        
        for cov_name in primary_covariates:
            if cov_name in covariates:
                if 'robust_p_value' in covariates[cov_name]:
                    p_vals.append(covariates[cov_name]['robust_p_value'])
                    covariate_list.append(cov_name)
                else:
                    logger.warning(f"Covariate '{cov_name}' in model '{model_type}' missing 'robust_p_value'. Skipping FDR for this covariate.")
        
        if len(p_vals) == 0:
            logger.info(f"No valid p-values found for primary covariates in model '{model_type}'. Skipping FDR.")
            continue
            
        # Apply BH correction
        p_array = np.array(p_vals)
        rejected_mask = apply_benjamini_hochberg(p_array, alpha)
        
        # Calculate adjusted p-values (optional but useful)
        # Adjusted p-value = p * n / rank
        sorted_indices = np.argsort(p_array)
        sorted_p = p_array[sorted_indices]
        n = len(sorted_p)
        ranks = np.arange(1, n + 1)
        
        # Calculate adjusted p-values, ensuring they are monotonic and <= 1
        adjusted_p_sorted = np.minimum.accumulate((sorted_p * n) / ranks[::-1][::-1])[::-1]
        adjusted_p_sorted = np.minimum(adjusted_p_sorted, 1.0)
        
        # Map adjusted p-values back to original order
        adjusted_p = np.zeros(n)
        adjusted_p[sorted_indices] = adjusted_p_sorted
        
        # Update the model results
        for i, cov_name in enumerate(covariate_list):
            model_results[model_type][cov_name]['fdr_rejected'] = bool(rejected_mask[i])
            model_results[model_type][cov_name]['fdr_adjusted_p'] = float(adjusted_p[i])
            
        logger.info(f"Model '{model_type}': {sum(rejected_mask)}/{len(rejected_mask)} primary covariates rejected after FDR correction.")
        
    return model_results

def main():
    """
    Main entry point to apply FDR correction to model results.
    Assumes model results are saved in data/processed/model_results.json
    and writes the FDR-corrected results to data/processed/model_results_fdr.json
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "model_results.json"
    output_path = project_root / "data" / "processed" / "model_results_fdr.json"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
        
    try:
        # Load model results
        with open(input_path, 'r') as f:
            model_results = json.load(f)
            
        # Define primary covariates (based on typical urban noise study)
        # These should match the covariates used in the models
        primary_covariates = [
            'traffic_volume', 
            'population_density', 
            'land_use_commercial',
            'land_use_industrial',
            'distance_to_road',
            'building_height'
        ]
        
        # Apply FDR correction
        corrected_results = apply_fdr_to_model_results(
            model_results, 
            primary_covariates, 
            alpha=0.05
        )
        
        # Save results
        with open(output_path, 'w') as f:
            json.dump(corrected_results, f, indent=2)
            
        logger.info(f"FDR-corrected results saved to: {output_path}")
        return 0
        
    except Exception as e:
        logger.exception(f"Error applying FDR correction: {e}")
        return 1

if __name__ == "__main__":
    import json
    import sys
    sys.exit(main())
