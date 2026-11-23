"""
Task T016d: Implement feature exclusion based on VIF report.

Reads data/processed/vif_report.csv, identifies descriptors flagged as True
(VIF > 5), excludes them from the feature matrix in data/processed/descriptors_v1.csv,
and writes the filtered dataset to data/processed/descriptors_vif_filtered.csv.

This script must be run after T016a (VIF calculation) and before T015a (missing value filtering).
"""

import logging
import sys
import os
from pathlib import Path
from typing import List, Set

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VIF_REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "vif_report.csv"
INPUT_DESCRIPTORS_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors_v1.csv"
OUTPUT_FILTERED_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors_vif_filtered.csv"

# Threshold for flagging (must match T016a logic)
VIF_THRESHOLD = 5.0

def load_vif_report(path: Path) -> pd.DataFrame:
    """Load the VIF report CSV."""
    if not path.exists():
        raise FileNotFoundError(f"VIF report not found at {path}. "
                                "Ensure T016a (vif_calculator.py) has completed successfully.")
    logger.info(f"Loading VIF report from {path}")
    df = pd.read_csv(path)
    required_cols = {'descriptor', 'vif_value', 'flagged'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"VIF report missing required columns: {missing}")
    return df

def load_descriptors(path: Path) -> pd.DataFrame:
    """Load the descriptors dataset."""
    if not path.exists():
        raise FileNotFoundError(f"Descriptors file not found at {path}. "
                                "Ensure T014e (finalize_descriptors) has completed successfully.")
    logger.info(f"Loading descriptors from {path}")
    return pd.read_csv(path)

def get_excluded_descriptors(vif_df: pd.DataFrame) -> Set[str]:
    """Extract the set of descriptor names that are flagged."""
    flagged = vif_df[vif_df['flagged'] == True]
    excluded = set(flagged['descriptor'].tolist())
    logger.info(f"Identified {len(excluded)} descriptors to exclude based on VIF > {VIF_THRESHOLD}: {excluded}")
    return excluded

def filter_features(df: pd.DataFrame, excluded: Set[str]) -> pd.DataFrame:
    """Remove excluded descriptor columns from the dataframe."""
    # Identify columns to keep: all columns except those in 'excluded'
    # We must preserve non-feature columns like 'formula', 'T_d', 'total_uncertainty', etc.
    # Strategy: Keep columns that are NOT in the excluded set.
    # Note: We assume 'descriptor' names in VIF report match column names in df exactly.
    
    cols_to_drop = [col for col in excluded if col in df.columns]
    cols_missing = excluded - set(df.columns)
    
    if cols_missing:
        logger.warning(f"Excluded descriptors not found in dataframe (might be target or metadata): {cols_missing}")
    
    if not cols_to_drop:
        logger.warning("No columns to drop. VIF report might be empty or flags are all False.")
    
    df_filtered = df.drop(columns=cols_to_drop, errors='ignore')
    logger.info(f"Dropped columns: {cols_to_drop}")
    return df_filtered

def main():
    """Main entry point for T016d."""
    logger.info("Starting T016d: Feature Exclusion based on VIF Report")
    
    try:
        # 1. Load VIF Report
        vif_df = load_vif_report(VIF_REPORT_PATH)
        
        # 2. Load Descriptors
        df_descriptors = load_descriptors(INPUT_DESCRIPTORS_PATH)
        
        # 3. Identify Excluded Features
        excluded_features = get_excluded_descriptors(vif_df)
        
        # 4. Filter Features
        df_filtered = filter_features(df_descriptors, excluded_features)
        
        # 5. Write Output
        # Ensure output directory exists
        OUTPUT_FILTERED_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        df_filtered.to_csv(OUTPUT_FILTERED_PATH, index=False)
        logger.info(f"Successfully wrote filtered dataset to {OUTPUT_FILTERED_PATH}")
        logger.info(f"Original shape: {df_descriptors.shape}, Filtered shape: {df_filtered.shape}")
        
        # Log column summary
        feature_cols = [c for c in df_filtered.columns if c not in ['formula', 'T_d', 'total_uncertainty', 'perovskite_family', 'instrument_model', 'manufacturer', 'precision_source']]
        logger.info(f"Remaining feature columns: {feature_cols}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T016d execution: {e}")
        raise

if __name__ == "__main__":
    main()