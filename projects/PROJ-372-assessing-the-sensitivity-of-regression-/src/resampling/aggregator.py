"""
Aggregator module for resampling results.

This module handles the aggregation of OLS coefficient results from multiple
random subsets, calculates empirical standard deviations, and performs
convergence analysis to verify stability of the estimates.
"""
import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from src.utils.config import SAMPLE_SIZE_TIERS
from src.models.data_models import StabilityResult

logger = logging.getLogger(__name__)

def calculate_empirical_sd(coefficients: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Calculate the empirical standard deviation of coefficients across subsets.
    
    Args:
        coefficients: List of coefficient dictionaries from each subset fit.
                      Each dict maps coefficient name to value.
    
    Returns:
        Dictionary mapping coefficient name to its empirical standard deviation.
    """
    if not coefficients:
        return {}
    
    # Convert list of dicts to DataFrame for easy calculation
    df = pd.DataFrame(coefficients)
    
    # Calculate standard deviation for each coefficient
    sd_result = df.std().to_dict()
    
    return sd_result

def calculate_se_of_sd(sd_values: List[float], n_subsets: int) -> float:
    """
    Calculate the Standard Error of the Standard Deviation.
    
    For a normal distribution, the standard error of the sample standard deviation
    is approximately sigma / sqrt(2 * n), where sigma is the true SD and n is
    the sample size (number of subsets).
    
    Args:
        sd_values: List of SD values calculated from different batch sizes
                   (e.g., SD from 50 subsets, SD from 100 subsets, etc.)
        n_subsets: The number of subsets used to calculate the final SD
    
    Returns:
        Standard Error of the SD estimate.
    """
    if not sd_values or n_subsets < 2:
        return 0.0
    
    # Use the final SD value as the estimate of sigma
    final_sd = sd_values[-1] if sd_values else 0.0
    
    if final_sd == 0.0:
        return 0.0
    
    # SE of SD ≈ sigma / sqrt(2 * n)
    se_sd = final_sd / np.sqrt(2 * n_subsets)
    
    return se_sd

def check_convergence(
    results_by_tier: Dict[int, List[Dict[str, Any]]],
    target_subsets: int = 200,
    convergence_threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Check convergence of coefficient SD estimates across increasing subset counts.
    
    This function compares SD estimates from different numbers of subsets to
    verify that the estimates have stabilized. It calculates the Standard Error
    of the SD and checks if the relative change between 150 and 200 subsets
    is within the threshold.
    
    Args:
        results_by_tier: Dictionary mapping sample size tier to list of results.
        target_subsets: Target number of subsets for convergence check.
        convergence_threshold: Maximum allowed relative change for convergence.
    
    Returns:
        Dictionary containing convergence analysis results.
    """
    convergence_data = {}
    
    for tier, results in results_by_tier.items():
        if not results:
            continue
        
        # Group results by subset count if available
        subset_counts = {}
        for result in results:
            count = result.get('subset_count', 0)
            if count > 0:
                if count not in subset_counts:
                    subset_counts[count] = []
                subset_counts[count].append(result)
        
        if not subset_counts:
            continue
        
        # Calculate SD for each subset count
        sd_by_count = {}
        for count, subset_results in subset_counts.items():
            # Aggregate all coefficients from this batch
            all_coeffs = []
            for sr in subset_results:
                coeffs = sr.get('coefficients', {})
                if coeffs:
                    all_coeffs.append(coeffs)
            
            if all_coeffs:
                sd_vals = calculate_empirical_sd(all_coeffs)
                sd_by_count[count] = sd_vals
        
        if not sd_by_count:
            continue
        
        # Sort by subset count
        sorted_counts = sorted(sd_by_count.keys())
        
        # Find the 150 and 200 subset results (or closest available)
        sd_150 = None
        sd_200 = None
        count_150 = None
        count_200 = None
        
        for count in sorted_counts:
            if count >= 200 and sd_200 is None:
                sd_200 = sd_by_count[count]
                count_200 = count
            elif count >= 150 and count < 200 and sd_150 is None:
                sd_150 = sd_by_count[count]
                count_150 = count
            elif count >= 150 and sd_150 is None:
                sd_150 = sd_by_count[count]
                count_150 = count
        
        # If we don't have 150/200, use the largest available
        if sd_150 is None and sorted_counts:
            max_count = sorted_counts[-1]
            sd_150 = sd_by_count[max_count]
            count_150 = max_count
        
        if sd_200 is None and sorted_counts:
            max_count = sorted_counts[-1]
            sd_200 = sd_by_count[max_count]
            count_200 = max_count
        
        if sd_150 is None or sd_200 is None:
            continue
        
        # Calculate relative change
        relative_changes = {}
        se_values = {}
        
        for coef in sd_150.keys():
            if coef in sd_200:
                val_150 = sd_150[coef]
                val_200 = sd_200[coef]
                
                if val_150 > 0:
                    rel_change = abs(val_200 - val_150) / val_150
                else:
                    rel_change = 0.0 if val_200 == 0 else float('inf')
                
                relative_changes[coef] = rel_change
                
                # Calculate SE of SD
                n_subsets = count_200 if count_200 else target_subsets
                se_values[coef] = calculate_se_of_sd(
                    [val_150, val_200], 
                    n_subsets
                )
        
        # Determine if converged
        converged = all(
            rel_change <= convergence_threshold 
            for rel_change in relative_changes.values()
            if rel_change != float('inf')
        )
        
        convergence_data[tier] = {
            'subset_counts_analyzed': sorted_counts,
            'sd_at_150': sd_150,
            'sd_at_200': sd_200,
            'relative_changes': relative_changes,
            'se_of_sd': se_values,
            'converged': converged,
            'threshold': convergence_threshold
        }
    
    return convergence_data

def log_convergence_results(
    convergence_data: Dict[str, Any],
    output_path: str = 'artifacts/convergence.log'
) -> None:
    """
    Log convergence analysis results to a file.
    
    Args:
        convergence_data: Dictionary containing convergence analysis results.
        output_path: Path to the output log file.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("CONVERGENCE ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Analysis generated at: {pd.Timestamp.now()}\n")
        f.write(f"Convergence threshold: 5%\n\n")
        
        all_converged = True
        
        for tier, data in convergence_data.items():
            f.write(f"--- Sample Size Tier: {tier}% ---\n")
            f.write(f"Subset counts analyzed: {data['subset_counts_analyzed']}\n")
            f.write(f"Converged: {data['converged']}\n\n")
            
            if not data['converged']:
                all_converged = False
            
            f.write("Coefficient-wise Analysis:\n")
            for coef, rel_change in data['relative_changes'].items():
                se_val = data['se_of_sd'].get(coef, 0.0)
                status = "✓" if rel_change <= data['threshold'] else "✗"
                f.write(f"  {coef}: {status}\n")
                f.write(f"    SD (150 subsets): {data['sd_at_150'].get(coef, 'N/A'):.6f}\n")
                f.write(f"    SD (200 subsets): {data['sd_at_200'].get(coef, 'N/A'):.6f}\n")
                f.write(f"    Relative change: {rel_change:.4%}\n")
                f.write(f"    SE of SD: {se_val:.6f}\n\n")
            
            f.write("-" * 40 + "\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("SUMMARY\n")
        f.write("=" * 80 + "\n")
        f.write(f"Overall convergence status: {'CONVERGED' if all_converged else 'NOT CONVERGED'}\n")
        f.write(f"Threshold for convergence: {data.get('threshold', 0.05) if data else 0.05}\n")
        f.write("=" * 80 + "\n")
        
        # Also save as JSON for programmatic access
        json_path = output_path.replace('.log', '.json')
        with open(json_path, 'w') as jf:
            json.dump(convergence_data, jf, indent=2, default=str)
        
        logger.info(f"Convergence analysis logged to {output_path}")
        logger.info(f"JSON results saved to {json_path}")

def run_convergence_check(
    stability_results_path: str,
    output_log_path: str = 'artifacts/convergence.log',
    target_subsets: int = 200
) -> Dict[str, Any]:
    """
    Main function to run convergence check on stability results.
    
    Args:
        stability_results_path: Path to the stability results file (JSON/CSV).
        output_log_path: Path for the convergence log output.
        target_subsets: Target number of subsets for convergence check.
    
    Returns:
        Dictionary containing convergence analysis results.
    """
    logger.info(f"Loading stability results from {stability_results_path}")
    
    # Load results
    if stability_results_path.endswith('.json'):
        with open(stability_results_path, 'r') as f:
            results = json.load(f)
    elif stability_results_path.endswith('.csv'):
        results = pd.read_csv(stability_results_path).to_dict('records')
    else:
        raise ValueError(f"Unsupported file format: {stability_results_path}")
    
    # Group by tier
    results_by_tier = {}
    for result in results:
        tier = result.get('sample_size_tier', 0)
        if tier not in results_by_tier:
            results_by_tier[tier] = []
        results_by_tier[tier].append(result)
    
    logger.info(f"Found {len(results_by_tier)} tiers with results")
    
    # Perform convergence check
    convergence_data = check_convergence(
        results_by_tier, 
        target_subsets=target_subsets
    )
    
    # Log results
    log_convergence_results(convergence_data, output_log_path)
    
    return convergence_data

def aggregate_stability_results(
    results: List[StabilityResult],
    output_path: str = 'artifacts/stability/aggregated_results.json'
) -> Dict[str, Any]:
    """
    Aggregate stability results across all tiers and calculate final metrics.
    
    Args:
        results: List of StabilityResult objects.
        output_path: Path to save aggregated results.
    
    Returns:
        Dictionary containing aggregated stability metrics.
    """
    logger.info(f"Aggregating {len(results)} stability results")
    
    # Group by tier
    by_tier = {}
    for result in results:
        tier = result.sample_size_tier
        if tier not in by_tier:
            by_tier[tier] = []
        by_tier[tier].append(result)
    
    aggregated = {}
    
    for tier, tier_results in by_tier.items():
        # Collect all coefficients
        all_coeffs = []
        for r in tier_results:
            if r.coefficients:
                all_coeffs.append(r.coefficients)
        
        if not all_coeffs:
            continue
        
        # Calculate empirical SD
        sd_values = calculate_empirical_sd(all_coeffs)
        
        # Calculate mean coefficients
        mean_coeffs = pd.DataFrame(all_coeffs).mean().to_dict()
        
        aggregated[tier] = {
            'sample_size_tier': tier,
            'num_subsets': len(tier_results),
            'mean_coefficients': mean_coeffs,
            'empirical_sd': sd_values,
            'valid_subsets': len(tier_results)
        }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(aggregated, f, indent=2, default=str)
    
    logger.info(f"Aggregated results saved to {output_path}")
    
    return aggregated

def verify_convergence_criteria(
    convergence_data: Dict[str, Any],
    threshold: float = 0.05
) -> bool:
    """
    Verify that convergence criteria are met (SC-005).
    
    Args:
        convergence_data: Dictionary from check_convergence().
        threshold: Maximum allowed relative change (default 5%).
    
    Returns:
        True if all tiers have converged, False otherwise.
    """
    for tier, data in convergence_data.items():
        if not data.get('converged', False):
            logger.warning(f"Tier {tier} did not converge")
            return False
    
    logger.info("All tiers converged within threshold")
    return True