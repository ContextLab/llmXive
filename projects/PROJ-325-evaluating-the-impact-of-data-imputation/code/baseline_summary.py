"""
Baseline Summary Script.

Orchestrates the calculation of baseline metrics (Complete-Case Analysis)
and writes the results to `data/processed/baseline_results.json`.

This script depends on:
- code/data_ingestion.py (for loading and cleaning)
- code/variance_estimator.py (for variance calculation)
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Import from sibling modules as per API surface
from data_ingestion import load_gss_data_subset, ensure_design_columns, detect_missingness
from variance_estimator import estimate_taylor_variance

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_and_prepare_data(input_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Loads the GSS dataset, ensures design columns exist, and filters variables.
    Returns the prepared DataFrame or None if loading fails.
    """
    try:
        # Default path if not specified
        if input_path is None:
            input_path = "data/raw/gss_2018_subset.csv"
        
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}. Please run data fetcher first.")
            return None

        logger.info(f"Loading data from {input_path}...")
        df = load_gss_data_subset(input_path)
        
        if df is None or df.empty:
            logger.error("Data loading resulted in an empty or None DataFrame.")
            return None

        # Ensure design columns exist (will abort if missing per T009)
        df = ensure_design_columns(df)
        
        # Detect missingness and filter variables (>30% missing)
        # This function returns a list of columns to skip
        skip_cols = detect_missingness(df, threshold=0.3)
        if skip_cols:
            logger.warning(f"Skipping variables with >30% missingness: {skip_cols}")
            df = df.drop(columns=skip_cols, errors='ignore')

        return df
    except Exception as e:
        logger.error(f"Failed to load or prepare data: {e}", exc_info=True)
        return None

def calculate_baseline_metrics(df: Any, variable_name: str = "realinc") -> Dict[str, Any]:
    """
    Calculates mean and design-based variance for a specific variable.
    Returns a dictionary with mean, variance, status, and design_type.
    """
    if df is None:
        return {
            "mean": None,
            "variance": None,
            "status": "failed",
            "design_type": "none",
            "error": "Data not loaded"
        }

    if variable_name not in df.columns:
        logger.warning(f"Variable '{variable_name}' not found in dataset. Available: {list(df.columns)[:10]}...")
        return {
            "mean": None,
            "variance": None,
            "status": "failed",
            "design_type": "none",
            "error": f"Variable '{variable_name}' not found"
        }

    try:
        # Filter to complete cases for the target variable
        # (Complete-Case Analysis)
        clean_df = df.dropna(subset=[variable_name])
        
        if clean_df.empty:
            logger.warning(f"No complete cases found for {variable_name}.")
            return {
                "mean": None,
                "variance": None,
                "status": "failed",
                "design_type": "taylor",
                "error": "No complete cases"
            }

        # Calculate Mean
        mean_val = clean_df[variable_name].mean()
        
        # Calculate Variance using Taylor Series Linearization
        # This function handles PSU/Strata checks internally (T009/T009b)
        variance_result = estimate_taylor_variance(
            clean_df, 
            variable_name, 
            weight_col="weight", 
            psu_col="psu", 
            strata_col="strata"
        )

        if variance_result.get("status") == "failed":
            return {
                "mean": float(mean_val),
                "variance": None,
                "status": "failed",
                "design_type": "taylor",
                "error": variance_result.get("error", "Variance estimation failed")
            }

        return {
            "mean": float(mean_val),
            "variance": float(variance_result["variance"]),
            "status": "success",
            "design_type": "taylor",
            "variable": variable_name,
            "n_obs": int(len(clean_df))
        }

    except Exception as e:
        logger.error(f"Error calculating baseline metrics: {e}", exc_info=True)
        return {
            "mean": None,
            "variance": None,
            "status": "failed",
            "design_type": "taylor",
            "error": str(e)
        }

def write_summary(results: Dict[str, Any], output_path: str = "data/processed/baseline_results.json"):
    """
    Writes the results dictionary to a JSON file.
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Baseline results written to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write summary to {output_path}: {e}", exc_info=True)
        return False

def main():
    """
    Main entry point for the baseline summary script.
    """
    # 1. Load and prepare data
    df = load_and_prepare_data()
    
    if df is None:
        # If data loading fails, write a failed status immediately
        # to satisfy T020 requirement of writing a JSON with status
        failed_results = {
            "mean": None,
            "variance": None,
            "status": "failed",
            "design_type": "none",
            "error": "Data loading failed"
        }
        write_summary(failed_results)
        return 1

    # 2. Calculate metrics (defaulting to 'realinc' if available, else first numeric)
    target_var = "realinc"
    if target_var not in df.columns:
        # Fallback to first numeric column that isn't a design column
        design_cols = {"weight", "psu", "strata", "year"}
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        available = [c for c in numeric_cols if c not in design_cols]
        if available:
            target_var = available[0]
            logger.info(f"Target variable not found, using '{target_var}' instead.")
        else:
            logger.error("No suitable numeric variable found for analysis.")
            failed_results = {
                "mean": None,
                "variance": None,
                "status": "failed",
                "design_type": "none",
                "error": "No suitable variable found"
            }
            write_summary(failed_results)
            return 1

    # 3. Calculate baseline metrics
    results = calculate_baseline_metrics(df, target_var)

    # 4. Write results
    success = write_summary(results)
    
    if not success:
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())