"""
Calculate FID Stability Correlation (T043 + T079).

This script computes the correlation between the predicted latent delta magnitude
and the actual FID stability (relative change in FID between skipped frames and
full-solver frames) for the full set of skipped frames.

It wraps the logic from T043 (FID Stability Correlation) and T079 (Verify FID Stability).
It ensures that the correlation is computed on real data and updates the state.yaml
with the validation status.

Dependencies:
- T050c (Metrics Computation): Provides hybrid output metrics.
- T060 (Ground Truth): Provides full solver output metrics.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = DATA_DIR / "logs"
METRICS_DIR = DATA_DIR / "metrics"
STATE_FILE = PROJECT_ROOT / "state.yaml"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "fid_stability.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_config_summary() -> Dict[str, Any]:
    """Load configuration summary if available."""
    config_path = PROJECT_ROOT / "code" / "config.py"
    # We rely on the existence of the file, but we don't dynamically import
    # to avoid circular dependency issues in this specific script context.
    # Instead, we assume standard paths or read from a JSON config if generated.
    # For now, we return defaults or read from a generated config file if it exists.
    config_json = PROJECT_ROOT / "code" / "config_summary.json"
    if config_json.exists():
        with open(config_json, 'r') as f:
            return json.load(f)
    return {"threshold_delta": 0.5, "min_correlation": 0.7}


def load_hybrid_metrics() -> Optional[pd.DataFrame]:
    """
    Load hybrid output metrics from T050c.
    Expected file: data/processed/hybrid_metrics.parquet or similar.
    Based on T050c description, it computes per-segment latency and FID.
    We assume the output is stored in data/metrics/hybrid_metrics.json or parquet.
    """
    # Attempt to find the file based on common patterns in the project
    possible_paths = [
        DATA_DIR / "metrics" / "hybrid_metrics.parquet",
        DATA_DIR / "metrics" / "hybrid_metrics.json",
        DATA_DIR / "processed" / "hybrid_output.parquet",
    ]

    for path in possible_paths:
        if path.exists():
            logger.info(f"Loading hybrid metrics from {path}")
            if path.suffix == '.parquet':
                return pd.read_parquet(path)
            elif path.suffix == '.json':
                with open(path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return pd.DataFrame(data)
                    return pd.DataFrame([data])
    return None


def load_baseline_metrics() -> Optional[pd.DataFrame]:
    """
    Load baseline (full solver) metrics from T060.
    Expected file: data/metrics/baseline_metrics.parquet or similar.
    """
    possible_paths = [
        DATA_DIR / "metrics" / "baseline_metrics.parquet",
        DATA_DIR / "metrics" / "baseline_metrics.json",
        DATA_DIR / "processed" / "baseline_output.parquet",
    ]

    for path in possible_paths:
        if path.exists():
            logger.info(f"Loading baseline metrics from {path}")
            if path.suffix == '.parquet':
                return pd.read_parquet(path)
            elif path.suffix == '.json':
                with open(path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return pd.DataFrame(data)
                    return pd.DataFrame([data])
    return None


def load_estimator_predictions() -> Optional[pd.DataFrame]:
    """
    Load estimator predictions (latent delta magnitude) from the training/output phase.
    Expected file: data/processed/estimator_predictions.parquet or similar.
    This data comes from the model trained in US2 (T019b) and applied in US3.
    """
    possible_paths = [
        DATA_DIR / "processed" / "estimator_predictions.parquet",
        DATA_DIR / "metrics" / "estimator_predictions.parquet",
        DATA_DIR / "processed" / "sampled_dataset.parquet", # Might contain the predictions if appended
    ]

    for path in possible_paths:
        if path.exists():
            df = pd.read_parquet(path)
            # Check if it has the required column
            if 'latent_delta_magnitude' in df.columns or 'predicted_delta' in df.columns:
                logger.info(f"Loaded estimator predictions from {path}")
                return df
    return None


def calculate_fid_stability(hybrid_df: pd.DataFrame, baseline_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate FID stability for each frame/segment.
    FID Stability = (FID_hybrid - FID_baseline) / FID_baseline
    Filter out frames where either metric is missing or invalid.
    """
    if hybrid_df is None or baseline_df is None:
        raise ValueError("Hybrid or Baseline metrics not found.")

    # Ensure common keys for joining. Assuming 'frame_id' or 'segment_id' exists.
    # If not, we might need to rely on index alignment if they are ordered identically.
    # Let's assume 'frame_id' is the key. If not present, we try to align by index.
    key_col = 'frame_id' if 'frame_id' in hybrid_df.columns else 'segment_id'
    if key_col not in hybrid_df.columns or key_col not in baseline_df.columns:
        # Fallback: try to merge on index if no common ID
        logger.warning("No common ID column found. Attempting index alignment.")
        hybrid_df = hybrid_df.reset_index(drop=True)
        baseline_df = baseline_df.reset_index(drop=True)
        if len(hybrid_df) != len(baseline_df):
            raise ValueError("Hybrid and Baseline datasets have different lengths and no common ID to join.")
        merged = pd.concat([hybrid_df, baseline_df], axis=1)
        merged.columns = [f"hybrid_{c}" if not c.startswith("hybrid_") and not c.startswith("baseline_") else c for c in merged.columns]
        # Rename columns for clarity
        merged = merged.rename(columns={
            'hybrid_fid': 'fid_hybrid',
            'fid_hybrid': 'fid_hybrid', # In case it was already prefixed
            'baseline_fid': 'fid_baseline',
            'fid_baseline': 'fid_baseline'
        })
        # Re-check
        if 'fid_hybrid' not in merged.columns:
            # Try to find columns containing 'fid'
            hybrid_fid = [c for c in hybrid_df.columns if 'fid' in c.lower()]
            baseline_fid = [c for c in baseline_df.columns if 'fid' in c.lower()]
            if hybrid_fid and baseline_fid:
                merged['fid_hybrid'] = hybrid_df[hybrid_fid[0]]
                merged['fid_baseline'] = baseline_df[baseline_fid[0]]
            else:
                raise ValueError("Could not find FID columns in hybrid or baseline data.")
    else:
        merged = pd.merge(hybrid_df, baseline_df, on=key_col, suffixes=('_hybrid', '_baseline'))

    # Calculate stability
    # Filter out rows where FID is 0 or NaN to avoid division by zero
    valid_mask = (merged['fid_baseline'] > 0) & (merged['fid_baseline'].notna()) & (merged['fid_hybrid'].notna())
    merged = merged[valid_mask]

    if len(merged) == 0:
        raise ValueError("No valid frames found for FID stability calculation.")

    merged['fid_stability'] = (merged['fid_hybrid'] - merged['fid_baseline']) / merged['fid_baseline']

    return merged


def update_state_yaml(validation_status: str, correlation_value: float):
    """
    Update state.yaml with the validation status and correlation value.
    Uses the update_state logic from T008.
    """
    import yaml

    if not STATE_FILE.exists():
        state = {"artifact_hashes": {}, "dataset": {"source": "unknown"}, "validation_status": "pending"}
    else:
        with open(STATE_FILE, 'r') as f:
            state = yaml.safe_load(f) or {}

    state['validation_status'] = validation_status
    state['fid_stability_correlation'] = correlation_value

    with open(STATE_FILE, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

    logger.info(f"Updated state.yaml: validation_status={validation_status}, correlation={correlation_value}")


def main():
    logger.info("Starting FID Stability Correlation Calculation (T085)...")

    # 1. Load Data
    hybrid_df = load_hybrid_metrics()
    baseline_df = load_baseline_metrics()
    estimator_df = load_estimator_predictions()

    if hybrid_df is None or baseline_df is None:
        logger.error("Missing required metrics files (Hybrid or Baseline).")
        logger.error("Ensure T060 (Ground Truth) and T050c (Metrics Computation) have run successfully.")
        # Create a placeholder log to indicate failure, but do not fabricate results
        with open(LOGS_DIR / "causal_fid.log", 'a') as f:
            f.write("ERROR: Missing input data for FID stability calculation.\n")
        sys.exit(1)

    if estimator_df is None:
        logger.error("Missing estimator predictions. Ensure the model was trained and predictions generated.")
        sys.exit(1)

    # 2. Calculate FID Stability
    try:
        stability_df = calculate_fid_stability(hybrid_df, baseline_df)
    except ValueError as e:
        logger.error(f"Error calculating FID stability: {e}")
        sys.exit(1)

    # 3. Merge with Estimator Predictions
    # We need to align stability_df with estimator_df.
    # Assuming both have 'frame_id' or can be aligned by index.
    key_col = 'frame_id' if 'frame_id' in stability_df.columns else 'segment_id'
    if key_col in estimator_df.columns:
        final_df = pd.merge(stability_df, estimator_df, on=key_col)
    else:
        # Fallback to index alignment
        if len(stability_df) != len(estimator_df):
            logger.error("Cannot align stability data with estimator predictions: length mismatch and no common ID.")
            sys.exit(1)
        final_df = pd.concat([stability_df.reset_index(drop=True), estimator_df.reset_index(drop=True)], axis=1)

    # 4. Compute Correlation
    # Identify the prediction column
    pred_col = 'latent_delta_magnitude' if 'latent_delta_magnitude' in final_df.columns else \
               'predicted_delta' if 'predicted_delta' in final_df.columns else None

    if pred_col is None:
        logger.error("Could not find prediction column in estimator data.")
        sys.exit(1)

    # Filter out NaNs
    valid_data = final_df[[pred_col, 'fid_stability']].dropna()

    if len(valid_data) < 2:
        logger.error("Insufficient data points to compute correlation.")
        sys.exit(1)

    r, p_value = pearsonr(valid_data[pred_col], valid_data['fid_stability'])

    logger.info(f"Computed Correlation: r={r:.4f}, p-value={p_value:.4f}")

    # 5. Log Results
    log_path = LOGS_DIR / "fid_stability.log"
    with open(log_path, 'a') as f:
        f.write(f"Total frames analyzed: {len(valid_data)}\n")
        f.write(f"Correlation (r): {r:.4f}\n")
        f.write(f"P-value: {p_value:.4f}\n")

    # 6. Determine Validation Status
    # Threshold from T043: r >= 0.7
    threshold = 0.7
    status = 'passed' if r >= threshold else 'failed'

    logger.info(f"Validation Status: {status} (Threshold: {threshold})")

    # 7. Update State
    update_state_yaml(status, r)

    # 8. Write Final Results to JSON
    result = {
        "correlation": r,
        "p_value": p_value,
        "threshold": threshold,
        "status": status,
        "frames_analyzed": len(valid_data)
    }
    result_path = METRICS_DIR / "fid_stability_results.json"
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Results written to {result_path}")

    if status == 'failed':
        logger.warning("FID Stability Correlation did not meet the threshold (r >= 0.7).")
        # Do not exit with error code here, as the calculation was successful,
        # but the result is negative. The project might still continue to log this.
        # However, if strict validation is required, we might exit 1.
        # Based on T043, it just updates state. We will exit 0 to allow the pipeline to continue
        # and report the failure in state.yaml.
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()