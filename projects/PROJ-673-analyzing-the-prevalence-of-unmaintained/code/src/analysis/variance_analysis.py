import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from src.analysis.stratified_stats import compute_stratified_correlations, load_dependencies_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_variance_and_comparisons(correlations: Dict[str, float], overall_correlation: float) -> Dict[str, Any]:
    """
    Calculate the variance of correlation coefficients across categories
    and compare it against the overall dataset correlation.
    
    Args:
        correlations: Dictionary mapping category names to their Spearman rho values.
        overall_correlation: The Spearman rho calculated over the entire dataset.
        
    Returns:
        Dictionary containing:
            - category_variances: Dict of category -> correlation
            - overall_variance: Variance of the category correlations
            - overall_correlation: The overall dataset correlation (for reference)
            - variance_ratio: Ratio of overall_variance to |overall_correlation|
            - analysis_summary: A string summary of the findings
    """
    if not correlations:
        logger.warning("No category correlations provided. Returning empty variance metrics.")
        return {
            "category_variances": {},
            "overall_variance": 0.0,
            "overall_correlation": overall_correlation,
            "variance_ratio": 0.0,
            "analysis_summary": "No categories found to calculate variance."
        }

    values = list(correlations.values())
    
    # Calculate variance of the correlations
    # Using population variance (ddof=0) as we are describing the variance of the observed groups
    variance = np.var(values, ddof=0)
    
    # Calculate a ratio to understand the magnitude of variance relative to the overall effect
    # Avoid division by zero if overall correlation is 0
    if abs(overall_correlation) < 1e-9:
        variance_ratio = float('inf') if variance > 0 else 0.0
    else:
        variance_ratio = variance / abs(overall_correlation)

    analysis_summary = (
        f"Calculated variance of {variance:.6f} across {len(correlations)} categories. "
        f"Overall dataset correlation was {overall_correlation:.6f}. "
        f"Variance ratio (variance/|rho|): {variance_ratio:.6f}."
    )

    logger.info(analysis_summary)

    return {
        "category_variances": correlations,
        "overall_variance": float(variance),
        "overall_correlation": float(overall_correlation),
        "variance_ratio": float(variance_ratio),
        "analysis_summary": analysis_summary
    }

def run_variance_analysis(input_path: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Orchestrates the variance calculation:
    1. Loads stratified correlations from the previous step (T035).
    2. Loads the overall correlation from the core analysis (T027).
    3. Calculates the variance metrics.
    4. Appends the results to the main correlation results file.
    
    Args:
        input_path: Path to the stratified results file (results_stratified.json). 
                    Defaults to data/processed/results_stratified.json.
        output_path: Path to the main correlation results file to update 
                    (results_correlation.json). Defaults to data/processed/results_correlation.json.
                    
    Returns:
        The full updated results dictionary.
    """
    # Default paths based on project structure
    base_dir = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
    stratified_path = Path(input_path) if input_path else (base_dir / "results_stratified.json")
    correlation_path = Path(output_path) if output_path else (base_dir / "results_correlation.json")

    logger.info(f"Loading stratified correlations from {stratified_path}")
    if not stratified_path.exists():
        raise FileNotFoundError(f"Stratified results file not found at {stratified_path}. "
                                "Please ensure T035 has been executed successfully.")
    
    with open(stratified_path, 'r') as f:
        stratified_data = json.load(f)

    # Extract category correlations from stratified data
    # The stratified data structure typically contains a 'results' key with category stats
    category_correlations = {}
    if 'results' in stratified_data:
        for category, stats in stratified_data['results'].items():
            if 'correlation_coefficient' in stats:
                category_correlations[category] = stats['correlation_coefficient']
            elif 'rho' in stats:
                category_correlations[category] = stats['rho']
    
    logger.info(f"Found correlations for categories: {list(category_correlations.keys())}")

    # Load overall correlation
    logger.info(f"Loading overall correlation from {correlation_path}")
    if not correlation_path.exists():
        # If the main file doesn't exist yet, we might need to calculate the overall correlation
        # from the raw data if stratified_stats didn't save it, or raise an error if it's a strict dependency.
        # Per T036 description, it depends on T035, but T027 (correlation.py) produces this file.
        # If T027 hasn't run, we try to compute it from raw data as a fallback to ensure the script runs.
        raw_data_path = base_dir / "dependencies_raw.csv"
        if raw_data_path.exists():
            logger.warning(f"{correlation_path} not found. Computing overall correlation from raw data.")
            raw_df = load_dependencies_data(str(raw_data_path))
            # Filter out nulls for correlation
            valid_df = raw_df[raw_df['age_in_days'].notna() & raw_df['vulnerability_count'].notna()]
            if len(valid_df) > 1:
                rho, p_val = np.corrcoef(valid_df['age_in_days'], valid_df['vulnerability_count'])
                overall_rho = rho
            else:
                raise ValueError("Not enough valid data points to calculate overall correlation.")
        else:
            raise FileNotFoundError(f"Main correlation file {correlation_path} not found, "
                                    "and raw data {raw_data_path} not found to compute it.")
    else:
        with open(correlation_path, 'r') as f:
            correlation_data = json.load(f)
        overall_rho = correlation_data.get('correlation_coefficient')
        if overall_rho is None:
            # Fallback if key is named differently
            overall_rho = correlation_data.get('rho')
            if overall_rho is None:
                raise ValueError("Could not find 'correlation_coefficient' or 'rho' in results_correlation.json")

    logger.info(f"Overall correlation coefficient: {overall_rho}")

    # Calculate variance
    variance_results = calculate_variance_and_comparisons(category_correlations, overall_rho)

    # Append to correlation data
    correlation_data['category_variances'] = variance_results['category_variances']
    correlation_data['overall_variance'] = variance_results['overall_variance']
    correlation_data['variance_ratio'] = variance_results['variance_ratio']
    correlation_data['variance_analysis_summary'] = variance_results['analysis_summary']

    # Write back to file
    logger.info(f"Writing updated results to {correlation_path}")
    with open(correlation_path, 'w') as f:
        json.dump(correlation_data, f, indent=2)

    logger.info("Variance calculation complete.")
    return correlation_data

def main():
    """
    Entry point for the variance analysis script.
    Usage: python src/analysis/variance_analysis.py [--input <path>] [--output <path>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate variance in correlation coefficients across categories.")
    parser.add_argument("--input", type=str, help="Path to stratified results JSON (results_stratified.json)")
    parser.add_argument("--output", type=str, help="Path to update correlation results JSON (results_correlation.json)")
    
    args = parser.parse_args()
    
    try:
        result = run_variance_analysis(
            input_path=args.input,
            output_path=args.output
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Variance analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
