import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np

from code.src.utils.config import get_processed_data_dir, get_logs_dir, ensure_directories

logger = logging.getLogger(__name__)

def check_zero_variance(df: pd.DataFrame, column: str) -> bool:
    """Check if a column has zero variance (constant value)."""
    if column not in df.columns:
        return False
    unique_vals = df[column].nunique()
    return unique_vals <= 1

def filter_cohort(
    df: pd.DataFrame,
    min_age: int = 65,
    required_columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Filter the cohort based on age and required non-null columns.
    
    Args:
        df: Input DataFrame
        min_age: Minimum age threshold (default 65)
        required_columns: List of columns that must be non-null.
                          Defaults to schema-defined covariates if None.
    
    Returns:
        Tuple of (filtered DataFrame, number of dropped rows)
    """
    if required_columns is None:
        # Schema-defined covariates per FR-002
        required_columns = [
            'age', 'sex', 'bmi', 
            'dietary_fiber_intake', 'antibiotic_use_history',
            'shannon_diversity', 'cognitive_flexibility_score'
        ]
    
    initial_count = len(df)
    
    # Filter by age
    logger.info(f"Filtering for age >= {min_age}")
    df = df[df['age'] >= min_age].copy()
    
    # Listwise deletion for missing covariates
    logger.info(f"Dropping rows with missing values in: {required_columns}")
    df = df.dropna(subset=required_columns)
    
    # Check for zero variance in key metrics (Edge Case T012)
    for col in ['shannon_diversity', 'cognitive_flexibility_score']:
        if col in df.columns and check_zero_variance(df, col):
            logger.warning(f"Column '{col}' has zero variance. Skipping correlation analysis for this metric.")
    
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} rows due to filtering criteria.")
    
    return df, dropped_count

def main():
    """Main entry point for filtering script."""
    from code.src.utils.config import get_raw_data_dir, setup_logging
    
    setup_logging("filtering.log")
    ensure_directories()
    
    # Load merged data (output of T010)
    input_path = get_raw_data_dir() / "merged_cohort.csv"
    if not input_path.exists():
        # Fallback to synthetic data if merged not found (for testing)
        input_path = get_raw_data_dir() / "synthetic_data.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Filter
    filtered_df, dropped = filter_cohort(df)
    
    # Save output
    output_dir = get_processed_data_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "filtered_cohort.csv"
    
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered cohort to {output_path} ({len(filtered_df)} rows)")
    
    # Log dropped count to specific log file as per T013
    log_dir = get_logs_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "filtering.log", "a") as f:
        f.write(f"Dropped rows count: {dropped}\n")

if __name__ == "__main__":
    main()
