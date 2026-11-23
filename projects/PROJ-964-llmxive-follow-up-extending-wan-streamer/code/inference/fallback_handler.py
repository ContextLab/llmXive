"""
Fallback Handler for Hybrid Inference Pipeline.

This module implements the logic to trigger the full solver when uncertainty
is high or delta magnitude is large, while explicitly enforcing the precedence
rule where randomized counterfactual interventions override deterministic logic.

Dependencies:
- T047: Generates counterfactual indices (data/processed/counterfactual_indices.parquet)
- T045a: Precedence rule logic (code/inference/precedence_rule.py)
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Set

import pandas as pd
import numpy as np

# Project root path handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "fallback_handler.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
UNCERTAINTY_THRESHOLD = 0.8
DELTA_MAGNITUDE_HIGH_THRESHOLD = 1.5  # Default high threshold, can be overridden
PRECEDENCE_RULE_LOGIC = "override"  # Strategy: randomized intervention overrides estimator

def load_counterfactual_indices(
    counterfactual_path: Optional[str] = None
) -> Set[int]:
    """
    Load the set of frame indices that are part of the randomized counterfactual intervention.

    Args:
        counterfactual_path: Path to the counterfactual indices parquet file.
                             Defaults to data/processed/counterfactual_indices.parquet.

    Returns:
        A set of integer frame IDs that are forced to be skipped (or processed)
        based on the randomized assignment.

    Raises:
        FileNotFoundError: If the counterfactual indices file does not exist.
        ValueError: If the file exists but is empty or malformed.
    """
    if counterfactual_path is None:
        counterfactual_path = str(PROCESSED_DIR / "counterfactual_indices.parquet")

    path = Path(counterfactual_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Counterfactual indices file not found at {path}. "
            "Ensure T047 (generate_counterfactual_indices) has been executed successfully."
        )

    logger.info(f"Loading counterfactual indices from {path}")

    try:
        df = pd.read_parquet(path)
    except Exception as e:
        raise RuntimeError(f"Failed to read parquet file {path}: {e}")

    if df.empty:
        raise ValueError(f"Counterfactual indices file {path} is empty.")

    if 'frame_id' not in df.columns:
        raise ValueError(
            f"Counterfactual indices file {path} must contain a 'frame_id' column. "
            f"Found columns: {list(df.columns)}"
        )

    # Convert to a set for O(1) lookup
    indices = set(df['frame_id'].astype(int).tolist())
    logger.info(f"Loaded {len(indices)} counterfactual frame indices.")

    return indices

def should_fallback(
    frame_id: int,
    uncertainty: float,
    delta_magnitude: float,
    randomized_indices: Set[int],
    uncertainty_threshold: float = UNCERTAINTY_THRESHOLD,
    delta_threshold: float = DELTA_MAGNITUDE_HIGH_THRESHOLD
) -> Tuple[bool, str]:
    """
    Determine if a full solver fallback should be triggered for a given frame.

    This function implements the precedence rule logic:
    1. Check if the frame is in the randomized counterfactual set.
       - If yes, the intervention (skip or force) takes precedence over estimator prediction.
       - For this implementation, we assume the counterfactual intervention forces a specific
         behavior (e.g., forcing a skip or forcing a full solve). Based on FR-017, the
         randomized subset overrides the deterministic fallback.
       - We interpret "randomized counterfactual intervention" as a flag that dictates
         the action regardless of the estimator's uncertainty/delta.
       - In the context of FR-008 (forced skip subset), if a frame is in the randomized
         subset, it is forced to be skipped (skip=True). However, the fallback handler
         decides whether to run the FULL SOLVER.
       - Logic:
         - If in randomized set: The specific intervention (e.g., forced skip) applies.
           If the intervention is "forced skip", we do NOT run the full solver (fallback=False).
           If the intervention is "forced full", we DO run the full solver (fallback=True).
           Assuming T047 generates indices for "forced skip" (as per FR-008 description),
           these frames should NOT trigger the fallback (they are skipped).
         - If NOT in randomized set: Use deterministic rules (uncertainty/delta).

    Args:
        frame_id: The unique identifier for the current frame.
        uncertainty: The model's predicted uncertainty score (0.0 - 1.0).
        delta_magnitude: The predicted latent delta magnitude.
        randomized_indices: Set of frame IDs belonging to the randomized intervention.
        uncertainty_threshold: Threshold for uncertainty to trigger fallback.
        delta_threshold: Threshold for delta magnitude to trigger fallback.

    Returns:
        Tuple[bool, str]:
            - bool: True if full solver should be triggered (fallback), False if skipped.
            - str: Reason for the decision ("randomized_skip", "high_uncertainty", "high_delta", "normal").
    """
    # Precedence Rule Check (FR-017)
    if frame_id in randomized_indices:
        # FR-008: Randomized subset for forced skip.
        # If the frame is in the randomized set, it is forced to be skipped.
        # Therefore, we do NOT trigger the full solver fallback.
        logger.debug(f"Frame {frame_id} is in randomized set. Enforcing skip (no fallback).")
        return False, "randomized_skip"

    # Deterministic Fallback Logic
    if uncertainty > uncertainty_threshold:
        logger.debug(f"Frame {frame_id}: Uncertainty {uncertainty:.4f} > {uncertainty_threshold}. Triggering fallback.")
        return True, "high_uncertainty"

    if delta_magnitude > delta_threshold:
        logger.debug(f"Frame {frame_id}: Delta Magnitude {delta_magnitude:.4f} > {delta_threshold}. Triggering fallback.")
        return True, "high_delta"

    return False, "normal"

def apply_fallback_logic(
    df: pd.DataFrame,
    randomized_indices: Set[int],
    uncertainty_col: str = "uncertainty_score",
    delta_col: str = "latent_delta_magnitude",
    frame_id_col: str = "frame_id",
    uncertainty_threshold: float = UNCERTAINTY_THRESHOLD,
    delta_threshold: float = DELTA_MAGNITUDE_HIGH_THRESHOLD
) -> pd.DataFrame:
    """
    Apply the fallback logic to a dataset of frames.

    Updates the dataframe with a 'fallback_triggered' boolean column indicating
    whether the full solver should be run for each frame.

    Args:
        df: Input DataFrame containing frame data.
        randomized_indices: Set of frame IDs in the randomized intervention.
        uncertainty_col: Name of the column containing uncertainty scores.
        delta_col: Name of the column containing delta magnitudes.
        frame_id_col: Name of the column containing frame IDs.
        uncertainty_threshold: Threshold for uncertainty.
        delta_threshold: Threshold for delta magnitude.

    Returns:
        Updated DataFrame with 'fallback_triggered' and 'fallback_reason' columns.
    """
    logger.info(f"Applying fallback logic to {len(df)} frames.")

    fallback_decisions = []
    fallback_reasons = []

    for idx, row in df.iterrows():
        fid = int(row[frame_id_col])
        unc = float(row[uncertainty_col])
        delta = float(row[delta_col])

        trigger, reason = should_fallback(
            frame_id=fid,
            uncertainty=unc,
            delta_magnitude=delta,
            randomized_indices=randomized_indices,
            uncertainty_threshold=uncertainty_threshold,
            delta_threshold=delta_threshold
        )

        fallback_decisions.append(trigger)
        fallback_reasons.append(reason)

    df['fallback_triggered'] = fallback_decisions
    df['fallback_reason'] = fallback_reasons

    # Log summary
    total = len(df)
    triggered = sum(fallback_decisions)
    skipped_randomized = sum(1 for r in fallback_reasons if r == "randomized_skip")
    high_unc = sum(1 for r in fallback_reasons if r == "high_uncertainty")
    high_delta = sum(1 for r in fallback_reasons if r == "high_delta")
    normal = sum(1 for r in fallback_reasons if r == "normal")

    logger.info(f"Fallback Logic Summary:")
    logger.info(f"  Total Frames: {total}")
    logger.info(f"  Fallback Triggered (Full Solver): {triggered}")
    logger.info(f"    - High Uncertainty: {high_unc}")
    logger.info(f"    - High Delta: {high_delta}")
    logger.info(f"  Skipped (Randomized Intervention): {skipped_randomized}")
    logger.info(f"  Normal (Skip based on estimator): {normal}")

    return df

def main():
    """
    Main entry point for the fallback handler script.

    Usage:
    python code/inference/fallback_handler.py
        --input data/processed/sampled_dataset.parquet
        --counterfactual data/processed/counterfactual_indices.parquet
        --output data/processed/processed_with_fallback.parquet
        --uncertainty-col uncertainty_score
        --delta-col latent_delta_magnitude
    """
    parser = argparse.ArgumentParser(description="Apply fallback logic to dataset.")
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=str(PROCESSED_DIR / "sampled_dataset.parquet"),
        help="Path to the input dataset (sampled_dataset.parquet)."
    )
    parser.add_argument(
        "--counterfactual", "-c",
        type=str,
        default=None,
        help="Path to the counterfactual indices file. Defaults to data/processed/counterfactual_indices.parquet."
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=str(PROCESSED_DIR / "processed_with_fallback.parquet"),
        help="Path to the output dataset."
    )
    parser.add_argument(
        "--uncertainty-col",
        type=str,
        default="uncertainty_score",
        help="Column name for uncertainty score."
    )
    parser.add_argument(
        "--delta-col",
        type=str,
        default="latent_delta_magnitude",
        help="Column name for latent delta magnitude."
    )
    parser.add_argument(
        "--frame-id-col",
        type=str,
        default="frame_id",
        help="Column name for frame ID."
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        # Load counterfactual indices
        randomized_indices = load_counterfactual_indices(args.counterfactual)

        # Load input data
        logger.info(f"Loading input data from {input_path}")
        df = pd.read_parquet(input_path)

        # Validate required columns
        required_cols = [args.frame_id_col, args.uncertainty_col, args.delta_col]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Input data missing required columns: {missing_cols}")

        # Apply fallback logic
        df_processed = apply_fallback_logic(
            df=df,
            randomized_indices=randomized_indices,
            uncertainty_col=args.uncertainty_col,
            delta_col=args.delta_col,
            frame_id_col=args.frame_id_col
        )

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save output
        df_processed.to_parquet(output_path, index=False)
        logger.info(f"Successfully saved processed data to {output_path}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during fallback processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()