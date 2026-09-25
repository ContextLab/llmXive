"""
Cohort construction module for single-dataset analysis.

Implements the logic to filter, validate, and construct the final analysis cohort
from the preprocessed Cyberbullying Survey 2021 data.

Per Plan 'Revised Approach': Uses only the Cyberbullying Survey 2021.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
COHORT_PATH = Path("data/results/analysis_cohort.csv")
VALIDATION_REPORT_PATH = Path("data/results/validation_report.json")
PREPROCESSED_DATA_PATH = Path("data/results/preprocessed_data.csv")

def load_preprocessed_data() -> pd.DataFrame:
    """
    Load the preprocessed dataset from disk.
    
    Returns:
        pd.DataFrame: The preprocessed dataset.
        
    Raises:
        FileNotFoundError: If the preprocessed data file does not exist.
        RuntimeError: If the data is empty or missing required columns.
    """
    if not PREPROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Preprocessed data not found at {PREPROCESSED_DATA_PATH}. "
            "Run preprocessing pipeline first."
        )
    
    df = pd.read_csv(PREPROCESSED_DATA_PATH)
    
    if df.empty:
        raise RuntimeError("Preprocessed data is empty.")
    
    required_cols = [
        'harassment_severity', 'social_support', 'depression', 'anxiety',
        'age', 'gender', 'education', 'income'
    ]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise RuntimeError(f"Missing required columns in preprocessed data: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows from preprocessed data.")
    return df

def filter_critical_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows with critical missing values in key variables.
    
    Critical variables: harassment_severity, social_support, and at least one
    mental health outcome (depression, anxiety, ptsd if available).
    
    Args:
        df (pd.DataFrame): Input dataframe.
        
    Returns:
        pd.DataFrame: Filtered dataframe.
    """
    logger.info("Filtering rows with critical missing values...")
    
    critical_cols = ['harassment_severity', 'social_support']
    outcome_cols = ['depression', 'anxiety']
    if 'ptsd' in df.columns:
        outcome_cols.append('ptsd')
    
    # Check for missingness in critical predictors
    df = df.dropna(subset=critical_cols)
    
    # Check for missingness in at least one outcome
    # We need at least one outcome to be present to proceed
    # If all outcomes are missing, drop the row
    if len(outcome_cols) > 0:
        mask = df[outcome_cols].isna().all(axis=1)
        df = df[~mask]
    
    logger.info(f"Filtered to {len(df)} rows after removing critical missing values.")
    return df

def check_harassment_variance(df: pd.DataFrame) -> bool:
    """
    Check if harassment_severity has sufficient variance.
    
    Criteria: SD > 0.5 and N > 30.
    
    Args:
        df (pd.DataFrame): Input dataframe.
        
    Returns:
        bool: True if variance check passes, False otherwise.
    """
    n = len(df)
    if n <= 30:
        logger.error(f"Insufficient sample size for variance check: N={n} (need > 30)")
        return False
    
    sd = df['harassment_severity'].std()
    if pd.isna(sd) or sd <= 0.5:
        logger.error(f"Insufficient variance in harassment_severity: SD={sd:.4f} (need > 0.5)")
        return False
    
    logger.info(f"Variance check passed: N={n}, SD={sd:.4f}")
    return True

def construct_analysis_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct the final analysis cohort.
    
    This function prepares the dataframe for analysis by ensuring all
    necessary variables are present and properly typed.
    
    Args:
        df (pd.DataFrame): Filtered dataframe.
        
    Returns:
        pd.DataFrame: Final analysis cohort.
    """
    logger.info("Constructing analysis cohort...")
    
    # Ensure binary exposure is derived if not already present
    if 'harassment_exposure' not in df.columns:
        df['harassment_exposure'] = (df['harassment_severity'] > 0).astype(int)
        logger.info("Derived binary harassment_exposure variable.")
    
    # Select only the columns needed for analysis
    analysis_cols = [
        'harassment_severity', 'harassment_exposure', 'social_support',
        'depression', 'anxiety', 'age', 'gender', 'education', 'income'
    ]
    
    # Add ptsd if present
    if 'ptsd' in df.columns:
        analysis_cols.append('ptsd')
    
    # Filter to existing columns
    existing_cols = [col for col in analysis_cols if col in df.columns]
    cohort_df = df[existing_cols].copy()
    
    logger.info(f"Analysis cohort constructed with {len(cohort_df)} rows and {len(existing_cols)} columns.")
    return cohort_df

def save_cohort(df: pd.DataFrame, path: Optional[Path] = None) -> None:
    """
    Save the analysis cohort to disk.
    
    Args:
        df (pd.DataFrame): The analysis cohort dataframe.
        path (Optional[Path]): Output path. Defaults to COHORT_PATH.
    """
    output_path = path or COHORT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Analysis cohort saved to {output_path}")

def validate_analysis_cohort(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the analysis cohort against quality checks.
    
    Checks:
        1. Harassment variance (SD > 0.5, N > 30)
        2. Collinearity (VIF < 5) - computed in validation module
        3. Data completeness
    
    Args:
        df (pd.DataFrame): The analysis cohort.
        
    Returns:
        Dict[str, Any]: Validation report.
    """
    report = {
        "pass": True,
        "checks": {},
        "warnings": []
    }
    
    # Check 1: Harassment Variance
    variance_ok = check_harassment_variance(df)
    report["checks"]["harassment_variance"] = {
        "passed": variance_ok,
        "n": len(df),
        "sd": float(df['harassment_severity'].std()) if not df.empty else None
    }
    if not variance_ok:
        report["pass"] = False
        raise RuntimeError("Cohort validity check failed: Harassment variance insufficient.")
    
    # Check 2: Basic Completeness
    missing_counts = df.isna().sum()
    if missing_counts.sum() > 0:
        report["warnings"].append(f"Missing values detected: {missing_counts.to_dict()}")
    
    # Check 3: Sample Size
    if len(df) < 30:
        report["pass"] = False
        raise RuntimeError("Cohort validity check failed: Sample size too small.")
    
    logger.info("Cohort validation completed successfully.")
    return report

def main():
    """
    Main entry point for cohort construction.
    
    Orchestrates the loading, filtering, validation, and saving of the analysis cohort.
    """
    logger.info("Starting cohort construction...")
    
    try:
        # 1. Load preprocessed data
        df = load_preprocessed_data()
        
        # 2. Filter critical missing values
        df_filtered = filter_critical_missing(df)
        
        # 3. Construct analysis cohort
        cohort_df = construct_analysis_cohort(df_filtered)
        
        # 4. Validate cohort
        validation_report = validate_analysis_cohort(cohort_df)
        
        # 5. Save validation report
        VALIDATION_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(VALIDATION_REPORT_PATH, 'w') as f:
            json.dump(validation_report, f, indent=2)
        logger.info(f"Validation report saved to {VALIDATION_REPORT_PATH}")
        
        # 6. Save cohort
        save_cohort(cohort_df)
        
        logger.info("Cohort construction completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Cohort construction failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())