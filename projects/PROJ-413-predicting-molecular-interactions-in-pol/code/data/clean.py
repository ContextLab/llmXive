import os
import sys
import logging
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))

from utils.exceptions import DataError
from utils.logger import PerformanceLogger, log_performance
from utils.seed_utils import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/cleaning.log')
    ]
)
logger = logging.getLogger(__name__)

def validate_adhesion_energy(df: Any) -> bool:
    """
    Validates that adhesion energy column exists and has no missing values.
    Returns True if valid, raises DataError otherwise.
    """
    if 'adhesion_energy' not in df.columns:
        raise DataError("E-DATA-001: Missing required column 'adhesion_energy'")
    
    missing = df['adhesion_energy'].isna().sum()
    if missing > 0:
        raise DataError(f"E-DATA-001: Found {missing} missing values in 'adhesion_energy'")
    
    return True

def validate_row_count(df: Any, min_rows: int = 100) -> bool:
    """
    Validates that the dataset has at least min_rows rows.
    Returns True if valid, raises DataError otherwise.
    """
    row_count = len(df)
    if row_count < min_rows:
        raise DataError(f"E-DATA-001: Dataset has {row_count} rows, minimum required is {min_rows}")
    return True

def validate_missing_values(df: Any, threshold: float = 0.05) -> Dict[str, float]:
    """
    Validates that missing values per column are below the threshold.
    Returns a dict of column names to missing value ratios.
    Raises DataError if any column exceeds threshold.
    """
    missing_ratios = {}
    for col in df.columns:
        ratio = df[col].isna().sum() / len(df)
        missing_ratios[col] = ratio
        if ratio > threshold:
            raise DataError(f"E-DATA-002: Column '{col}' has {ratio:.2%} missing values (threshold: {threshold:.0%})")
    
    return missing_ratios

def calculate_margin_of_error(std_dev: float, n: int, confidence_level: float = 0.95) -> float:
    """
    Calculates the margin of error for a given standard deviation and sample size.
    Uses the formula: z * (std / sqrt(n))
    For 95% confidence, z = 1.96
    """
    if n <= 1:
        return float('inf')
    
    # Z-score for 95% confidence interval
    z_score = 1.96
    margin = z_score * (std_dev / math.sqrt(n))
    return margin

def clean_and_validate(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main cleaning and validation pipeline.
    1. Loads data from input_path
    2. Validates adhesion energy presence and completeness
    3. Validates row count (min 100)
    4. Validates missing values per column (max 5%)
    5. If 100 <= rows < 500, logs warning and calculates margin of error
    6. Saves cleaned data to output_path
    7. Returns summary statistics
    """
    import pandas as pd
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    initial_rows = len(df)
    logger.info(f"Loaded {initial_rows} rows")
    
    # Step 1: Validate adhesion energy
    try:
        validate_adhesion_energy(df)
        logger.info("Adhesion energy validation passed")
    except DataError as e:
        logger.error(f"Adhesion energy validation failed: {e}")
        raise
    
    # Step 2: Validate row count
    try:
        validate_row_count(df, min_rows=100)
        logger.info("Row count validation passed")
    except DataError as e:
        logger.error(f"Row count validation failed: {e}")
        raise
    
    # Step 3: Validate missing values
    try:
        missing_ratios = validate_missing_values(df, threshold=0.05)
        logger.info(f"Missing values validation passed: {missing_ratios}")
    except DataError as e:
        logger.error(f"Missing values validation failed: {e}")
        raise
    
    # Step 4: Limited Power Warning Logic (T015)
    row_count = len(df)
    summary = {
        "initial_rows": initial_rows,
        "final_rows": row_count,
        "missing_ratios": missing_ratios,
        "power_status": "adequate"
    }
    
    if 100 <= row_count < 500:
        summary["power_status"] = "limited"
        warning_msg = (
            f"Limited Power Warning: Dataset has {row_count} rows (target: 500). "
            f"Results should be interpreted with caution."
        )
        logger.warning(warning_msg)
        
        # Calculate margin of error for adhesion energy
        if 'adhesion_energy' in df.columns:
            std_dev = df['adhesion_energy'].std()
            if not math.isnan(std_dev) and row_count > 1:
                moe = calculate_margin_of_error(std_dev, row_count)
                summary["margin_of_error"] = moe
                summary["std_dev"] = std_dev
                summary["confidence_interval_95"] = (
                    f"{df['adhesion_energy'].mean() - moe:.4f} to {df['adhesion_energy'].mean() + moe:.4f}"
                )
                logger.info(f"Margin of Error (95% CI): ±{moe:.4f}")
                logger.info(f"95% Confidence Interval: {summary['confidence_interval_95']}")
            else:
                summary["margin_of_error"] = None
                logger.warning("Could not calculate margin of error (std_dev is NaN or n <= 1)")
    
    # Step 5: Save cleaned data
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")
    
    # Step 6: Save summary statistics
    summary_path = Path(output_path).with_suffix('.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved summary statistics to {summary_path}")
    
    return summary

def main():
    """
    Entry point for the cleaning script.
    Expects environment variables:
    - INPUT_PATH: Path to raw data CSV
    - OUTPUT_PATH: Path to save cleaned data CSV
    """
    set_seed(42)
    
    input_path = os.getenv('INPUT_PATH', 'data/raw/molnet_raw.csv')
    output_path = os.getenv('OUTPUT_PATH', 'data/curated/curated_dataset.csv')
    
    logger.info(f"Starting data cleaning pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        summary = clean_and_validate(input_path, output_path)
        logger.info("Data cleaning completed successfully")
        logger.info(f"Summary: {json.dumps(summary, indent=2)}")
    except DataError as e:
        logger.error(f"Data error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()