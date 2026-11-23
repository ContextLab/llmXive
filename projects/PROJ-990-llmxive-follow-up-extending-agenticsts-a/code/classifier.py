import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union

import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# Import config for constants
from config import load_config_from_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_utility_labels(path: str) -> pd.DataFrame:
    """Load ablation utility labels."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Utility labels file not found: {path}")
    
    # Try JSON first (from T008)
    if p.suffix == '.json':
        with open(p, 'r') as f:
            data = json.load(f)
        # Normalize to DataFrame if it's a list of dicts
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            # Assume it's a dict with a 'labels' key or similar
            if 'labels' in data:
                df = pd.DataFrame(data['labels'])
            else:
                df = pd.DataFrame([data])
        return df
    elif p.suffix == '.csv':
        return pd.read_csv(p)
    else:
        raise ValueError(f"Unsupported file format: {p.suffix}")

def load_holdout_set(path: str) -> pd.DataFrame:
    """Load the validation set split from T014a."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Holdout set file not found: {path}")
    return pd.read_csv(p)

def load_static_logs(path: str) -> pd.DataFrame:
    """Load static log proxy data. 
    Note: In the absence of a specific pre-computed static log file, 
    we derive the proxy from the metrics_with_moves.csv which contains 
    the raw static features (entropy, legal moves) used as the proxy 
    for the ablation utility.
    """
    p = Path(path)
    if not p.exists():
        # Fallback to the standard metrics file if the specific proxy file is missing
        fallback = Path("data/processed/metrics_with_moves.csv")
        if fallback.exists():
            logger.warning(f"Static logs not found at {path}, using {fallback}")
            return pd.read_csv(fallback)
        raise FileNotFoundError(f"Static logs file not found: {path} (and fallback missing)")
    return pd.read_csv(p)

def prepare_features(
    holdout_df: pd.DataFrame, 
    utility_df: pd.DataFrame, 
    proxy_col: str = 'entropy', 
    target_col: str = 'utility_score'
) -> Tuple[pd.Series, pd.Series]:
    """
    Prepare aligned feature (proxy) and target (ablation utility) series.
    Merges on trajectory_id and turn if necessary, or assumes row alignment.
    """
    # Ensure we have the target column
    if target_col not in utility_df.columns:
        # Try to find a similar column
        possible_cols = [c for c in utility_df.columns if 'utility' in c.lower() or 'score' in c.lower()]
        if possible_cols:
            target_col = possible_cols[0]
            logger.info(f"Using found column '{target_col}' as target.")
        else:
            raise ValueError(f"Target column '{target_col}' not found in utility labels. Available: {utility_df.columns.tolist()}")

    # Merge on common keys (trajectory_id, turn) if they exist
    common_keys = ['trajectory_id', 'turn']
    if all(k in holdout_df.columns and k in utility_df.columns for k in common_keys):
        merged = pd.merge(holdout_df, utility_df, on=common_keys, how='inner')
    elif 'trajectory_id' in holdout_df.columns and 'trajectory_id' in utility_df.columns:
        # Merge on trajectory_id only if turn is missing
        merged = pd.merge(holdout_df, utility_df, on='trajectory_id', how='inner')
    else:
        # Assume row alignment if no keys
        merged = pd.concat([holdout_df, utility_df], axis=1)

    if merged.empty:
        raise ValueError("Merged dataset is empty. Check keys or column alignment.")

    if proxy_col not in merged.columns:
        raise ValueError(f"Proxy column '{proxy_col}' not found in merged data. Available: {merged.columns.tolist()}")

    # Drop rows with NaN in proxy or target
    valid = merged[[proxy_col, target_col]].dropna()

    if len(valid) < 2:
        raise ValueError(f"Insufficient valid data points for correlation (n={len(valid)}).")

    return valid[proxy_col], valid[target_col]

def validate_proxy_correlation(proxy: pd.Series, target: pd.Series, threshold: float = 0.1) -> Tuple[float, bool]:
    """
    Calculate Pearson correlation between static log proxy and ablation utility.
    Returns (correlation_coefficient, is_valid).
    """
    if len(proxy) != len(target):
        raise ValueError("Proxy and target series must be of equal length.")

    r, p_value = pearsonr(proxy, target)
    is_valid = abs(r) > threshold
    
    logger.info(f"Pearson Correlation: {r:.4f} (p-value: {p_value:.4e})")
    logger.info(f"Proxy Validity (|r| > {threshold}): {is_valid}")
    
    return r, is_valid

def save_report(report_data: Dict[str, Any], output_path: str) -> None:
    """Save the validation report to JSON."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w') as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Report saved to {output_path}")

def run_training() -> None:
    """Placeholder for T009 training logic if needed here, but T009 is separate."""
    pass

def load_model(path: str) -> Any:
    """Load a trained model if needed."""
    p = Path(path)
    if not p.exists():
        return None
    with open(p, 'rb') as f:
        return pickle.load(f)

def main():
    """
    Main entry point for T014: Proxy Validation Logic.
    1. Load validation set (from T014a).
    2. Load ablation utility labels (from T008).
    3. Load static log proxy data.
    4. Align and validate correlation.
    5. Write proxy_validation_report.json.
    """
    config = load_config_from_file()
    
    # Paths
    holdout_path = config.get('paths', {}).get('validation_set', 'data/processed/validation_set.csv')
    utility_path = config.get('paths', {}).get('ablation_labels_train', 'data/processed/ablation_labels_train.json')
    # If a specific static log file isn't defined, we use the metrics file which holds the proxy features
    proxy_path = config.get('paths', {}).get('metrics_with_moves', 'data/processed/metrics_with_moves.csv')
    output_path = config.get('paths', {}).get('proxy_validation_report', 'data/processed/proxy_validation_report.json')
    
    # Threshold for validity (configurable, default 0.1)
    threshold = config.get('hyperparameters', {}).get('proxy_correlation_threshold', 0.1)

    logger.info("Starting Proxy Validation (T014)...")

    try:
        # Load Data
        logger.info(f"Loading holdout set from {holdout_path}")
        holdout_df = load_holdout_set(holdout_path)
        
        logger.info(f"Loading utility labels from {utility_path}")
        utility_df = load_utility_labels(utility_path)
        
        logger.info(f"Loading static proxy from {proxy_path}")
        proxy_df = load_static_logs(proxy_path)

        # Prepare Features
        logger.info("Aligning proxy and utility data...")
        proxy_series, target_series = prepare_features(
            holdout_df, 
            utility_df, 
            proxy_col='entropy', # Default proxy column
            target_col='utility_score' # Default target column
        )

        # Validate Correlation
        r, is_valid = validate_proxy_correlation(proxy_series, target_series, threshold=threshold)

        # Construct Report
        report = {
            "task_id": "T014",
            "status": "completed",
            "proxy_valid": is_valid,
            "correlation_coefficient": float(r),
            "sample_size": int(len(proxy_series)),
            "threshold": threshold,
            "message": "Proxy validation successful" if is_valid else "Proxy correlation below threshold"
        }

        # Save Report
        save_report(report, output_path)
        logger.info("T014 completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        # Fail loudly as per constraints
        raise
    except Exception as e:
        logger.error(f"Error during proxy validation: {e}")
        raise

if __name__ == "__main__":
    main()