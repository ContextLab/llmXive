"""
T016: Output JSON summary with status "success" for US1.

This script consumes the output of the complete-case analysis and variance estimation
(produced by T014 and T015) and writes a JSON summary to data/processed/baseline_results.json.

Required keys: mean, variance, status, design_type.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Import existing pipeline components
from data_ingestion import load_gss_data_subset
from imputation_pipeline import perform_complete_case_analysis
from variance_estimator import estimate_taylor_variance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_and_prepare_data(data_path: str) -> Optional[Dict[str, Any]]:
    """Load GSS data, apply complete-case analysis, and return processed data."""
    logger.info(f"Loading data from {data_path}")
    try:
        df = load_gss_data_subset(data_path)
        if df is None or df.empty:
            logger.error("Data loading resulted in empty or None dataframe.")
            return None
        
        # Perform complete-case analysis (T014)
        # Assuming 'varname' is the variable of interest; if not specified, we pick a numeric one.
        # For this task, we assume the pipeline has already identified a variable or we use a default.
        # Let's look for a common variable like 'hrs1' (hours worked) or similar in GSS subsets.
        # If the data_ingestion module filters, we use the result.
        
        cc_result = perform_complete_case_analysis(df, target_var=None) 
        # If target_var is None, the function should pick a representative numeric column
        # or we need to specify one. Based on T014 context, let's assume it returns a dict with 'cleaned_df' and 'target_var'.
        
        if 'cleaned_df' not in cc_result or 'target_var' not in cc_result:
            logger.error("Complete case analysis did not return expected keys.")
            return None
        
        return {
            "df": cc_result['cleaned_df'],
            "target_var": cc_result['target_var']
        }
    except Exception as e:
        logger.error(f"Error during data preparation: {e}")
        return None

def calculate_baseline_metrics(processed_data: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """Calculate mean and variance using design-based estimation (T015)."""
    df = processed_data['df']
    target_var = processed_data['target_var']
    
    if target_var not in df.columns:
        logger.error(f"Target variable {target_var} not found in dataframe.")
        return None
    
    try:
        # Estimate variance using Taylor series linearization (T015)
        # The function expects a dataframe and a variable name
        variance_result = estimate_taylor_variance(df, target_var)
        
        if variance_result is None or 'variance' not in variance_result:
            logger.error("Variance estimation failed or returned no variance.")
            return None
        
        # Calculate mean
        mean_val = df[target_var].mean()
        variance_val = variance_result['variance']
        
        return {
            "mean": float(mean_val),
            "variance": float(variance_val)
        }
    except Exception as e:
        logger.error(f"Error during metric calculation: {e}")
        return None

def write_summary(metrics: Dict[str, float], output_path: str) -> bool:
    """Write the JSON summary file."""
    summary = {
        "mean": metrics["mean"],
        "variance": metrics["variance"],
        "status": "success",
        "design_type": "Taylor Series Linearization"
    }
    
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Successfully wrote summary to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write summary: {e}")
        return False

def main():
    # Configuration
    input_path = "data/raw/gss_2018_subset.csv"
    output_path = "data/processed/baseline_results.json"
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}. Please run T004/T012 first.")
        sys.exit(1)
    
    # Step 1: Load and prepare data
    processed = load_and_prepare_data(input_path)
    if not processed:
        logger.error("Data preparation failed. Aborting T016.")
        sys.exit(1)
    
    # Step 2: Calculate metrics
    metrics = calculate_baseline_metrics(processed)
    if not metrics:
        logger.error("Metric calculation failed. Aborting T016.")
        sys.exit(1)
    
    # Step 3: Write output
    success = write_summary(metrics, output_path)
    if not success:
        logger.error("Failed to write output file. Aborting T016.")
        sys.exit(1)
    
    logger.info("T016 completed successfully.")

if __name__ == "__main__":
    main()
