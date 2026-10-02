"""
T019: Bonferroni Correction Implementation

Implements multiple-comparison correction (Bonferroni) for:
- perseverative_errors
- categories_completed

Uses scipy.stats.multipletests with method='bonferroni' to adjust p-values.
Reads statistical results from T018 (Welch's t-test output) and writes corrected
results to data/results/bonferroni_corrected.json.

Depends on: T018
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from scipy import stats

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
STATISTICAL_RESULTS_PATH = PROJECT_ROOT / "data" / "results" / "statistical_analysis.json"
BONFERRONI_OUTPUT_PATH = PROJECT_ROOT / "data" / "results" / "bonferroni_corrected.json"

def load_statistical_results() -> Dict[str, Any]:
    """
    Load statistical results from T018 (Welch's t-test output).
    
    Returns:
        Dict containing p-values, t-statistics, and other metrics for
        perseverative_errors and categories_completed comparisons.
        
    Raises:
        FileNotFoundError: If the statistical results file doesn't exist.
        ValueError: If the file is empty or malformed.
    """
    if not STATISTICAL_RESULTS_PATH.exists():
        logger.error(f"Statistical results file not found: {STATISTICAL_RESULTS_PATH}")
        raise FileNotFoundError(
            f"Statistical results file not found: {STATISTICAL_RESULTS_PATH}. "
            "Ensure T018 (Welch's t-test) has been run successfully."
        )
    
    with open(STATISTICAL_RESULTS_PATH, 'r') as f:
        data = json.load(f)
    
    if not data:
        logger.error("Statistical results file is empty")
        raise ValueError("Statistical results file is empty")
    
    logger.info(f"Loaded statistical results from {STATISTICAL_RESULTS_PATH}")
    return data

def apply_bonferroni_correction(
    statistical_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to multiple comparisons.
    
    The Bonferroni correction adjusts p-values to control the family-wise error rate
    when performing multiple hypothesis tests. It multiplies each p-value by the
    number of comparisons (n), capped at 1.0.
    
    Args:
        statistical_results: Dictionary containing raw p-values from Welch's t-test
                            for perseverative_errors and categories_completed.
    
    Returns:
        Dictionary containing corrected p-values and significance flags.
        
    Raises:
        KeyError: If expected keys are missing from statistical results.
    """
    # Define the metrics we're correcting for
    metrics = ['perseverative_errors', 'categories_completed']
    
    # Extract raw p-values for each metric
    p_values = []
    metric_names = []
    
    for metric in metrics:
        if metric not in statistical_results:
            logger.error(f"Missing metric in statistical results: {metric}")
            raise KeyError(f"Missing metric in statistical results: {metric}")
        
        # Get p-value from the results
        p_val = statistical_results[metric].get('p_value')
        if p_val is None:
            logger.error(f"p_value is None for {metric}")
            raise ValueError(f"p_value is None for {metric}")
        
        p_values.append(float(p_val))
        metric_names.append(metric)
        logger.info(f"Raw p-value for {metric}: {p_val:.6f}")
    
    # Apply Bonferroni correction using scipy.stats.multipletests
    # method='bonferroni' multiplies p-values by n_tests and caps at 1.0
    corrected_results = stats.multipletests(
        p_values,
        method='bonferroni'
    )
    
    # corrected_pvalues, reject, pvalues_corrected, alphac_sidak
    corrected_pvalues = corrected_results[0]
    reject_flags = corrected_results[1]
    
    # Build the output dictionary
    bonferroni_results = {
        'correction_method': 'bonferroni',
        'n_comparisons': len(metrics),
        'alpha_level': 0.05,
        'adjusted_alpha': 0.05 / len(metrics),
        'results': {}
    }
    
    for i, metric in enumerate(metric_names):
        raw_p = p_values[i]
        corrected_p = float(corrected_pvalues[i])
        is_significant = bool(reject_flags[i])
        
        bonferroni_results['results'][metric] = {
            'raw_p_value': raw_p,
            'corrected_p_value': corrected_p,
            'is_significant_at_0.05': is_significant,
            'significance_status': 'significant' if is_significant else 'not_significant'
        }
        
        logger.info(
            f"BONFERRONI CORRECTION - {metric}: "
            f"raw_p={raw_p:.6f} -> corrected_p={corrected_p:.6f}, "
            f"significant={is_significant}"
        )
    
    return bonferroni_results

def save_bonferroni_results(
    bonferroni_results: Dict[str, Any],
    output_path: Path = BONFERRONI_OUTPUT_PATH
) -> None:
    """
    Save Bonferroni correction results to JSON file.
    
    Args:
        bonferroni_results: Dictionary containing corrected p-values and metadata.
        output_path: Path to save the results file.
        
    Raises:
        IOError: If unable to write to the output path.
    """
    # Ensure the results directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(bonferroni_results, f, indent=2)
    
    logger.info(f"Bonferroni correction results saved to {output_path}")

def main() -> int:
    """
    Main entry point for T019: Bonferroni Correction.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        logger.info("=" * 60)
        logger.info("T019: Bonferroni Correction Implementation")
        logger.info("=" * 60)
        
        # Step 1: Load statistical results from T018
        logger.info("Loading statistical results from T018...")
        statistical_results = load_statistical_results()
        
        # Step 2: Apply Bonferroni correction
        logger.info("Applying Bonferroni correction...")
        bonferroni_results = apply_bonferroni_correction(statistical_results)
        
        # Step 3: Save corrected results
        logger.info("Saving Bonferroni correction results...")
        save_bonferroni_results(bonferroni_results)
        
        # Step 4: Log summary
        logger.info("=" * 60)
        logger.info("BONFERRONI CORRECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Number of comparisons: {bonferroni_results['n_comparisons']}")
        logger.info(f"Adjusted alpha level: {bonferroni_results['adjusted_alpha']:.4f}")
        
        for metric, results in bonferroni_results['results'].items():
            logger.info(f"\n{metric}:")
            logger.info(f"  Raw p-value:      {results['raw_p_value']:.6f}")
            logger.info(f"  Corrected p-value: {results['corrected_p_value']:.6f}")
            logger.info(f"  Significant (α=0.05): {results['significance_status']}")
        
        logger.info("=" * 60)
        logger.info("T019 COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"FILE NOT FOUND ERROR: {e}")
        logger.error("Ensure T018 (Welch's t-test) has been run successfully.")
        return 1
        
    except KeyError as e:
        logger.error(f"KEY ERROR: {e}")
        logger.error("Statistical results file is missing required keys.")
        return 1
        
    except ValueError as e:
        logger.error(f"VALUE ERROR: {e}")
        return 1
        
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit(main())
