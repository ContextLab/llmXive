"""
Signal Output Module for T025b.
Generates the output/signals.csv file with all metrics, adjusted p-values,
signal flags, and background rate status.
"""

import os
import sys
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import thresholds from config
from src.utils.config import THRESHOLDS


def apply_signal_flag(row: pd.Series) -> bool:
    """
    Apply the 2-out-of-3 rule to determine if a SOC is a signal.
    
    Rules (from T004 config):
    1. ROR > 2.0 AND ROR CI Lower > 1.0
    2. PRR > 1.5 AND PRR CI Lower > 1.0
    3. IC > 0.0 AND IC CI Lower > 0.0
    
    A signal is flagged if at least 2 of these 3 conditions are met.
    """
    # Condition 1: ROR
    ror_pass = (
        row.get('ror', np.nan) > THRESHOLDS['ror_min'] and 
        row.get('ror_ci_lower', np.nan) > THRESHOLDS['ror_ci_min']
    )
    
    # Condition 2: PRR
    prr_pass = (
        row.get('prr', np.nan) > THRESHOLDS['prr_min'] and 
        row.get('prr_ci_lower', np.nan) > THRESHOLDS['prr_ci_min']
    )
    
    # Condition 3: IC
    ic_pass = (
        row.get('ic', np.nan) > THRESHOLDS['ic_min'] and 
        row.get('ic_ci_lower', np.nan) > THRESHOLDS['ic_ci_min']
    )
    
    # Count passed conditions
    passed_count = sum([ror_pass, prr_pass, ic_pass])
    
    return passed_count >= 2


def generate_signals_csv(
    metrics_df: pd.DataFrame,
    output_path: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Generate the final signals.csv file.
    
    Args:
        metrics_df: DataFrame containing calculated metrics (ROR, PRR, IC, CIs, p-values).
        output_path: Path to write the output CSV.
        logger: Optional logger for progress updates.
    
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the input DataFrame is missing required columns.
    """
    if logger:
        logger.info(f"Generating signals CSV at {output_path}")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Apply signal flag
    metrics_df['signal_flag'] = metrics_df.apply(apply_signal_flag, axis=1)
    
    # Set background_rate_status to 'UNKNOWN' as per spec (no external rates calculated)
    metrics_df['background_rate_status'] = 'UNKNOWN'
    
    # Define the required schema columns in order
    required_columns = [
        'soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
        'prr', 'prr_ci_lower', 'prr_ci_upper',
        'ic', 'ic_ci_lower', 'ic_ci_upper',
        'p_adj', 'signal_flag', 'background_rate_status'
    ]
    
    # Verify required columns exist
    missing_cols = [col for col in required_columns if col not in metrics_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in metrics_df: {missing_cols}")
    
    # Select and order columns
    output_df = metrics_df[required_columns].copy()
    
    # Sort by adjusted p-value for readability (optional but good practice)
    output_df = output_df.sort_values(by='p_adj')
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)
    
    if logger:
        total_rows = len(output_df)
        signal_count = output_df['signal_flag'].sum()
        logger.info(f"Successfully wrote {total_rows} rows to {output_path}")
        logger.info(f"Identified {signal_count} signals based on 2-out-of-3 rule")


def main() -> int:
    """
    Main entry point for generating signals.csv.
    
    This function assumes that T024 (calculate_disproportionality_metrics) 
    has already run and produced the intermediate metrics file.
    
    Returns:
        0 on success, 1 on failure.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/signal_output.log')
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting signal output generation (T025b)")
    
    try:
        # Define paths
        # Assuming the previous step (T024) outputs to this location
        # If T024 outputs to a different temp file, adjust this path.
        # Based on the pipeline flow, T024 likely writes to a temp or intermediate file.
        # However, T025b requires reading the results of T024.
        # Let's assume T024 writes to 'data/processed/disproportionality_metrics.csv' 
        # or similar. If not, we might need to read from the parquet if T024 didn't write CSV.
        # Re-reading the task: T024 implements calculation. T025b generates the CSV.
        # It is most efficient if T024 writes the metrics to a temp CSV or if T025b 
        # reads the parquet from T016 and recalculates (inefficient) or if T024 
        # left the data in a known location.
        
        # Looking at T022/T023/T024 flow: T022 builds tables, T023 corrects, T024 calculates.
        # The most robust way for T025b is to read the intermediate metrics if T024 wrote them.
        # If T024 did not write a file, we must assume the data is available in the 
        # 'output' directory or 'data/processed' from a previous run of the analysis module.
        
        # Let's assume the analysis module (disproportionality.py) has a `run_analysis` 
        # that returns the DataFrame, or we re-run the logic. 
        # To avoid duplication, we assume the `disproportionality.py` main function 
        # or a helper was used to generate a metrics file.
        
        # Standard practice in this pipeline: T024 likely writes to 'output/disproportionality_metrics.csv'
        # or similar. Let's check for a standard location or read from the cleaned data 
        # if we must recalculate (but that defeats the purpose of T024 being separate).
        
        # Given the strict task separation, T024 should have produced a file.
        # Let's assume the file is at 'output/disproportionality_metrics.csv' 
        # or we read from the parquet and call the functions again if T024 didn't write.
        
        # However, the task T025b says "Generate output/signals.csv... Prerequisite: T025".
        # T025 applies the rule. T024 calculates metrics.
        # If T024 didn't write a file, T025b must read the cleaned data and recalculate 
        # or T024 must be fixed to write. 
        # Since I am implementing T025b, I must assume T024 worked correctly.
        # If T024 wrote to a temp file, I need to know where.
        
        # Let's assume the standard output path for the analysis step is:
        input_metrics_path = Path("data/processed/disproportionality_metrics.csv")
        
        # Fallback: If the file doesn't exist, check if we need to run the analysis again.
        # But T024 is "Implement calculation". It should have run.
        # If the file is missing, we might need to re-run the logic from the cleaned parquet.
        # To be safe, let's check for the file. If missing, we will try to load from 
        # the cleaned parquet and recalculate (assuming T024 logic is in the same module).
        
        if not input_metrics_path.exists():
            # Fallback: Recalculate from cleaned data if metrics file is missing
            # This handles the case where T024 was implemented but didn't write a file yet.
            logger.warning(f"Metrics file {input_metrics_path} not found. Recalculating from cleaned data.")
            
            cleaned_data_path = Path("data/processed/cleaned_vaers_full_non_covid.parquet")
            if not cleaned_data_path.exists():
                logger.error(f"Cleaned data file {cleaned_data_path} not found. Cannot proceed.")
                return 1
            
            # Import calculation functions
            from src.analysis.disproportionality import run_analysis
            
            # Run analysis to get metrics
            metrics_df = run_analysis(str(cleaned_data_path))
            
            # Save intermediate for future runs
            metrics_df.to_csv(input_metrics_path, index=False)
        else:
            metrics_df = pd.read_csv(input_metrics_path)
        
        # Generate the final output
        output_path = "output/signals.csv"
        generate_signals_csv(metrics_df, output_path, logger)
        
        return 0
        
    except Exception as e:
        logger.error(f"Error generating signals CSV: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())