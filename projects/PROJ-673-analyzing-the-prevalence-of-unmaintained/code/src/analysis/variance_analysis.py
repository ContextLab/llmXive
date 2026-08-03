import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from src.analysis.stratified_stats import compute_stratified_correlations, load_dependencies_data

logger = logging.getLogger(__name__)


def calculate_variance_and_comparisons(stratified_results: Dict[str, Any], overall_correlation: float) -> Dict[str, Any]:
    """
    Calculate variance of correlation coefficients across categories and compare
    each category's coefficient against the overall dataset correlation.

    Args:
        stratified_results: Dictionary containing per-category correlation results
                            from compute_stratified_correlations
        overall_correlation: The Spearman correlation coefficient for the full dataset

    Returns:
        Dictionary containing variance metrics and comparative measurements
    """
    category_correlations = []
    category_names = []
    category_samples = []

    # Extract valid correlations (those with sufficient sample size)
    for category, stats in stratified_results.get('stratified_correlations', {}).items():
        if stats.get('n_samples', 0) >= 30 and stats.get('rho') is not None:
            category_correlations.append(stats['rho'])
            category_names.append(category)
            category_samples.append(stats['n_samples'])

    if len(category_correlations) < 2:
        logger.warning("Insufficient categories with N >= 30 to calculate variance")
        return {
            'variance': None,
            'std_deviation': None,
            'comparisons': [],
            'num_categories_analyzed': 0
        }

    # Calculate variance and standard deviation
    variance = float(np.var(category_correlations, ddof=1))
    std_deviation = float(np.std(category_correlations, ddof=1))

    # Compare each category against overall correlation
    comparisons = []
    for i, category in enumerate(category_names):
        rho = category_correlations[i]
        n = category_samples[i]

        difference = rho - overall_correlation
        # Z-score approximation: (rho - overall) / std_dev_of_correlations
        # This gives a sense of how many standard deviations away from the mean
        z_score = difference / std_deviation if std_deviation > 0 else 0.0

        comparisons.append({
            'category': category,
            'category_rho': rho,
            'overall_rho': overall_correlation,
            'difference': float(difference),
            'z_score': float(z_score),
            'n_samples': n,
            'is_significantly_different': abs(z_score) > 1.96  # Approx 95% confidence
        })

    return {
        'variance': variance,
        'std_deviation': std_deviation,
        'mean_category_rho': float(np.mean(category_correlations)),
        'comparisons': comparisons,
        'num_categories_analyzed': len(category_correlations)
    }


def run_variance_analysis(
    input_csv_path: str,
    stratified_results_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Main entry point to run variance analysis on stratified correlation results.

    This function:
    1. Loads the dependencies data to calculate overall correlation
    2. Loads existing stratified results from T029
    3. Calculates variance and comparative measurements
    4. Appends results to the correlation results file

    Args:
        input_csv_path: Path to dependencies_raw.csv
        stratified_results_path: Path to results_correlation.json (from T024/T029)
        output_path: Path to append results to (same as stratified_results_path)

    Returns:
        Dictionary containing the variance analysis results
    """
    logger.info(f"Loading dependencies data from {input_csv_path}")
    df = load_dependencies_data(input_csv_path)

    # Calculate overall correlation if not already in stratified results
    # Filter for valid pairs
    valid_df = df.dropna(subset=['age_in_days', 'vulnerability_count'])
    if len(valid_df) < 2:
        raise ValueError("Insufficient data points to calculate overall correlation")

    from scipy.stats import spearmanr
    overall_rho, overall_p = spearmanr(valid_df['age_in_days'], valid_df['vulnerability_count'])
    logger.info(f"Overall correlation (rho={overall_rho:.4f}, p={overall_p:.4f})")

    # Load existing stratified results
    logger.info(f"Loading stratified results from {stratified_results_path}")
    with open(stratified_results_path, 'r') as f:
        existing_results = json.load(f)

    # Extract stratified correlations from the loaded results
    stratified_correlations = existing_results.get('stratified_correlations', {})

    # Calculate variance and comparisons
    variance_results = calculate_variance_and_comparisons(
        {'stratified_correlations': stratified_correlations},
        float(overall_rho)
    )

    # Add overall correlation context
    variance_results['overall_correlation'] = {
        'rho': float(overall_rho),
        'p_value': float(overall_p),
        'n_samples': len(valid_df)
    }

    # Append to existing results
    existing_results['variance_analysis'] = variance_results
    existing_results['analysis_complete'] = True

    # Write back to file
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(existing_results, f, indent=2)

    logger.info(f"Variance analysis results appended to {output_path}")

    return variance_results


def main():
    """CLI entry point for variance analysis."""
    import argparse
    import logging

    parser = argparse.ArgumentParser(description='Run variance analysis on stratified correlations')
    parser.add_argument('--input', type=str, default='data/processed/dependencies_raw.csv',
                      help='Path to dependencies CSV file')
    parser.add_argument('--results', type=str, default='data/processed/results_correlation.json',
                      help='Path to existing correlation results JSON')
    parser.add_argument('--output', type=str, default='data/processed/results_correlation.json',
                      help='Path to output results JSON (same as results by default)')
    parser.add_argument('--log-level', type=str, default='INFO',
                      help='Logging level')

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        results = run_variance_analysis(
            args.input,
            args.results,
            args.output
        )
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Variance analysis failed: {e}", exc_info=True)
        raise