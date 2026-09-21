"""
FDR Correction Module for Power Curve Analysis.

Implements Benjamini-Hochberg procedure for multiple comparison correction
across paradigms in statistical power analysis.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FDRCorrectionError(Exception):
    """Custom exception for FDR correction failures."""
    pass


def benjamini_hochberg(
    p_values: np.ndarray,
    alpha: float = 0.05,
    method: str = 'indep'
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Perform Benjamini-Hochberg FDR correction on a list of p-values.

    Args:
        p_values: Array of p-values to correct.
        alpha: Significance level (default 0.05).
        method: 'indep' for independent tests or 'neg' for negative dependent tests.

    Returns:
        Tuple of (reject_mask, adjusted_p_values, fdr_threshold).
        - reject_mask: Boolean array indicating which hypotheses are rejected.
        - adjusted_p_values: FDR-adjusted p-values.
        - fdr_threshold: The threshold used for rejection.

    Raises:
        FDRCorrectionError: If input is invalid or correction fails.
    """
    if p_values is None or len(p_values) == 0:
        raise FDRCorrectionError("Input p-values array is empty or None.")

    p_values = np.asarray(p_values, dtype=float)

    if np.any(p_values < 0) or np.any(p_values > 1):
        raise FDRCorrectionError("All p-values must be between 0 and 1.")

    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]

    # Calculate BH thresholds
    ranks = np.arange(1, n + 1)
    if method == 'indep':
        thresholds = (ranks / n) * alpha
    elif method == 'neg':
        # For negative dependence, use sum(1/i)
        c_n = sum(1.0 / i for i in range(1, n + 1))
        thresholds = (ranks / (n * c_n)) * alpha
    else:
        raise FDRCorrectionError(f"Unknown method: {method}. Use 'indep' or 'neg'.")

    # Find the largest k such that p_(k) <= threshold_(k)
    # We need to find the last index where sorted_p <= threshold
    # To handle floating point issues, we use a small epsilon
    mask = sorted_p_values <= thresholds
    if not np.any(mask):
        # No rejections
        reject_mask = np.zeros(n, dtype=bool)
        adjusted_p_values = np.minimum(np.minimum.accumulate(1 - sorted_p_values[::-1])[::-1], 1.0)
        adjusted_p_values = np.minimum(adjusted_p_values, 1.0)
        return reject_mask, adjusted_p_values, 0.0

    # Find the largest k
    k = np.max(np.where(mask)[0])
    fdr_threshold = thresholds[k]

    # Construct rejection mask
    reject_mask = np.zeros(n, dtype=bool)
    reject_mask[sorted_indices[:k+1]] = True

    # Calculate adjusted p-values (monotonically increasing)
    # adj_p_i = min(1, min_{j>=i} (n/j * p_j))
    adjusted_p_values = np.zeros(n)
    running_min = 1.0
    for i in range(n - 1, -1, -1):
        idx = sorted_indices[i]
        val = sorted_p_values[i] * n / (i + 1)
        running_min = min(running_min, val)
        adjusted_p_values[idx] = running_min

    adjusted_p_values = np.minimum(adjusted_p_values, 1.0)

    return reject_mask, adjusted_p_values, fdr_threshold


def apply_fdr_to_power_curves(
    power_curves_data: Dict[str, Any],
    alpha: float = 0.05,
    method: str = 'indep'
) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg FDR correction to power curve results across paradigms.

    This function extracts p-values from the logistic regression model results
    for each paradigm, applies FDR correction, and returns the corrected results.

    Args:
        power_curves_data: Dictionary containing power curve results with 'paradigm_results' list.
                           Each paradigm result should have 'model_stats' containing 'p_values'.
        alpha: Significance level for FDR correction (default 0.05).
        method: 'indep' or 'neg' for BH method.

    Returns:
        Dictionary with original data plus 'fdr_corrected' section containing:
        - adjusted_p_values
        - rejection_mask
        - fdr_threshold
        - corrected_significance (boolean per paradigm)
    """
    if 'paradigm_results' not in power_curves_data:
        raise FDRCorrectionError("Input data missing 'paradigm_results' key.")

    paradigm_results = power_curves_data['paradigm_results']
    if not paradigm_results:
        logger.warning("No paradigm results found to correct.")
        return power_curves_data

    # Extract p-values from each paradigm's model statistics
    p_values = []
    paradigm_names = []

    for idx, result in enumerate(paradigm_results):
        if 'model_stats' not in result:
            logger.warning(f"Paradigm {idx} missing 'model_stats', skipping.")
            continue
        
        stats = result['model_stats']
        if 'p_values' not in stats:
            logger.warning(f"Paradigm {idx} missing 'p_values' in model_stats, skipping.")
            continue

        # Get p-values for the sample size coefficient (usually the first non-intercept)
        # Assuming the model is: replication_success ~ sample_size
        # The p_value for sample_size is what we care about
        p_vals = stats['p_values']
        
        # If p_values is a dict, extract the relevant one
        if isinstance(p_vals, dict):
            # Look for the sample_size or similar coefficient
            key = next((k for k in p_vals.keys() if 'sample' in k.lower() or 'size' in k.lower()), None)
            if key is None:
                # Fallback to first non-intercept
                keys = list(p_vals.keys())
                key = keys[1] if len(keys) > 1 else keys[0]
            p_val = p_vals[key]
        elif isinstance(p_vals, (list, np.ndarray)):
            # Assume first non-intercept or the only value
            p_val = p_vals[1] if len(p_vals) > 1 else p_vals[0]
        else:
            p_val = float(p_vals)

        p_values.append(p_val)
        paradigm_names.append(result.get('paradigm_name', f'paradigm_{idx}'))

    if len(p_values) == 0:
        raise FDRCorrectionError("No valid p-values found for correction.")

    logger.info(f"Applying FDR correction to {len(p_values)} paradigms at alpha={alpha}")

    # Apply BH correction
    reject_mask, adjusted_p_values, fdr_threshold = benjamini_hochberg(
        np.array(p_values), alpha=alpha, method=method
    )

    # Construct corrected results
    corrected_results = {
        'alpha': alpha,
        'method': method,
        'fdr_threshold': float(fdr_threshold),
        'paradigm_names': paradigm_names,
        'original_p_values': p_values,
        'adjusted_p_values': adjusted_p_values.tolist(),
        'rejection_mask': reject_mask.tolist(),
        'corrected_significance': [bool(r) for r in reject_mask],
        'num_significant': int(np.sum(reject_mask)),
        'num_tested': len(p_values)
    }

    # Add to power curves data
    output = power_curves_data.copy()
    output['fdr_corrected'] = corrected_results

    logger.info(f"FDR correction complete: {corrected_results['num_significant']}/{corrected_results['num_tested']} significant")

    return output


def main():
    """
    Main entry point for FDR correction script.
    
    Reads power curve results from data/aggregated/power_curves.json,
    applies Benjamini-Hochberg FDR correction, and writes to
    data/aggregated/corrected_power_curves.json.
    """
    # Define paths
    input_path = Path('data/aggregated/power_curves.json')
    output_path = Path('data/aggregated/corrected_power_curves.json')

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading power curves from {input_path}")
    with open(input_path, 'r') as f:
        power_curves_data = json.load(f)

    # Parse arguments (optional)
    parser = argparse.ArgumentParser(description='Apply FDR correction to power curves')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    parser.add_argument('--method', type=str, default='indep', choices=['indep', 'neg'], help='BH method')
    args = parser.parse_args()

    try:
        corrected_data = apply_fdr_to_power_curves(
            power_curves_data,
            alpha=args.alpha,
            method=args.method
        )
    except FDRCorrectionError as e:
        logger.error(f"FDR correction failed: {e}")
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing corrected results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(corrected_data, f, indent=2)

    logger.info("FDR correction completed successfully")
    print(f"Corrected power curves saved to: {output_path}")


if __name__ == '__main__':
    main()
