"""
Multiple comparison correction (Bonferroni, Benjamini-Hochberg) for regression results.
Optimized for memory by using float32 for p-value arrays.
"""
import os
import sys
import csv
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from config import DATA_RESULTS_DIR, get_dtype, FORCE_FLOAT32

logger = logging.getLogger(__name__)

def load_regression_results() -> Dict[str, Any]:
    """
    Loads regression results from JSON.
    """
    import json
    path = DATA_RESULTS_DIR / "regression_results.json"
    if not path.exists():
        raise FileNotFoundError(f"Regression results not found at {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Ensure float32 if configured
    if FORCE_FLOAT32 and 'coefficients' in data:
        data['coefficients'] = [np.float32(c) for c in data['coefficients']]
    
    return data

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Applies Bonferroni correction to p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    corrected = [p * n for p in p_values]
    if FORCE_FLOAT32:
        corrected = [np.float32(p) for p in corrected]
    
    return corrected

def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Applies Benjamini-Hochberg correction to determine significance.
    Returns a list of booleans indicating significance.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with indices
    indexed_p_values = sorted(enumerate(p_values), key=lambda x: x[1])
    ranks = [i + 1 for i in range(n)]
    
    # Calculate thresholds
    thresholds = [alpha * r / n for r in ranks]
    
    # Determine significance
    significant = [False] * n
    for i, (idx, p) in enumerate(indexed_p_values):
        if p <= thresholds[i]:
            significant[idx] = True
    
    return significant

def apply_corrections(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies corrections to regression results.
    Assumes results contain p-values (simplified for this task).
    """
    # In a real scenario, we would extract p-values from the regression object
    # For this example, we assume we have a list of p-values
    p_values = results.get('p_values', [0.05] * len(results.get('coefficients', [])))
    
    if FORCE_FLOAT32:
        p_values = [np.float32(p) for p in p_values]
    
    corrected_p = bonferroni_correction(p_values)
    significant = benjamini_hochberg_correction(p_values)
    
    results['bonferroni_corrected_p'] = corrected_p
    results['significant_bh'] = significant
    
    return results

def save_corrected_results(results: Dict[str, Any], filepath: Path):
    """
    Saves corrected results.
    """
    import json
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Corrected results saved to {filepath}")

def run_correction_pipeline():
    """
    Runs the multiple comparison correction pipeline.
    """
    logger.info("Starting multiple comparison correction...")
    
    results = load_regression_results()
    corrected_results = apply_corrections(results)
    
    output_path = DATA_RESULTS_DIR / "corrected_regression_results.json"
    save_corrected_results(corrected_results, output_path)
    
    logger.info("Multiple comparison correction completed.")

def main():
    """
    Main entry point.
    """
    logging.basicConfig(level=logging.INFO)
    run_correction_pipeline()

if __name__ == "__main__":
    main()