import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure code directory is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import logger setup
from utils.logger import get_logger

def load_preprocessed_data():
    """Load the preprocessed data from T013d output."""
    logger = get_logger("cohort")
    # T013d output is 'data/results/preprocessed_data.csv'
    path = Path("data/results/preprocessed_data.csv")
    import pandas as pd
    if not path.exists():
        logger.error(f"Preprocessed data not found at {path}. Ensure T013d completed successfully.")
        raise FileNotFoundError(f"Preprocessed data not found at {path}.")
    logger.info(f"Loaded preprocessed data from {path} with {len(pd.read_csv(path))} rows.")
    return pd.read_csv(path)

def filter_critical_missing(df):
    """Filter rows with critical missing values based on T013d logic."""
    logger = get_logger("cohort")
    # T013d handles outcome missingness. T014 filters remaining critical predictors/outcomes if any.
    # Critical columns as per task description: harassment_severity, social_support, mental health outcomes.
    critical_cols = ['harassment_severity', 'social_support']
    # Ensure at least one outcome exists
    outcomes = [c for c in ['depression', 'anxiety', 'ptsd'] if c in df.columns]
    if outcomes:
        critical_cols.extend(outcomes)
    
    initial = len(df)
    # Drop rows where ANY critical column is NaN
    df = df.dropna(subset=critical_cols)
    dropped = initial - len(df)
    logger.info(f"Filtered critical missing values. Dropped {dropped} rows. Remaining: {len(df)}.")
    return df

def check_harassment_variance(df):
    """Check variance of Harassment Exposure (SD > 0.5, N > 30)."""
    logger = get_logger("cohort")
    if "harassment_exposure" not in df.columns:
        logger.error("E-LOW-VAR-001: harassment_exposure column missing.")
        raise RuntimeError("E-LOW-VAR-001: harassment_exposure column missing.")
    
    col = df["harassment_exposure"]
    sd = col.std()
    n = len(col)
    
    logger.info(f"Harassment Exposure Variance Check: SD={sd:.4f}, N={n}")
    
    if sd <= 0.5 or n <= 30:
        logger.error(f"E-LOW-VAR-001: Variance check failed (SD={sd}, N={n}).")
        raise RuntimeError(f"E-LOW-VAR-001: Variance check failed (SD={sd}, N={n}).")
    return True

def construct_analysis_cohort(df):
    """Construct the final analysis cohort by selecting relevant columns."""
    logger = get_logger("cohort")
    # Select relevant columns as defined in the task and spec
    desired_cols = [
        'age', 'gender', 'education', 'income', 
        'social_support', 'harassment_severity', 'harassment_exposure',
        'depression', 'anxiety', 'ptsd', 'platform'
    ]
    # Filter to only those present in the dataframe
    cols = [c for c in desired_cols if c in df.columns]
    if not cols:
        logger.warning("No expected columns found. Using all columns.")
        cols = df.columns.tolist()
    
    logger.info(f"Constructing cohort with columns: {cols}")
    return df[cols].reset_index(drop=True)

def save_cohort(df):
    """Save the analysis cohort to the declared output path."""
    logger = get_logger("cohort")
    output_path = Path("data/results/analysis_cohort.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Analysis cohort saved to {output_path} with {len(df)} rows.")
    return output_path

def validate_analysis_cohort(df):
    """Run validation checks on the cohort (Variance Check)."""
    logger = get_logger("cohort")
    # T014 requirement: Check variance of Harassment Exposure
    check_harassment_variance(df)
    
    # Note: VIF check is moved to T015 (Validation task) as per task dependencies.
    # T014 focuses on filtering and variance check.
    
    logger.info("Cohort validation (variance) passed.")
    return True

def main():
    """Entry point for cohort construction (T014)."""
    logger = get_logger("cohort")
    logger.info("Starting T014: Implement cohort construction.")
    try:
        # 1. Load preprocessed data (output of T013d)
        df = load_preprocessed_data()
        
        # 2. Filter critical missing values (redundant if T013d did it, but ensures safety)
        df = filter_critical_missing(df)
        
        # 3. Check variance of harassment exposure
        check_harassment_variance(df)
        
        # 4. Construct final cohort
        df = construct_analysis_cohort(df)
        
        # 5. Validate (variance check again as final gate)
        validate_analysis_cohort(df)
        
        # 6. Save to declared output path
        save_cohort(df)
        
        logger.info("T014 completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T014 Cohort construction failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())