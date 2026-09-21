"""
Variance calculation and comparative measurement of correlation coefficients across categories.
Implements T029a: Calculates variance of correlation coefficients across categories and overall.
Outputs to data/processed/results_correlation.json (appending category_variances and overall_variance).
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from src.analysis.stratified_stats import compute_stratified_correlations, load_dependencies_data

logger = logging.getLogger(__name__)

def calculate_variance_and_comparisons(
    correlations: Dict[str, float],
    categories: List[str]
) -> Dict[str, Any]:
    """
    Calculate variance of correlation coefficients across categories and overall.

    Args:
        correlations: Dictionary mapping category names to their correlation coefficients.
        categories: List of category names (for context, though correlations keys are used).

    Returns:
        Dictionary with 'category_variances' and 'overall_variance'.
    """
    if not correlations:
        logger.warning("No correlations provided for variance calculation.")
        return {
            'category_variances': {},
            'overall_variance': 0.0,
            'message': 'No data to calculate variance.'
        }

    values = list(correlations.values())
    if len(values) < 2:
        # Variance requires at least 2 samples.
        # If only one category, variance is 0 or undefined. We return 0.
        logger.warning(f"Only one category ({len(values)}) found. Variance is 0.")
        return {
            'category_variances': {cat: 0.0 for cat in correlations.keys()},
            'overall_variance': 0.0,
            'message': 'Insufficient categories for variance calculation.'
        }

    # Calculate overall variance (population variance or sample variance?
    # Usually for a set of measurements, sample variance (ddof=1) is appropriate,
    # but if these are the only categories we care about, population (ddof=0) might be intended.
    # Given the context of "comparative measurement", sample variance is safer for inference.
    # However, standard numpy var defaults to population. Let's use sample variance (ddof=1).
    overall_var = np.var(values, ddof=1)

    # For category_variances, we don't have multiple measurements per category in this specific task description.
    # The task asks for "variance calculation ... across categories".
    # If the input 'correlations' is just one value per category, we can't calculate variance *within* a category
    # without the raw data split by category.
    # Re-reading T029a: "Implement variance calculation and comparative measurement of correlation coefficients across categories."
    # And output schema: {'category_variances': {<cat>: float}, 'overall_variance': float}
    # This implies we might need to calculate the variance *of the coefficients* (which is the overall variance),
    # or perhaps the task implies we have multiple coefficients per category?
    # Looking at T029: "compute per-category coefficients". T029a adds "variance ... across categories".
    # If T029 produces ONE coefficient per category, then "variance across categories" IS the variance of the list of coefficients.
    # The schema key 'category_variances' is plural per category. This is ambiguous.
    # Interpretation:
    # 1. If we have multiple correlation estimates per category (e.g. bootstrapped), we calculate variance per category.
    # 2. If we have one per category, 'category_variances' might be a misnomer or intended to store the contribution of each to the overall?
    # 3. Or, perhaps 'category_variances' is meant to be the variance of the *values* within each category (e.g. age vs vuln variance within category)?
    # But the schema says "correlation coefficients across categories".
    # Let's assume the standard interpretation for "variance of correlation coefficients across categories":
    # We have a set of coefficients (one per category). We calculate the variance of this set.
    # What about 'category_variances': {<cat>: float}?
    # Maybe it's the squared deviation of each category's coefficient from the mean? (Contribution to total sum of squares).
    # Or maybe it's a placeholder for future multi-measure support.
    # Given the strict schema requirement in T029a: `{'category_variances': {<cat>: float}, 'overall_variance': float}`
    # I will interpret 'category_variances' as the squared deviation of each category's correlation from the mean correlation.
    # This sums to (N-1)*variance (for sample) or N*variance (for population).
    # Let's calculate the mean and then the squared deviation for each.

    mean_corr = np.mean(values)
    category_variances = {}
    for cat, corr in correlations.items():
        squared_deviation = (corr - mean_corr) ** 2
        category_variances[cat] = float(squared_deviation)

    return {
        'category_variances': category_variances,
        'overall_variance': float(overall_var),
        'mean_correlation': float(mean_corr),
        'num_categories': len(correlations)
    }

def run_variance_analysis(
    input_csv_path: str,
    output_json_path: str,
    existing_correlations: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Run the variance analysis pipeline.
    If existing_correlations are not provided, it computes them via stratified analysis.
    Then calculates variances and appends to the output file.

    Args:
        input_csv_path: Path to the dependencies CSV file.
        output_json_path: Path to the results_correlation.json file to append to.
        existing_correlations: Optional pre-computed correlations. If None, computes from input.

    Returns:
        The variance analysis result dictionary.
    """
    logger.info(f"Running variance analysis on {input_csv_path}")

    if existing_correlations is None:
        logger.info("No existing correlations provided. Computing stratified correlations...")
        # Load data and compute stratified correlations
        df = load_dependencies_data(input_csv_path)
        if df is None or df.empty:
            logger.error("Failed to load data or data is empty.")
            return {'error': 'Data loading failed'}

        stratified_results = compute_stratified_correlations(df)
        if not stratified_results:
            logger.warning("Stratified analysis returned no correlations.")
            # If no categories met the N>=30 threshold, we can't calculate variance across them.
            return {
                'category_variances': {},
                'overall_variance': 0.0,
                'message': 'No categories with sufficient data (N>=30) for stratified analysis.'
            }
        correlations = {res['category']: res['correlation'] for res in stratified_results}
    else:
        correlations = existing_correlations

    logger.info(f"Calculated {len(correlations)} correlations: {correlations}")

    variance_result = calculate_variance_and_comparisons(correlations, list(correlations.keys()))

    # Append to existing file or create new
    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    existing_data = {}
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                existing_data = json.load(f)
            logger.info(f"Loaded existing data from {output_json_path}")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing file {output_json_path}: {e}. Starting fresh.")
            existing_data = {}

    # Update the existing data with new keys
    existing_data['category_variances'] = variance_result['category_variances']
    existing_data['overall_variance'] = variance_result['overall_variance']
    
    # Optionally preserve other keys if they exist (like individual correlations if stored separately)
    # But T029a specifically asks to append these keys to results_correlation.json.
    
    with open(output_path, 'w') as f:
        json.dump(existing_data, f, indent=2)

    logger.info(f"Variance analysis complete. Results written to {output_json_path}")
    return variance_result

def main():
    """Entry point for variance analysis."""
    import argparse
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description='Calculate variance of correlation coefficients across categories.')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV (dependencies_raw.csv).')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON (results_correlation.json).')
    args = parser.parse_args()

    result = run_variance_analysis(args.input, args.output)
    
    if 'error' in result:
        logger.error(f"Variance analysis failed: {result['error']}")
        return 1
    
    logger.info(f"Analysis successful. Overall Variance: {result.get('overall_variance', 'N/A')}")
    return 0

if __name__ == '__main__':
    exit(main())