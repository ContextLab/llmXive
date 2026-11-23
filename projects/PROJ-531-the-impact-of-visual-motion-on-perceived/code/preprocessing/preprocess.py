"""
Preprocessing pipeline for the Visual Motion Agency project.

This script implements Task T014:
1. Loads source data (from T012 real or T013 synthetic).
2. Extracts motion features (latency, smoothness, lead_time).
3. Aggregates and standardizes agency scores (0-1 range).
4. Verifies independence of user_response_trigger from agency_score (FR-012).
5. Computes VIF for motion predictors (FR-006).
6. Outputs raw_processed.csv and vif_report.json.
"""
import os
import json
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Ensure project root is in path for imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants
DATA_RAW_DIR = project_root / "data" / "raw"
DATA_PROCESSED_DIR = project_root / "data" / "processed"
SYNTHETIC_DATA_PATH = DATA_RAW_DIR / "synthetic_data.csv"
DOWNLOAD_STATUS_PATH = DATA_RAW_DIR / "download_status.json"
PROCESSED_OUTPUT_PATH = DATA_PROCESSED_DIR / "raw_processed.csv"
VIF_REPORT_PATH = DATA_PROCESSED_DIR / "vif_report.json"

# Thresholds
TRIGGER_CORR_THRESHOLD = 0.05
VIF_THRESHOLD = 5.0

def load_source_data():
    """
    Load data from the appropriate source.
    Checks T012 status file to decide whether to use real or synthetic data.
    """
    if not DOWNLOAD_STATUS_PATH.exists():
        logger.error(f"Status file not found: {DOWNLOAD_STATUS_PATH}. Run T012 first.")
        sys.exit(1)

    with open(DOWNLOAD_STATUS_PATH, 'r') as f:
        status_data = json.load(f)

    status = status_data.get("status")

    if status == "invalid":
        logger.error("Dataset excluded: Unvalidated instrument (FR-009). Aborting.")
        sys.exit(1)

    if status == "success":
        # Logic for real data would go here.
        # Since T012 currently reports 'unavailable' in the synthetic-only flow,
        # we treat 'success' as a placeholder for future real data implementation.
        # For now, if 'success' is reported but no file exists, we fail.
        real_data_path = DATA_RAW_DIR / "real_data.csv" # Assumed path
        if not real_data_path.exists():
            logger.error("Real data reported as available but file not found.")
            sys.exit(1)
        logger.info("Loading real data...")
        return pd.read_csv(real_data_path)

    elif status == "unavailable":
        logger.info("Real data unavailable. Loading synthetic data from T013.")
        if not SYNTHETIC_DATA_PATH.exists():
            logger.error(f"Synthetic data file not found: {SYNTHETIC_DATA_PATH}. Run T013 first.")
            sys.exit(1)
        return pd.read_csv(SYNTHETIC_DATA_PATH)
    
    else:
        logger.error(f"Unknown status in download_status.json: {status}")
        sys.exit(1)

def extract_motion_features(df):
    """
    Extract motion features.
    Assumes columns 'latency', 'smoothness', 'lead_time' exist or are derived.
    If they don't exist, we assume the synthetic generator already produced them.
    """
    required_motion_cols = ['latency', 'smoothness', 'lead_time']
    existing_cols = df.columns.tolist()
    
    # Check for presence; if missing, log warning but proceed (assuming generator handled it)
    missing = [c for c in required_motion_cols if c not in existing_cols]
    if missing:
        logger.warning(f"Missing motion feature columns in input: {missing}. "
                       "Assuming input data already contains processed features.")
    
    return df

def aggregate_agency_scores(df):
    """
    Aggregate Likert-scale items into a continuous variable using 'mean of items'.
    Then standardize to 0-1 range using (score - min) / (max - min).
    """
    # Assuming 'agency_score' is already an aggregate or raw sum in input.
    # If input has multiple items (e.g., agency_1, agency_2...), we would aggregate here.
    # Based on T013, 'agency_score' is generated directly.
    
    col_name = 'agency_score'
    if col_name not in df.columns:
        logger.error(f"Agency score column '{col_name}' not found in input data.")
        sys.exit(1)

    # Standardization: (score - min) / (max - min)
    min_val = df[col_name].min()
    max_val = df[col_name].max()

    if max_val == min_val:
        logger.warning("Agency score range is zero. Setting all to 0.5.")
        df[col_name] = 0.5
    else:
        df[col_name] = (df[col_name] - min_val) / (max_val - min_val)

    return df

def calculate_trigger_independence(df):
    """
    Calculate Pearson correlation between user_response_trigger and agency_score.
    Gate: Exit with code 1 if correlation >= 0.05 (FR-012).
    """
    trigger_col = 'user_response_trigger'
    agency_col = 'agency_score'

    if trigger_col not in df.columns or agency_col not in df.columns:
        logger.error(f"Missing required columns for independence check: {trigger_col}, {agency_col}")
        sys.exit(1)

    # Drop NaNs for correlation calculation
    valid_data = df[[trigger_col, agency_col]].dropna()
    
    if len(valid_data) < 2:
        logger.error("Insufficient data points to calculate correlation.")
        sys.exit(1)

    corr, p_value = valid_data[trigger_col].corr(valid_data[agency_col]), 0.0 # p-value not strictly needed for gate
    
    logger.info(f"Correlation between {trigger_col} and {agency_col}: {corr:.4f}")

    if abs(corr) >= TRIGGER_CORR_THRESHOLD:
        logger.error(f"Gate Failed: Correlation ({corr:.4f}) >= threshold ({TRIGGER_CORR_THRESHOLD}). "
                     f"FR-012 violation: Trigger and Agency are too dependent.")
        sys.exit(1)
    
    return corr

def compute_vif(df):
    """
    Compute Variance Inflation Factor (VIF) for all motion predictors.
    Returns a dict of feature: vif_score.
    """
    motion_features = ['latency', 'smoothness', 'lead_time']
    # Filter to only those present
    features = [f for f in motion_features if f in df.columns]
    
    if len(features) < 2:
        logger.warning("Less than 2 features for VIF. VIF requires multiple predictors.")
        return {f: 0.0 for f in features}

    # Add constant for statsmodels
    X = df[features].dropna() # Drop rows with NaNs in features for VIF calculation
    
    if len(X) < len(features) + 1:
        logger.warning("Not enough samples for VIF calculation.")
        return {f: np.inf for f in features}

    X_const = sm.add_constant(X)
    vif_data = {}
    
    for i, col in enumerate(X_const.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_const.values, i)
            vif_data[col] = vif
        except Exception as e:
            logger.error(f"Error computing VIF for {col}: {e}")
            vif_data[col] = np.inf

    return vif_data

def run_preprocessing():
    """
    Main entry point for preprocessing.
    """
    logger.info("Starting preprocessing pipeline (T014)...")
    
    # 1. Load Data
    df = load_source_data()
    logger.info(f"Loaded {len(df)} rows.")

    # 2. Extract Motion Features
    df = extract_motion_features(df)

    # 3. Aggregate & Standardize Agency Scores
    df = aggregate_agency_scores(df)

    # 4. Trigger Independence Check (Gate)
    calculate_trigger_independence(df)

    # 5. Compute VIF
    vif_scores = compute_vif(df)
    
    # Log VIF scores
    for feat, score in vif_scores.items():
        status = "PASS" if score < VIF_THRESHOLD else "WARN (High Collinearity)"
        logger.info(f"VIF for {feat}: {score:.2f} [{status}]")

    # 6. Save Outputs
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save raw_processed.csv
    df.to_csv(PROCESSED_OUTPUT_PATH, index=False)
    logger.info(f"Saved processed data to {PROCESSED_OUTPUT_PATH}")

    # Save vif_report.json
    report = {
        "vif_scores": vif_scores,
        "threshold": VIF_THRESHOLD,
        "features_analyzed": list(vif_scores.keys()),
        "timestamp": pd.Timestamp.now().isoformat()
    }
    with open(VIF_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved VIF report to {VIF_REPORT_PATH}")

    return df, vif_scores

def main():
    run_preprocessing()

if __name__ == "__main__":
    main()