import numpy as np
import json
import logging
from pathlib import Path
from statsmodels.stats.multitest import fdrcorrection
import code.config as config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_fdr_to_results(p_values: list, alpha: float = 0.05) -> dict:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Args:
        p_values: List of p-values to correct.
        alpha: Significance threshold (default 0.05).

    Returns:
        Dictionary containing:
            - 'p_values': Original p-values
            - 'corrected_p_values': FDR-corrected p-values
            - 'is_significant': Boolean mask of significant results
            - 'num_significant': Count of significant results
    """
    if not p_values:
        return {
            'p_values': [],
            'corrected_p_values': [],
            'is_significant': [],
            'num_significant': 0
        }

    # Apply FDR correction
    reject, pvals_corrected, _, _ = fdrcorrection(np.array(p_values), alpha=alpha, method='indep')

    return {
        'p_values': p_values,
        'corrected_p_values': pvals_corrected.tolist(),
        'is_significant': reject.tolist(),
        'num_significant': int(np.sum(reject))
    }

def run_fdr_correction_pipeline(
    decoder_metrics_path: str,
    rsa_metrics_path: str,
    output_path: str
) -> dict:
    """
    Run FDR correction pipeline across narrative categories and ROIs.

    This function:
    1. Loads decoder metrics (accuracy/p-values) for each narrative category
    2. Loads RSA metrics (dissimilarity comparisons) for each ROI
    3. Aggregates all p-values
    4. Applies FDR correction
    5. Writes results to output file

    Args:
        decoder_metrics_path: Path to decoder_metrics.json
        rsa_metrics_path: Path to rsa_metrics.json (or group_rsa_stats.json)
        output_path: Path to write fdr_corrected_results.json

    Returns:
        Dictionary with FDR correction results
    """
    logger.info(f"Loading decoder metrics from {decoder_metrics_path}")
    try:
        with open(decoder_metrics_path, 'r') as f:
            decoder_data = json.load(f)
    except FileNotFoundError:
        logger.warning(f"Decoder metrics file not found: {decoder_metrics_path}")
        decoder_data = {}

    logger.info(f"Loading RSA metrics from {rsa_metrics_path}")
    try:
        with open(rsa_metrics_path, 'r') as f:
            rsa_data = json.load(f)
    except FileNotFoundError:
        logger.warning(f"RSA metrics file not found: {rsa_metrics_path}")
        rsa_data = {}

    # Collect all p-values from decoder results
    decoder_p_values = []
    decoder_labels = []

    if 'per_category' in decoder_data:
        for category, metrics in decoder_data['per_category'].items():
            if 'p_value' in metrics:
                decoder_p_values.append(metrics['p_value'])
                decoder_labels.append(f"decoder_{category}")

    # Collect p-values from RSA results (early vs late comparisons)
    rsa_p_values = []
    rsa_labels = []

    if 'group_stats' in rsa_data:
        for roi, stats in rsa_data['group_stats'].items():
            if 'early_late_p_value' in stats:
                rsa_p_values.append(stats['early_late_p_value'])
                rsa_labels.append(f"rsa_{roi}_early_late")
            if 'early_early_p_value' in stats:
                rsa_p_values.append(stats['early_early_p_value'])
                rsa_labels.append(f"rsa_{roi}_early_early")

    # Combine all p-values
    all_p_values = decoder_p_values + rsa_p_values
    all_labels = decoder_labels + rsa_labels

    if not all_p_values:
        logger.warning("No p-values found to correct. Writing empty result.")
        result = {
            'decoder_results': apply_fdr_to_results(decoder_p_values),
            'rsa_results': apply_fdr_to_results(rsa_p_values),
            'combined_results': {
                'p_values': [],
                'corrected_p_values': [],
                'labels': [],
                'is_significant': [],
                'num_significant': 0
            },
            'summary': {
                'total_tests': 0,
                'total_significant': 0,
                'alpha': 0.05
            }
        }
    else:
        # Apply FDR to combined p-values
        combined_result = apply_fdr_to_results(all_p_values)
        combined_result['labels'] = all_labels

        # Apply FDR to subsets for detailed reporting
        decoder_result = apply_fdr_to_results(decoder_p_values)
        decoder_result['labels'] = decoder_labels

        rsa_result = apply_fdr_to_results(rsa_p_values)
        rsa_result['labels'] = rsa_labels

        result = {
            'decoder_results': decoder_result,
            'rsa_results': rsa_result,
            'combined_results': combined_result,
            'summary': {
                'total_tests': len(all_p_values),
                'total_significant': combined_result['num_significant'],
                'alpha': 0.05,
                'decoder_tests': len(decoder_p_values),
                'decoder_significant': decoder_result['num_significant'],
                'rsa_tests': len(rsa_p_values),
                'rsa_significant': rsa_result['num_significant']
            }
        }

    # Write results to output file
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path_obj, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"FDR correction results written to {output_path}")
    logger.info(f"Total tests: {result['summary']['total_tests']}, "
               f"Significant: {result['summary']['total_significant']}")

    return result

def main():
    """Main entry point for FDR correction pipeline."""
    # Define paths
    decoder_metrics_path = config.get_output_path('decoder_metrics.json')
    rsa_metrics_path = config.get_output_path('group_rsa_stats.json')
    output_path = config.get_output_path('fdr_corrected_results.json')

    # Run pipeline
    results = run_fdr_correction_pipeline(
        decoder_metrics_path,
        rsa_metrics_path,
        output_path
    )

    return results

if __name__ == '__main__':
    main()
