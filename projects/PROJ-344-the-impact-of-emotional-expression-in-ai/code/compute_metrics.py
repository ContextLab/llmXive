"""
T015: Implement intra-modal consistency metric calculation.

Computes the max absolute cross-correlation within ±2s lag, normalized by
the product of standard deviations (FR-004).

Inputs:
  - data/processed/clean_features.csv (from T015_merge) OR
  - data/processed/synthetic_features.csv (from T012_gen)

Output:
  - data/processed/metrics.csv with columns:
    interaction_id (str), consistency_score (float), trust_score (int)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import logging config from sibling module
from logging_config import get_logger, log_pipeline_start, log_pipeline_complete, log_pipeline_error

logger = get_logger(__name__)

# Constants
LAG_SECONDS = 2.0
SAMPLE_RATE_HZ = 15.0  # Assumed from synthetic media spec (15fps)
MAX_LAG_SAMPLES = int(LAG_SECONDS * SAMPLE_RATE_HZ)


def validate_feature_input(df: pd.DataFrame) -> None:
    """Validate that the input dataframe has the required columns."""
    required_cols = ['interaction_id', 'facial_landmarks_json', 'vocal_prosody_json', 'trust_score']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Input dataframe missing required columns: {missing}")


def parse_json_series(series: pd.Series) -> List[List[Dict[str, Any]]]:
    """
    Parse the JSON string column into a list of dicts for each row.
    Returns a list of lists, where each inner list is the time-series for one interaction.
    """
    parsed = []
    for val in series:
        if pd.isna(val):
            parsed.append([])
        else:
            try:
                parsed.append(json.loads(val))
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON: {val}")
                parsed.append([])
    return parsed


def compute_max_abs_cross_correlation(
    facial_ts: List[Dict[str, Any]],
    vocal_ts: List[Dict[str, Any]],
    max_lag: int = MAX_LAG_SAMPLES
) -> float:
    """
    Compute the max absolute cross-correlation between two time-series,
    normalized by the product of their standard deviations.

    We extract a scalar signal from the JSON objects (e.g., average landmark distance
    for facial, pitch mean for vocal) to perform the correlation.

    FR-004: max abs cross-correlation within ±2s lag, normalized by product of std devs.
    """
    if not facial_ts or not vocal_ts:
        return 0.0

    # Extract scalar signals
    # Facial: Use average distance from face center (approximate using landmarks if present)
    # If landmarks are dicts with 'x', 'y', compute centroid distance or just use a proxy
    # For robustness, we'll try to find a numeric value. If the JSON structure is complex,
    # we'll fall back to a simple heuristic or 0.
    def extract_signal(ts: List[Dict]) -> np.ndarray:
        vals = []
        for item in ts:
            if isinstance(item, dict):
                # Try to find a 'value' or 'score' or compute a simple metric
                if 'value' in item:
                    vals.append(float(item['value']))
                elif 'score' in item:
                    vals.append(float(item['score']))
                elif 'x' in item and 'y' in item:
                    # Simple proxy: distance from origin or mean of coords
                    vals.append((float(item.get('x', 0)) + float(item.get('y', 0))) / 2.0)
                else:
                    # Fallback: try to find any float value
                    float_vals = [v for v in item.values() if isinstance(v, (int, float))]
                    if float_vals:
                        vals.append(np.mean(float_vals))
                    else:
                        vals.append(0.0)
            else:
                vals.append(float(item) if isinstance(item, (int, float)) else 0.0)
        return np.array(vals, dtype=float)

    signal_f = extract_signal(facial_ts)
    signal_v = extract_signal(vocal_ts)

    # Ensure same length by truncating to the shortest
    min_len = min(len(signal_f), len(signal_v))
    if min_len == 0:
        return 0.0

    signal_f = signal_f[:min_len]
    signal_v = signal_v[:min_len]

    std_f = np.std(signal_f)
    std_v = np.std(signal_v)

    if std_f < 1e-9 or std_v < 1e-9:
        return 0.0

    # Normalize
    signal_f_norm = (signal_f - np.mean(signal_f)) / std_f
    signal_v_norm = (signal_v - np.mean(signal_v)) / std_v

    # Compute cross-correlation for lags in [-max_lag, max_lag]
    max_corr = 0.0
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            f_slice = signal_f_norm[-lag:]
            v_slice = signal_v_norm[:lag]
        elif lag > 0:
            f_slice = signal_f_norm[:-lag]
            v_slice = signal_v_norm[lag:]
        else:
            f_slice = signal_f_norm
            v_slice = signal_v_norm

        if len(f_slice) == 0:
            continue

        corr = np.mean(f_slice * v_slice)
        if abs(corr) > max_corr:
            max_corr = abs(corr)

    return float(max_corr)


def compute_consistency_score(
    facial_ts: List[Dict[str, Any]],
    vocal_ts: List[Dict[str, Any]]
) -> float:
    """Wrapper to compute consistency score for a single interaction."""
    return compute_max_abs_cross_correlation(facial_ts, vocal_ts)


def process_interaction_features(row: pd.Series) -> Tuple[str, float, int]:
    """
    Process a single row of features to compute the consistency score.
    Returns (interaction_id, consistency_score, trust_score).
    """
    try:
        facial_ts = json.loads(row['facial_landmarks_json']) if isinstance(row['facial_landmarks_json'], str) else row['facial_landmarks_json']
        vocal_ts = json.loads(row['vocal_prosody_json']) if isinstance(row['vocal_prosody_json'], str) else row['vocal_prosody_json']

        score = compute_consistency_score(facial_ts, vocal_ts)
        return (row['interaction_id'], score, int(row['trust_score']))
    except Exception as e:
        logger.error(f"Error processing interaction {row.get('interaction_id', 'unknown')}: {e}")
        return (row['interaction_id'], 0.0, int(row['trust_score']))


def main():
    log_pipeline_start("T015_compute_metrics")

    # Determine input file
    synthetic_path = "data/processed/synthetic_features.csv"
    clean_path = "data/processed/clean_features.csv"
    output_path = "data/processed/metrics.csv"

    input_path = None
    is_validation_only = False

    if os.path.exists(synthetic_path):
        input_path = synthetic_path
        is_validation_only = True
        logger.info("Using synthetic features (VALIDATION_ONLY mode).")
    elif os.path.exists(clean_path):
        input_path = clean_path
        logger.info("Using clean features (PRIMARY study mode).")
    else:
        logger.error("Input file not found: data/processed/clean_features.csv or data/processed/synthetic_features.csv")
        logger.error("Please ensure T015_merge (or T012_gen) has completed successfully.")
        log_pipeline_error("Input file missing")
        sys.exit(1)

    # Load data
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load input file {input_path}: {e}")
        log_pipeline_error(f"Load error: {e}")
        sys.exit(1)

    # Validate
    try:
        validate_feature_input(df)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        log_pipeline_error(f"Validation error: {e}")
        sys.exit(1)

    # Process
    logger.info(f"Processing {len(df)} interactions...")
    results = []
    for _, row in df.iterrows():
        res = process_interaction_features(row)
        results.append(res)

    # Create output dataframe
    out_df = pd.DataFrame(results, columns=['interaction_id', 'consistency_score', 'trust_score'])

    # Add metadata column if synthetic
    if is_validation_only:
        out_df['mode'] = 'VALIDATION_ONLY'
    else:
        out_df['mode'] = 'PRIMARY'

    # Write output
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        out_df.to_csv(output_path, index=False)
        logger.info(f"Metrics written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        log_pipeline_error(f"Write error: {e}")
        sys.exit(1)

    log_pipeline_complete("T015_compute_metrics")


if __name__ == "__main__":
    main()