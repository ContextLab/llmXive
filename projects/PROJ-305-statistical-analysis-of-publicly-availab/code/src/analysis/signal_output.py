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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def apply_signal_flag(row: pd.Series) -> bool:
    """
    Apply the 2-out-of-3 rule to determine if a SOC is a signal.
    
    Rules (from T004 config):
    1. ROR > 2.0 AND ROR_CI_LOWER > 1.0
    2. PRR > 1.5 AND PRR_CI_LOWER > 1.0
    3. IC > 0.0 AND IC_CI_LOWER > 0.0
    
    Signal is True if at least 2 of these 3 conditions are met.
    """
    # Condition 1: ROR criteria
    cond_ror = (
        row.get('ror', 0) > THRESHOLDS['ror_min'] and 
        row.get('ror_ci_lower', 0) > THRESHOLDS['ror_ci_min']
    )
    
    # Condition 2: PRR criteria
    cond_prr = (
        row.get('prr', 0) > THRESHOLDS['prr_min'] and 
        row.get('prr_ci_lower', 0) > THRESHOLDS['prr_ci_min']
    )
    
    # Condition 3: IC criteria
    cond_ic = (
        row.get('ic', 0) > THRESHOLDS['ic_min'] and 
        row.get('ic_ci_lower', 0) > THRESHOLDS['ic_ci_min']
    )
    
    # Count how many conditions are met
    conditions_met = sum([cond_ror, cond_prr, cond_ic])
    
    return conditions_met >= 2

def generate_signals_csv(input_path: str, output_path: str) -> None:
    """
    Load the disproportionality metrics, apply the signal flag, and save to CSV.
    
    Args:
        input_path: Path to the input CSV containing metrics (e.g., from T025)
        output_path: Path to save the final signals CSV
    """
    logger.info(f"Loading metrics from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_columns = [
        'soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
        'prr', 'prr_ci_lower', 'prr_ci_upper',
        'ic', 'ic_ci_lower', 'ic_ci_upper', 'p_adj'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input: {missing_cols}")
    
    logger.info(f"Applying signal flag rule (2-out-of-3) to {len(df)} rows")
    df['signal_flag'] = df.apply(apply_signal_flag, axis=1)
    
    # Ensure column order matches specification
    output_columns = [
        'soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
        'prr', 'prr_ci_lower', 'prr_ci_upper',
        'ic', 'ic_ci_lower', 'ic_ci_upper',
        'p_adj', 'signal_flag'
    ]
    
    # Filter to only include expected columns if extra exist, or reorder
    final_df = df[output_columns]
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Saving signals to {output_path}")
    final_df.to_csv(output_path, index=False)
    
    signal_count = final_df['signal_flag'].sum()
    logger.info(f"Total signals identified: {signal_count} out of {len(final_df)} SOCs")
    
    return final_df

def main():
    """
    Main entry point for T026: Generate output/signals.csv
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_file = project_root / "output" / "disproportionality_metrics.csv"
    output_file = project_root / "output" / "signals.csv"
    
    # If input file doesn't exist at the standard location, try to find it
    # or use the path provided by the pipeline context
    if not input_file.exists():
        # Fallback: look in common locations
        fallback_paths = [
            project_root / "output" / "metrics.csv",
            project_root / "data" / "processed" / "metrics.csv"
        ]
        for fallback in fallback_paths:
            if fallback.exists():
                input_file = fallback
                logger.info(f"Using fallback input path: {input_file}")
                break
    
    if not input_file.exists():
        logger.error(f"Input metrics file not found. Expected at {input_file}")
        sys.exit(1)
    
    try:
        generate_signals_csv(str(input_file), str(output_file))
        logger.info("T026 completed successfully: output/signals.csv generated")
    except Exception as e:
        logger.error(f"Error generating signals CSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
