"""
Variance calculation and comparative measurement of correlation coefficients.

This module implements SC-003 by calculating the variance of correlation
coefficients across categories and comparing them against the overall dataset
correlation.
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from src.analysis.stratified_stats import compute_stratified_correlations, load_dependencies_data

logger = logging.getLogger(__name__)


def calculate_variance_and_comparisons(
    stratified_results: Dict[str, Dict[str, float]],
    overall_correlation: float
) -> Dict[str, Any]:
    """
    Calculate variance of correlation coefficients across categories and
    compare each category's coefficient against the overall dataset.
    
    Args:
        stratified_results: Dictionary mapping category names to correlation stats
        overall_correlation: The correlation coefficient for the full dataset
        
    Returns:
        Dictionary containing variance, comparisons, and summary statistics
    """
    if not stratified_results:
        return {
            "error": "No stratified results provided",
            "variance": None,
            "comparisons": []
        }
    
    # Extract correlation coefficients
    correlations = []
    category_data = []
    
    for category, stats in stratified_results.items():
        rho = stats.get("rho")
        if rho is not None:
            correlations.append(rho)
            category_data.append({
                "category": category,
                "rho": rho,
                "p_value": stats.get("p_value"),
                "n_samples": stats.get("n_samples")
            })
    
    if len(correlations) < 2:
        logger.warning("Insufficient categories for variance calculation (need >= 2)")
        return {
            "variance": None,
            "std_dev": None,
            "overall_correlation": overall_correlation,
            "comparisons": [],
            "note": "Variance requires at least 2 categories"
        }
    
    # Calculate variance and standard deviation
    correlations_array = np.array(correlations)
    variance = float(np.var(correlations_array, ddof=1))  # Sample variance
    std_dev = float(np.std(correlations_array, ddof=1))
    
    # Compare each category against overall
    comparisons = []
    for cat_data in category_data:
        rho = cat_data["rho"]
        diff = rho - overall_correlation
        # Calculate z-score if we have enough data
        z_score = None
        if std_dev > 0:
            z_score = diff / std_dev
        
        comparisons.append({
            "category": cat_data["category"],
            "category_rho": rho,
            "overall_rho": overall_correlation,
            "difference": diff,
            "z_score": z_score,
            "p_value": cat_data["p_value"],
            "n_samples": cat_data["n_samples"],
            "significantly_different": z_score is not None and abs(z_score) > 1.96
        })
    
    return {
        "variance": variance,
        "std_dev": std_dev,
        "mean_category_rho": float(np.mean(correlations_array)),
        "overall_correlation": overall_correlation,
        "n_categories": len(correlations),
        "comparisons": comparisons
    }


def run_variance_analysis(
    input_csv_path: str = "data/processed/dependencies_raw.csv",
    output_json_path: str = "data/processed/results_correlation.json"
) -> Dict[str, Any]:
    """
    Main function to run variance analysis and append results to correlation file.
    
    Args:
        input_csv_path: Path to the dependencies CSV file
        output_json_path: Path to the correlation results JSON file
        
    Returns:
        Complete analysis results dictionary
    """
    logger.info(f"Loading data from {input_csv_path}")
    df = load_dependencies_data(input_csv_path)
    
    if df is None or df.empty:
        logger.error("Failed to load data or data is empty")
        return {"error": "No data loaded"}
    
    # Run stratified analysis to get per-category correlations
    logger.info("Running stratified correlation analysis")
    stratified_results = compute_stratified_correlations(df)
    
    if not stratified_results:
        logger.error("Stratified analysis returned no results")
        return {"error": "No stratified results"}
    
    # Calculate overall correlation for comparison
    logger.info("Calculating overall correlation")
    valid_mask = df['age_in_days'].notna() & df['vulnerability_count'].notna()
    overall_rho, overall_p = np.nan, np.nan
    if valid_mask.sum() >= 2:
        from scipy.stats import spearmanr
        overall_rho, overall_p = spearmanr(
            df.loc[valid_mask, 'age_in_days'],
            df.loc[valid_mask, 'vulnerability_count']
        )
    
    # Calculate variance and comparisons
    logger.info("Calculating variance and comparisons")
    variance_results = calculate_variance_and_comparisons(
        stratified_results, 
        float(overall_rho) if not np.isnan(overall_rho) else 0.0
    )
    
    # Prepare final results structure
    final_results = {
        "overall_correlation": {
            "rho": float(overall_rho) if not np.isnan(overall_rho) else None,
            "p_value": float(overall_p) if not np.isnan(overall_p) else None,
            "n_samples": int(valid_mask.sum())
        },
        "stratified_correlations": stratified_results,
        "variance_analysis": variance_results
    }
    
    # Load existing results if file exists, then append/merge
    output_path = Path(output_json_path)
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                existing_data = json.load(f)
            # Merge variance analysis into existing results
            existing_data["variance_analysis"] = variance_results
            existing_data["overall_correlation"] = final_results["overall_correlation"]
            existing_data["stratified_correlations"] = stratified_results
            final_results = existing_data
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not merge with existing file: {e}, overwriting")
    
    # Write results to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    logger.info(f"Variance analysis results written to {output_path}")
    
    return final_results


def main():
    """Entry point for command-line execution."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="Calculate variance of correlation coefficients across categories"
    )
    parser.add_argument(
        "--input", 
        default="data/processed/dependencies_raw.csv",
        help="Path to input CSV file"
    )
    parser.add_argument(
        "--output",
        default="data/processed/results_correlation.json",
        help="Path to output JSON file"
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_variance_analysis(args.input, args.output)
        
        if "error" in results:
            print(f"Error: {results['error']}", file=sys.stderr)
            sys.exit(1)
        
        print("Variance analysis completed successfully")
        print(f"Variance: {results.get('variance_analysis', {}).get('variance', 'N/A')}")
        print(f"Categories analyzed: {results.get('variance_analysis', {}).get('n_categories', 0)}")
        
    except Exception as e:
        logger.exception("Unexpected error during variance analysis")
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
