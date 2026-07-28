"""
Baseline Summary Module for User Story 1.

Orchestrates the calculation of complete-case baseline metrics and outputs
the JSON summary artifact required by T016.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Import from sibling modules as per API surface
from data_ingestion import load_gss_data_subset, detect_missingness
from imputation_pipeline import perform_complete_case_analysis
from variance_estimator import estimate_taylor_variance
from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_and_prepare_data(input_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the GSS subset and prepare it for analysis.
    
    Args:
        input_path: Optional path to the raw data file. Defaults to config.
        
    Returns:
        Dictionary containing the dataframe and metadata.
    """
    config = get_config()
    if input_path is None:
        input_path = config.get('data', {}).get('raw_gss_path', 'data/raw/gss_2018_subset.csv')
    
    logger.info(f"Loading data from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Required data file not found: {input_path}. "
                              "Please run T004/T004b to fetch data first.")
    
    df = load_gss_data_subset(input_path)
    
    # Detect missingness and log warnings for high-missing variables
    missingness_info = detect_missingness(df)
    if missingness_info:
        logger.warning(f"Detected missingness in variables: {list(missingness_info.keys())}")
        
    return {
        'df': df,
        'missingness': missingness_info,
        'source': input_path
    }

def calculate_baseline_metrics(data_context: Dict[str, Any], target_var: str = 'hours') -> Dict[str, Any]:
    """
    Calculate baseline mean and variance using complete-case analysis.
    
    Args:
        data_context: Dictionary from load_and_prepare_data containing 'df'.
        target_var: The variable to analyze (default: 'hours').
        
    Returns:
        Dictionary with mean, variance, and design info.
    """
    df = data_context['df']
    
    if target_var not in df.columns:
        raise ValueError(f"Target variable '{target_var}' not found in data. "
                       f"Available columns: {list(df.columns)}")
    
    logger.info(f"Performing complete-case analysis for variable: {target_var}")
    
    # Perform complete-case analysis (drop rows with missing target)
    clean_df, dropped_count = perform_complete_case_analysis(df, target_var)
    logger.info(f"Dropped {dropped_count} rows due to missingness. "
               f"Remaining rows: {len(clean_df)}")
    
    if len(clean_df) == 0:
        raise ValueError("Complete-case analysis resulted in an empty dataset.")
    
    # Estimate design-based variance
    logger.info("Estimating design-based variance (Taylor Series)")
    
    try:
        variance_result = estimate_taylor_variance(
            clean_df, 
            target_var, 
            weight_col='wtssall', 
            psu_col='psu', 
            strata_col='strata'
        )
        
        mean_val = float(clean_df[target_var].mean())
        variance_val = float(variance_result['variance_estimate'])
        design_type = variance_result.get('design_type', 'Taylor Series Linearization')
        
        logger.info(f"Baseline Mean: {mean_val:.4f}")
        logger.info(f"Baseline Variance: {variance_val:.4f}")
        
        return {
            'mean': mean_val,
            'variance': variance_val,
            'design_type': design_type,
            'n_observations': len(clean_df),
            'n_dropped': dropped_count
        }
        
    except Exception as e:
        logger.error(f"Variance estimation failed: {e}")
        # Re-raise to ensure the pipeline fails loudly rather than returning fake data
        raise

def write_summary(metrics: Dict[str, Any], output_path: str = "data/processed/baseline_results.json") -> None:
    """
    Write the baseline metrics to a JSON file.
    
    Args:
        metrics: Dictionary containing mean, variance, status, design_type.
        output_path: Path to the output JSON file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure status is success before writing
    if 'status' not in metrics:
        metrics['status'] = 'success'
        
    if metrics['status'] != 'success':
        logger.warning(f"Writing summary with status: {metrics['status']}")
    else:
        logger.info(f"Writing successful baseline summary to {output_path}")
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    logger.info(f"Successfully wrote {output_path}")

def main():
    """
    Main entry point for the baseline summary pipeline.
    Produces data/processed/baseline_results.json.
    """
    logger.info("Starting Baseline Summary Pipeline (T016)")
    
    try:
        # 1. Load and prepare data
        data_context = load_and_prepare_data()
        
        # 2. Calculate metrics
        metrics = calculate_baseline_metrics(data_context)
        
        # 3. Construct final output object with required schema keys
        final_output = {
            'mean': metrics['mean'],
            'variance': metrics['variance'],
            'status': 'success',
            'design_type': metrics['design_type'],
            'metadata': {
                'n_observations': metrics['n_observations'],
                'n_dropped': metrics['n_dropped']
            }
        }
        
        # 4. Write to disk
        write_summary(final_output)
        
        logger.info("Baseline Summary Pipeline completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        # Do not write a partial or failed file; let the script exit with error
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())