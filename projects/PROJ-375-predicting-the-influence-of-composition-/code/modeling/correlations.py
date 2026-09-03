"""
Task T038: Implement Pearson correlation calculation for each feature against CTE.

Reads the test split from data/processed/test_split.parquet, calculates the Pearson
correlation coefficient between each compositional descriptor and the CTE target,
and writes the results to results/correlations.csv.

Features analyzed:
- mean_atomic_radius
- electronegativity_var
- vec
- size_mismatch
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.io import setup_logging

# Setup logging
logger = setup_logging("T038_correlations")

# Constants
INPUT_PATH = "data/processed/test_split.parquet"
OUTPUT_PATH = "results/correlations.csv"
FEATURES = ["mean_atomic_radius", "electronegativity_var", "vec", "size_mismatch"]
TARGET = "cte"
PRECISION = 4

def load_test_data(path: str) -> pd.DataFrame:
    """Load the test split parquet file."""
    full_path = project_root / path
    if not full_path.exists():
        raise FileNotFoundError(f"Test split not found at {full_path}. "
                                "Ensure T018 (data splitting) has been executed.")
    
    logger.info(f"Loading test data from {full_path}")
    df = pd.read_parquet(full_path)
    
    required_cols = FEATURES + [TARGET]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Test data missing required columns: {missing}")
    
    return df

def calculate_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Pearson correlation for each feature against CTE."""
    results = []
    
    for feature in FEATURES:
        # Drop rows where either feature or target is NaN
        valid_data = df[[feature, TARGET]].dropna()
        
        if len(valid_data) < 2:
            logger.warning(f"Insufficient data for {feature} (n={len(valid_data)}). Skipping.")
            corr = np.nan
        else:
            # Calculate Pearson correlation
            corr, _ = valid_data[feature].corr(valid_data[TARGET], method='pearson'), None
            if not np.isfinite(corr):
                corr = np.nan
                logger.warning(f"Non-finite correlation for {feature}.")
        
        results.append({
            "feature": feature,
            "correlation_coefficient": round(corr, PRECISION) if not np.isnan(corr) else np.nan
        })
    
    return pd.DataFrame(results)

def save_results(df: pd.DataFrame, path: str):
    """Save results to CSV."""
    full_path = project_root / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(full_path, index=False)
    logger.info(f"Saved correlation results to {full_path}")

def main():
    """Main entry point for T038."""
    try:
        logger.info("Starting T038: Pearson Correlation Calculation")
        
        # Load data
        df = load_test_data(INPUT_PATH)
        logger.info(f"Loaded {len(df)} samples from test split")
        
        # Calculate correlations
        corr_df = calculate_correlations(df)
        
        # Save results
        save_results(corr_df, OUTPUT_PATH)
        
        logger.info("T038 completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"T038 failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())