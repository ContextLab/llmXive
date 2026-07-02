"""
Multiple Comparison Correction for Regression Results.

Implements Bonferroni and Benjamini-Hochberg (BH) corrections for the
regression results generated in T029b3 (data/results/regression_results.csv).

This addresses FR-005 requirement for statistical rigor in hypothesis testing.
"""
import os
import sys
import csv
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Project imports
from config import DATA_RESULTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_regression_results(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load regression results from CSV.
    
    Expected columns: term, coef, std_err, p_value, lower_ci, upper_ci
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Regression results file not found: {filepath}")
    
    results = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'term': row['term'],
                'coef': float(row['coef']),
                'std_err': float(row['std_err']),
                'p_value': float(row['p_value']),
                'lower_ci': float(row['lower_ci']),
                'upper_ci': float(row['upper_ci']),
                'original_p': float(row['p_value'])
            })
    
    logger.info(f"Loaded {len(results)} regression terms from {filepath}")
    return results

def bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    The Bonferroni correction multiplies each p-value by the number of tests (m),
    capping the result at 1.0. It is a conservative method controlling the 
    Family-Wise Error Rate (FWER).
    
    Args:
        p_values: List of raw p-values from hypothesis tests.
        
    Returns:
        List of corrected p-values.
    """
    m = len(p_values)
    if m == 0:
        return []
    
    corrected = []
    for p in p_values:
        # p_adj = min(p * m, 1.0)
        adj = p * m
        corrected.append(min(adj, 1.0))
    
    logger.info(f"Bonferroni correction applied to {m} tests")
    return corrected

def benjamini_hochberg_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg (BH) correction to a list of p-values.
    
    The BH procedure controls the False Discovery Rate (FDR). It is less 
    conservative than Bonferroni and more powerful when many hypotheses are tested.
    
    Algorithm:
    1. Sort p-values: p(1) <= p(2) <= ... <= p(m)
    2. Calculate critical values: (i/m) * alpha (we return the adjusted p-values)
    3. Adjusted p-value for p(i) is min(p(j) * m / j for j >= i)
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of adjusted p-values corresponding to the input order.
    """
    m = len(p_values)
    if m == 0:
        return []
    
    # Create list of (original_index, p_value)
    indexed_p = list(enumerate(p_values))
    # Sort by p-value
    indexed_p.sort(key=lambda x: x[1])
    
    # Calculate adjusted p-values
    # Start from the largest p-value and work backwards to ensure monotonicity
    # adjusted_p[i] = min( (p(j) * m) / j for j >= i )
    
    adj_p_sorted = [0.0] * m
    min_so_far = 1.0
    
    # Iterate from largest to smallest index in the sorted list
    for i in range(m - 1, -1, -1):
        orig_idx, p_val = indexed_p[i]
        rank = i + 1  # 1-based rank
        # BH adjusted p-value formula: p * m / rank
        adj = (p_val * m) / rank
        # Ensure monotonicity: adjusted p-values should not decrease as we go to smaller ranks
        if adj > min_so_far:
            adj = min_so_far
        min_so_far = adj
        adj_p_sorted[i] = min(adj, 1.0)
    
    # Map back to original order
    final_adjusted = [0.0] * m
    for i, adj_val in enumerate(adj_p_sorted):
        orig_idx = indexed_p[i][0]
        final_adjusted[orig_idx] = adj_val
    
    logger.info(f"Benjamini-Hochberg correction applied to {m} tests")
    return final_adjusted

def apply_corrections(results: List[Dict[str, Any]], method: str = 'bonferroni') -> List[Dict[str, Any]]:
    """
    Apply multiple comparison correction to regression results.
    
    Args:
        results: List of regression result dictionaries containing 'p_value'.
        method: Either 'bonferroni' or 'bh' (Benjamini-Hochberg).
        
    Returns:
        List of results with added 'p_value_corrected' and 'significant' keys.
    """
    if not results:
        logger.warning("No results to correct")
        return results
    
    p_values = [r['p_value'] for r in results]
    
    if method.lower() == 'bonferroni':
        corrected_p = bonferroni_correction(p_values)
    elif method.lower() in ('bh', 'benjamini-hochberg'):
        corrected_p = benjamini_hochberg_correction(p_values)
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    # Update results
    for i, result in enumerate(results):
        result['p_value_corrected'] = corrected_p[i]
        result['significant'] = corrected_p[i] < 0.05
        result['correction_method'] = method
    
    return results

def save_corrected_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save corrected regression results to CSV.
    """
    if not results:
        logger.warning("No results to save")
        return
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'term', 'coef', 'std_err', 'p_value', 'p_value_corrected', 
        'lower_ci', 'upper_ci', 'significant', 'correction_method'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved corrected results to {output_path}")

def run_correction_pipeline(input_path: Optional[Path] = None, 
                            output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main pipeline to load regression results, apply corrections, and save.
    
    Args:
        input_path: Path to input regression results CSV. Defaults to 
                   data/results/regression_results.csv.
        output_path: Path to output corrected results CSV. Defaults to
                    data/results/regression_results_corrected.csv.
                    
    Returns:
        Dictionary with summary statistics of the correction.
    """
    if input_path is None:
        input_path = DATA_RESULTS_DIR / "regression_results.csv"
    if output_path is None:
        output_path = DATA_RESULTS_DIR / "regression_results_corrected.csv"
    
    logger.info(f"Starting multiple comparison correction pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Load results
    results = load_regression_results(input_path)
    
    # Apply Bonferroni
    results_bonf = apply_corrections(results.copy(), method='bonferroni')
    save_corrected_results(results_bonf, output_path.with_name("regression_results_bonferroni.csv"))
    
    # Apply Benjamini-Hochberg
    results_bh = apply_corrections(results.copy(), method='bh')
    save_corrected_results(results_bh, output_path.with_name("regression_results_bh.csv"))
    
    # Summary statistics
    summary = {
        'total_tests': len(results),
        'significant_bonferroni': sum(1 for r in results_bonf if r['significant']),
        'significant_bh': sum(1 for r in results_bh if r['significant']),
        'input_file': str(input_path),
        'output_files': [
            str(output_path.with_name("regression_results_bonferroni.csv")),
            str(output_path.with_name("regression_results_bh.csv"))
        ]
    }
    
    logger.info(f"Pipeline complete. Significant terms (Bonferroni): {summary['significant_bonferroni']}")
    logger.info(f"Significant terms (BH): {summary['significant_bh']}")
    
    return summary

def main():
    """Entry point for command line execution."""
    try:
        summary = run_correction_pipeline()
        print(f"Correction completed successfully.")
        print(f"Total tests: {summary['total_tests']}")
        print(f"Significant (Bonferroni): {summary['significant_bonferroni']}")
        print(f"Significant (BH): {summary['significant_bh']}")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())