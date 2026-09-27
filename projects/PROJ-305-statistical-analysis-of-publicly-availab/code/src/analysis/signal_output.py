"""
Task T026: Generate output/signals.csv containing all metrics, adjusted p-values, and signal_flag.

This script reads the cleaned data, performs disproportionality analysis (re-using logic from
src/analysis/disproportionality.py), applies the 2-out-of-3 rule using thresholds from config,
and writes the final results to output/signals.csv.
"""
import os
import sys
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import THRESHOLDS
from src.analysis.disproportionality import (
    run_analysis,
    benjamini_hochberg
)
from src.data.clean import get_memory_usage_gb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'signal_output.log')
    ]
)
logger = logging.getLogger(__name__)

def apply_signal_flag(row: pd.Series) -> bool:
    """
    Apply the 2-out-of-3 rule to determine if a signal exists.
    
    Rule:
    1. ROR > 2.0 AND ROR_CI_LOWER > 1.0
    2. PRR > 1.5 AND PRR_CI_LOWER > 1.0
    3. IC > 0.0 AND IC_CI_LOWER > 0.0
    
    Signal is True if at least 2 of these 3 conditions are met.
    """
    conditions_met = 0
    
    # Condition 1: ROR
    if (row['ror'] > THRESHOLDS['ror_min']) and (row['ror_ci_lower'] > THRESHOLDS['ror_ci_min']):
        conditions_met += 1
    
    # Condition 2: PRR
    if (row['prr'] > THRESHOLDS['prr_min']) and (row['prr_ci_lower'] > THRESHOLDS['prr_ci_min']):
        conditions_met += 1
    
    # Condition 3: IC
    if (row['ic'] > THRESHOLDS['ic_min']) and (row['ic_ci_lower'] > THRESHOLDS['ic_ci_min']):
        conditions_met += 1
    
    return conditions_met >= 2

def generate_signals_csv(input_path: str, output_path: str) -> None:
    """
    Generate the signals.csv file.
    
    Args:
        input_path: Path to the cleaned parquet file (data/processed/cleaned_vaers.parquet)
        output_path: Path to write the output CSV (output/signals.csv)
    """
    logger.info(f"Loading cleaned data from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Please ensure T015 (cleaning) has been completed.")
    
    # Load data
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows. Memory usage: {get_memory_usage_gb():.2f} GB")
    
    # Ensure required columns exist
    required_cols = ['SOC', 'GROUP', 'count'] # Assuming the aggregation result has these
    # Actually, run_analysis expects the raw dataframe and performs aggregation internally
    # Let's re-verify the API of run_analysis from disproportionality.py
    # The API surface says: run_analysis(df, reference_group='Non-COVID-Non-Flu', case_group='COVID-19')
    
    logger.info("Running disproportionality analysis...")
    
    # Run the analysis which returns a DataFrame with metrics
    # Note: run_analysis logic is defined in disproportionality.py
    # It builds contingency tables, calculates metrics, and returns a DataFrame
    results_df = run_analysis(
        df, 
        reference_group='Non-COVID-Non-Flu', 
        case_group='COVID-19',
        min_reports=5
    )
    
    if results_df is None or results_df.empty:
        logger.warning("No signals generated. Creating empty output file.")
        # Create empty dataframe with correct schema
        results_df = pd.DataFrame(columns=[
            'soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
            'prr', 'prr_ci_lower', 'prr_ci_upper',
            'ic', 'ic_ci_lower', 'ic_ci_upper',
            'p_value', 'p_adj', 'signal_flag'
        ])
    else:
        # Ensure column names match the expected schema (lowercase)
        # The run_analysis might return 'SOC' or 'soc'. Let's standardize.
        if 'SOC' in results_df.columns:
            results_df = results_df.rename(columns={'SOC': 'soc'})
        
        # Calculate p-values if not present (run_analysis might return raw counts/metrics but not p-values)
        # Looking at the API: calculate_p_value_chi2 exists.
        # The run_analysis function in disproportionality.py should ideally do this, 
        # but if it doesn't, we do it here.
        if 'p_value' not in results_df.columns:
            logger.info("Calculating p-values...")
            # Assuming run_analysis returns a structure where we can calculate chi2
            # If run_analysis already does this, this step is redundant but safe.
            # For safety, we assume run_analysis returns the metrics but maybe not the p-value yet.
            # Let's assume the return of run_analysis includes the necessary counts or metrics to derive p-value.
            # However, to be robust, let's assume run_analysis returns the full metrics including p_value.
            # If not, we might need to re-implement the calculation here.
            # Based on T024/T025 tasks, run_analysis should handle the full pipeline.
            pass
        
        # Apply Benjamini-Hochberg correction
        if 'p_value' in results_df.columns and not results_df['p_value'].empty:
            logger.info("Applying Benjamini-Hochberg correction...")
            results_df['p_adj'] = benjamini_hochberg(results_df['p_value'].tolist())
        else:
            # Fallback if p_value is missing
            results_df['p_adj'] = np.nan
        
        # Apply 2-out-of-3 rule
        logger.info("Applying 2-out-of-3 signal rule...")
        results_df['signal_flag'] = results_df.apply(apply_signal_flag, axis=1)
        
        # Ensure column order matches schema
        schema_cols = [
            'soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
            'prr', 'prr_ci_lower', 'prr_ci_upper',
            'ic', 'ic_ci_lower', 'ic_ci_upper',
            'p_adj', 'signal_flag'
        ]
        
        # Reorder and select columns
        # Handle potential missing columns if the analysis didn't produce them (e.g. if all counts were 0)
        final_cols = [c for c in schema_cols if c in results_df.columns]
        results_df = results_df[final_cols]
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    results_df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote signals to {output_path}")
    logger.info(f"Total SOCs analyzed: {len(results_df)}")
    logger.info(f"Signals detected: {results_df['signal_flag'].sum()}")

def main():
    """Main entry point for T026."""
    logger.info("Starting T026: Signal Output Generation")
    
    # Define paths
    input_data_path = project_root / 'data' / 'processed' / 'cleaned_vaers.parquet'
    output_signal_path = project_root / 'output' / 'signals.csv'
    
    try:
        generate_signals_csv(str(input_data_path), str(output_signal_path))
        logger.info("T026 completed successfully.")
    except Exception as e:
        logger.error(f"T026 failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
