"""
Task T014: Implement Proxy Validation Logic.

Logic:
1. Generate Proxy: If static logs exist, calculate `proxy_utility` for each layer
   (frequency-weighted score) and save to `data/processed/proxy_utility_labels.csv`.
2. Validate: Load `proxy_utility_labels.csv` and `data/processed/ablation_labels_train.json`.
   Join on `trajectory_id` and `layer_name`. Calculate Pearson correlation.
3. Gate: If correlation < 0.7, set `proxy_valid=false` and trigger fallback heuristic path.

Constraint: Validation MUST use the hold-out set of at least 20 trajectories where
ground truth is established via ablation.

Output: `data/processed/proxy_validation_report.json` containing a boolean `proxy_valid`.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy.stats import pearsonr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data/processed")
OUTPUT_FILE = DATA_DIR / "proxy_validation_report.json"
PROXY_FILE = DATA_DIR / "proxy_utility_labels.csv"
ABLATION_FILE = DATA_DIR / "ablation_labels_train.json"
STATIC_LOGS_FILE = DATA_DIR / "simulation_logs_static.json"
CORRELATION_THRESHOLD = 0.7
MIN_HOLDOUT_SIZE = 20


def ensure_directories():
    """Ensure the data/processed directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_static_logs() -> Optional[pd.DataFrame]:
    """
    Load static simulation logs to calculate proxy utility.
    Returns a DataFrame with trajectory_id, layer_name, and frequency/usage metrics.
    """
    if not STATIC_LOGS_FILE.exists():
        logger.warning(f"Static logs not found at {STATIC_LOGS_FILE}. Cannot generate proxy.")
        return None

    try:
        with open(STATIC_LOGS_FILE, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list):
            logger.error("Static logs format invalid: expected a list of trajectory records.")
            return None

        records = []
        for record in data:
            tid = record.get('trajectory_id')
            if not tid:
                continue

            # Extract layers used in this trajectory
            turns = record.get('turns', [])
            for turn in turns:
                layers_used = turn.get('layers_used', [])
                for layer_name in layers_used:
                    records.append({
                        'trajectory_id': tid,
                        'layer_name': layer_name,
                        'used': 1
                    })

        if not records:
            logger.warning("No layer usage records found in static logs.")
            return None

        df = pd.DataFrame(records)
        return df

    except Exception as e:
        logger.error(f"Failed to load static logs: {e}")
        return None


def calculate_proxy_utility(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate proxy utility as frequency-weighted score per layer per trajectory.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    # Group by trajectory and layer to count frequency
    grouped = df.groupby(['trajectory_id', 'layer_name']).size().reset_index(name='frequency')

    # Calculate proxy utility: normalized frequency (or raw frequency if preferred)
    # Here we use raw frequency as the proxy score
    grouped['proxy_utility'] = grouped['frequency']

    return grouped[['trajectory_id', 'layer_name', 'proxy_utility']]


def save_proxy_labels(proxy_df: pd.DataFrame):
    """Save the calculated proxy utility labels to CSV."""
    if proxy_df.empty:
        logger.warning("Proxy DataFrame is empty. Saving empty CSV.")
        proxy_df.to_csv(PROXY_FILE, index=False)
        return

    proxy_df.to_csv(PROXY_FILE, index=False)
    logger.info(f"Saved proxy utility labels to {PROXY_FILE}")


def load_ablation_labels() -> Optional[pd.DataFrame]:
    """
    Load ablation labels (ground truth) from JSON.
    Expected format: list of dicts with trajectory_id, layer_name, utility_delta.
    """
    if not ABLATION_FILE.exists():
        logger.error(f"Ablation labels not found at {ABLATION_FILE}.")
        return None

    try:
        with open(ABLATION_FILE, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list):
            logger.error("Ablation labels format invalid: expected a list.")
            return None

        # Normalize to DataFrame
        records = []
        for record in data:
            tid = record.get('trajectory_id')
            layer = record.get('layer_name')
            utility = record.get('utility_delta')

            if tid and layer and utility is not None:
                records.append({
                    'trajectory_id': tid,
                    'layer_name': layer,
                    'ablation_utility': float(utility)
                })

        if not records:
            logger.error("No valid records found in ablation labels.")
            return None

        return pd.DataFrame(records)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ablation labels JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading ablation labels: {e}")
        return None


def validate_proxy_correlation(proxy_df: pd.DataFrame, ablation_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Join proxy and ablation data on trajectory_id and layer_name.
    Calculate Pearson correlation.
    Return validation report dict.
    """
    if proxy_df.empty or ablation_df.empty:
        logger.warning("One or both input DataFrames are empty. Cannot compute correlation.")
        return {
            'proxy_valid': False,
            'reason': 'Input data empty',
            'correlation': None,
            'sample_size': 0
        }

    # Merge on trajectory_id and layer_name
    merged = pd.merge(
        proxy_df,
        ablation_df,
        on=['trajectory_id', 'layer_name'],
        how='inner'
    )

    if len(merged) < MIN_HOLDOUT_SIZE:
        logger.warning(f"Sample size ({len(merged)}) is less than required holdout ({MIN_HOLDOUT_SIZE}).")
        # We still compute correlation but flag the small sample size
        report = {
            'proxy_valid': False,
            'reason': f'Sample size too small ({len(merged)} < {MIN_HOLDOUT_SIZE})',
            'correlation': None,
            'sample_size': len(merged)
        }
        return report

    if len(merged) < 2:
        logger.error("Insufficient data points for correlation calculation.")
        return {
            'proxy_valid': False,
            'reason': 'Insufficient data points for correlation',
            'correlation': None,
            'sample_size': len(merged)
        }

    # Calculate Pearson correlation
    try:
        corr, p_value = pearsonr(merged['proxy_utility'], merged['ablation_utility'])

        # Handle NaN or Inf
        if np.isnan(corr) or np.isinf(corr):
            logger.warning("Correlation calculation resulted in NaN or Inf.")
            corr_val = None
            is_valid = False
        else:
            corr_val = float(corr)
            is_valid = corr_val >= CORRELATION_THRESHOLD

        report = {
            'proxy_valid': is_valid,
            'correlation': corr_val,
            'p_value': float(p_value),
            'sample_size': len(merged),
            'threshold': CORRELATION_THRESHOLD,
            'reason': 'Correlation meets threshold' if is_valid else f'Correlation {corr_val:.4f} below threshold {CORRELATION_THRESHOLD}'
        }

    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        return {
            'proxy_valid': False,
            'reason': f'Correlation calculation failed: {str(e)}',
            'correlation': None,
            'sample_size': len(merged)
        }

    return report


def save_report(report: Dict[str, Any]):
    """Save the validation report to JSON."""
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Saved validation report to {OUTPUT_FILE}")


def main():
    """Main entry point for Task T014."""
    logger.info("Starting Proxy Validation Logic (T014).")
    ensure_directories()

    # Step 1: Generate Proxy
    static_logs = load_static_logs()
    proxy_df = calculate_proxy_utility(static_logs)
    save_proxy_labels(proxy_df)

    # Step 2: Load Ground Truth (Ablation Labels)
    ablation_df = load_ablation_labels()
    if ablation_df is None:
        logger.error("Ablation labels missing. Validation cannot proceed.")
        report = {
            'proxy_valid': False,
            'reason': 'Ablation labels missing',
            'correlation': None,
            'sample_size': 0
        }
        save_report(report)
        return

    # Step 3: Validate Correlation
    report = validate_proxy_correlation(proxy_df, ablation_df)
    save_report(report)

    logger.info("Proxy Validation Logic (T014) completed.")


if __name__ == "__main__":
    main()
