import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

# Import existing modules from the project API surface
from data_ingestion import load_gss_data_subset
from variance_estimator import estimate_taylor_variance

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_prepare_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the GSS dataset.
    If input_path is not provided, attempts to load the standard artifact.
    """
    if input_path is None:
        input_path = "data/raw/gss_2018_subset.csv"
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input data file not found at {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure design columns exist for variance estimation
    required_cols = ['weight', 'psu', 'strata']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required design columns: {missing_cols}")
    
    return df

def calculate_baseline_metrics(df: pd.DataFrame, variable_name: str = 'realinc') -> Dict[str, Any]:
    """
    Calculate mean and variance for a specific variable using design-based estimation.
    Returns a dictionary with mean, variance, status, and design_type.
    """
    if variable_name not in df.columns:
        logger.warning(f"Variable {variable_name} not found. Using first numeric column.")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            raise ValueError("No numeric columns found in dataset.")
        variable_name = numeric_cols[0]
        logger.info(f"Selected variable: {variable_name}")

    # Filter out missing values for the variable of interest
    valid_df = df.dropna(subset=[variable_name])
    
    if valid_df.empty:
        logger.error(f"No valid data for variable {variable_name}")
        return {
            "mean": None,
            "variance": None,
            "status": "failed",
            "design_type": "taylor_series",
            "variable": variable_name,
            "reason": "No valid data"
        }

    try:
        # Use the design-based variance estimator
        # This function expects the dataframe and the variable name
        # It returns a dict with 'mean', 'variance', etc.
        result = estimate_taylor_variance(valid_df, variable_name)
        
        if result.get('status') != 'success':
            return {
                "mean": None,
                "variance": None,
                "status": "failed",
                "design_type": "taylor_series",
                "variable": variable_name,
                "reason": result.get('reason', 'Unknown error in variance estimation')
            }

        return {
            "mean": float(result['mean']),
            "variance": float(result['variance']),
            "status": "success",
            "design_type": "taylor_series",
            "variable": variable_name,
            "n_obs": int(len(valid_df))
        }
        
    except Exception as e:
        logger.error(f"Error calculating variance: {e}", exc_info=True)
        return {
            "mean": None,
            "variance": None,
            "status": "failed",
            "design_type": "taylor_series",
            "variable": variable_name,
            "reason": str(e)
        }

def write_summary(results: Dict[str, Any], output_path: str) -> None:
    """
    Write the baseline results to a JSON file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Baseline results written to {output_path}")

def main():
    """
    Main entry point to generate baseline_results.json.
    """
    # Default paths
    input_data_path = "data/raw/gss_2018_subset.csv"
    output_json_path = "data/processed/baseline_results.json"
    target_variable = "realinc"

    # Parse arguments if provided
    if len(sys.argv) > 1:
        input_data_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_json_path = sys.argv[2]
    if len(sys.argv) > 3:
        target_variable = sys.argv[3]

    try:
        # Load data
        df = load_and_prepare_data(input_data_path)
        
        # Calculate metrics
        metrics = calculate_baseline_metrics(df, target_variable)
        
        # Write output
        write_summary(metrics, output_json_path)
        
        # Exit with appropriate code
        if metrics['status'] == 'success':
            logger.info("Baseline calculation completed successfully.")
            sys.exit(0)
        else:
            logger.warning(f"Baseline calculation failed: {metrics.get('reason')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        # Write a failure status to the output file so the pipeline can continue gracefully
        failure_result = {
            "mean": None,
            "variance": None,
            "status": "failed",
            "design_type": "taylor_series",
            "variable": target_variable,
            "reason": str(e)
        }
        try:
            write_summary(failure_result, output_json_path)
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()