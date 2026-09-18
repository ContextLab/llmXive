import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from utils import get_logger, read_json, write_json
from config import ensure_directories

def load_existing_results(null_distribution_path: str) -> Dict[str, Any]:
    """
    Load the null distribution stats and observed stats from the JSON file.
    """
    if not os.path.exists(null_distribution_path):
        raise FileNotFoundError(f"Null distribution file not found: {null_distribution_path}")
    
    logger = get_logger(__name__)
    logger.info(f"Loading null distribution results from {null_distribution_path}")
    
    data = read_json(null_distribution_path)
    return data

def compute_null_distribution_stats(null_maes: np.ndarray) -> Dict[str, float]:
    """
    Compute summary statistics for the null distribution of MAEs.
    """
    return {
        "mean_mae": float(np.mean(null_maes)),
        "std_mae": float(np.std(null_maes)),
        "min_mae": float(np.min(null_maes)),
        "max_mae": float(np.max(null_maes)),
        "count": int(len(null_maes))
    }

def calculate_empirical_p_value(observed_mae: float, null_maes: np.ndarray) -> float:
    """
    Calculate the empirical p-value based on the observed MAE and the null distribution.
    
    Formula: p = (count(Null MAE <= Observed MAE) + 1) / (N + 1)
    
    This implements the standard convention for empirical p-values to avoid zero p-values.
    """
    if len(null_maes) == 0:
        raise ValueError("Null distribution is empty; cannot calculate p-value.")
    
    # Count how many null MAEs are less than or equal to the observed MAE
    count_leq = np.sum(null_maes <= observed_mae)
    n = len(null_maes)
    
    # Calculate p-value using the standard formula
    p_value = (count_leq + 1) / (n + 1)
    
    logger = get_logger(__name__)
    logger.info(f"Calculated empirical p-value: {p_value:.6f} (count_leq={count_leq}, n={n})")
    
    return float(p_value)

def generate_model_report(
    observed_stats: Dict[str, float],
    null_stats: Dict[str, Any],
    p_value: float,
    output_path: str
) -> Dict[str, Any]:
    """
    Generate the final model report JSON containing observed stats, null stats, and p-value.
    """
    report = {
        "observed_stats": observed_stats,
        "null_distribution_stats": null_stats,
        "empirical_p_value": p_value,
        "formula": "p = (count(Null MAE <= Observed MAE) + 1) / (N + 1)",
        "interpretation": "Significant" if p_value < 0.05 else "Not Significant"
    }
    
    logger = get_logger(__name__)
    logger.info(f"Writing model report to {output_path}")
    write_json(output_path, report)
    
    return report

def main():
    """
    Main entry point for T022: Empirical p-value calculation.
    
    Reads data/results/null_distribution.json, calculates the empirical p-value
    using the observed MAE and the null distribution, and updates the file.
    """
    logger = get_logger(__name__)
    ensure_directories()
    
    # Define paths
    null_dist_path = "data/results/null_distribution.json"
    
    # Load existing results
    try:
        data = load_existing_results(null_dist_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    
    # Extract observed MAE and null MAEs (if available in full form)
    observed_mae = data["observed_stats"]["mae"]
    
    # The null_distribution.json file structure might not have the full array.
    # However, T021 is supposed to have written the null distribution stats.
    # If the full array is not present, we cannot calculate p-value from this file alone.
    # We assume that if the task T021 was implemented correctly, it might have stored
    # the array or we need to re-run the permutation if not.
    # Given the task description: "read data/results/null_distribution.json and the observed MAE... then calculate"
    # It implies the necessary data is in the file.
    
    # Check if the full null distribution array is available.
    # If not, we might need to assume T021 stored it or we have to re-generate it.
    # However, the schema provided in the prompt shows only stats.
    # Let's assume for T022 we need to re-run the null generation if the array is missing,
    # OR the prompt implies we have the array.
    # Since the prompt says "read ... and the observed MAE ... then calculate", 
    # and the provided file content only has stats, there is a mismatch.
    # BUT, T021 description says: "writing the resulting MAE and R² values to data/results/null_distribution.json".
    # It does not explicitly say it writes the full array.
    # However, to calculate p-value, we need the distribution (the array of 1000 MAEs).
    # If the file only has stats, we cannot calculate p-value without re-running.
    # Let's check if the file has a 'null_maes' key. If not, we must re-run the null pipeline.
    
    null_maes = data.get("null_maes", None)
    
    if null_maes is None:
        logger.warning("Full null distribution (array) not found in null_distribution.json. Re-running null distribution pipeline.")
        # Import the modeling function to re-run the null distribution
        from modeling import run_null_distribution_pipeline, load_cleaned_data, prepare_model_data, run_ridge_regression_with_nested_cv
        
        # We need to re-run the null distribution to get the array
        # This assumes the cleaned data exists
        cleaned_data_path = "data/processed/cleaned_data.csv"
        if not os.path.exists(cleaned_data_path):
            logger.error(f"Cleaned data not found at {cleaned_data_path}. Cannot run null distribution.")
            return 1
        
        df = load_cleaned_data(cleaned_data_path)
        y, X = prepare_model_data(df)
        
        # Run null distribution (N=1000 as per T021)
        null_results = run_null_distribution_pipeline(y, X, n_permutations=1000)
        null_maes = null_results["maes"]
        
        # Update observed stats if needed (re-run primary model)
        # The observed stats in the file might be stale if we re-run.
        # But T021 says it writes observed stats too.
        # Let's re-run the primary model to get the current observed MAE
        observed_result = run_ridge_regression_with_nested_cv(y, X)
        observed_mae = observed_result["mae"]
        
        data["observed_stats"]["mae"] = observed_mae
        data["null_maes"] = null_maes.tolist()
    
    else:
        # Convert list back to numpy array if it was serialized
        null_maes = np.array(null_maes)
    
    # Calculate empirical p-value
    p_value = calculate_empirical_p_value(observed_mae, null_maes)
    
    # Update the data dictionary
    data["empirical_p_value"] = p_value
    
    # Recompute stats for consistency (optional, but good practice)
    null_stats = compute_null_distribution_stats(null_maes)
    data["null_distribution_stats"].update(null_stats)
    
    # Write the updated report
    generate_model_report(
        observed_stats=data["observed_stats"],
        null_stats=data["null_distribution_stats"],
        p_value=p_value,
        output_path=null_dist_path
    )
    
    logger.info("T022 completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
