"""
Extrapolation Flagging Module

Implements logic to detect predictions outside plausible reduction ranges
and apply confidence penalties as per FR-009.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union

import numpy as np
import pandas as pd

# Import project configuration
from config import get_reductions, ConfigurationError
from utils.logging import get_logger

logger = get_logger(__name__)


# Define plausible reduction range boundaries based on physical constraints
# Cold rolling reductions typically range from 0% to ~95%
# We define a "safe" training range and an "extrapolation" warning range
MIN_PLAUSIBLE_REDUCTION = 0.0
MAX_PLAUSIBLE_REDUCTION = 95.0  # Hard physical limit (100% would be zero thickness)

# Warning threshold: if prediction is within this margin of the boundary, flag as "near-boundary"
NEAR_BOUNDARY_MARGIN = 5.0  # percent

# Confidence penalty multiplier for extrapolation
# If prediction is outside plausible range, confidence is multiplied by this factor
EXTRAPOLATION_PENALTY_FACTOR = 0.5

# Confidence penalty multiplier for near-boundary predictions
NEAR_BOUNDARY_PENALTY_FACTOR = 0.8


def is_extrapolation(
    reduction: float,
    min_valid: Optional[float] = None,
    max_valid: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Determine if a given reduction value represents an extrapolation.

    Args:
        reduction: The reduction percentage to check.
        min_valid: Optional override for minimum valid reduction.
        max_valid: Optional override for maximum valid reduction.

    Returns:
        Tuple of (is_extrapolation: bool, reason: str)
    """
    if min_valid is None:
        min_valid = MIN_PLAUSIBLE_REDUCTION
    if max_valid is None:
        max_valid = MAX_PLAUSIBLE_REDUCTION

    if reduction < min_valid:
        return True, f"Reduction {reduction}% is below minimum plausible value ({min_valid}%)"
    if reduction > max_valid:
        return True, f"Reduction {reduction}% is above maximum plausible value ({max_valid}%)"

    # Check near-boundary conditions
    if abs(reduction - min_valid) < NEAR_BOUNDARY_MARGIN:
        return False, f"Reduction {reduction}% is near lower boundary (within {NEAR_BOUNDARY_MARGIN}%)"
    if abs(reduction - max_valid) < NEAR_BOUNDARY_MARGIN:
        return False, f"Reduction {reduction}% is near upper boundary (within {NEAR_BOUNDARY_MARGIN}%)"

    return False, "Reduction is within safe interpolation range"


def apply_confidence_penalty(
    confidence: float,
    reduction: float,
    min_valid: Optional[float] = None,
    max_valid: Optional[float] = None
) -> Tuple[float, str, bool]:
    """
    Apply confidence penalty based on extrapolation status.

    Args:
        confidence: Original confidence score (0.0 to 1.0).
        reduction: The reduction percentage for the prediction.
        min_valid: Optional override for minimum valid reduction.
        max_valid: Optional override for maximum valid reduction.

    Returns:
        Tuple of (adjusted_confidence: float, penalty_reason: str, is_extrapolated: bool)
    """
    is_extr, reason = is_extrapolation(reduction, min_valid, max_valid)

    if is_extr:
        adjusted = confidence * EXTRAPOLATION_PENALTY_FACTOR
        return adjusted, f"Extrapolation penalty applied: {reason}", True

    # Check for near-boundary (not extrapolation, but lower confidence)
    if abs(reduction - (min_valid or MIN_PLAUSIBLE_REDUCTION)) < NEAR_BOUNDARY_MARGIN:
        adjusted = confidence * NEAR_BOUNDARY_PENALTY_FACTOR
        return adjusted, f"Near-boundary penalty applied: {reason}", False

    if abs(reduction - (max_valid or MAX_PLAUSIBLE_REDUCTION)) < NEAR_BOUNDARY_MARGIN:
        adjusted = confidence * NEAR_BOUNDARY_PENALTY_FACTOR
        return adjusted, f"Near-boundary penalty applied: {reason}", False

    return confidence, "No penalty applied (safe interpolation range)", False


def flag_predictions(
    predictions_df: pd.DataFrame,
    reduction_col: str = 'reduction',
    confidence_col: str = 'confidence',
    output_col: str = 'adjusted_confidence',
    flags_col: str = 'extrapolation_flags'
) -> pd.DataFrame:
    """
    Process a DataFrame of predictions to flag extrapolations and adjust confidence.

    Args:
        predictions_df: DataFrame containing predictions with reduction and confidence.
        reduction_col: Column name for reduction values.
        confidence_col: Column name for confidence scores.
        output_col: Column name for adjusted confidence output.
        flags_col: Column name for flag details output.

    Returns:
        DataFrame with added columns for adjusted confidence and flags.
    """
    if reduction_col not in predictions_df.columns:
        raise ValueError(f"Column '{reduction_col}' not found in predictions DataFrame")
    if confidence_col not in predictions_df.columns:
        raise ValueError(f"Column '{confidence_col}' not found in predictions DataFrame")

    results = []
    flags = []

    for idx, row in predictions_df.iterrows():
        reduction = float(row[reduction_col])
        confidence = float(row[confidence_col])

        adj_conf, flag_reason, is_ext = apply_confidence_penalty(
            confidence, reduction
        )

        results.append(adj_conf)
        flags.append({
            'is_extrapolation': is_ext,
            'reason': flag_reason,
            'original_confidence': confidence,
            'adjusted_confidence': adj_conf
        })

    predictions_df = predictions_df.copy()
    predictions_df[output_col] = results
    predictions_df[flags_col] = flags

    # Log summary
    extrapolated_count = sum(1 for f in flags if f['is_extrapolation'])
    if extrapolated_count > 0:
        logger.warning(f"Found {extrapolated_count} extrapolated predictions out of {len(flags)} total.")
    else:
        logger.info("All predictions are within safe interpolation range.")

    return predictions_df


def run_extrapolation_check(
    predictions_path: str,
    output_path: str
) -> None:
    """
    Main entry point to run extrapolation flagging on a predictions file.

    Args:
        predictions_path: Path to input predictions CSV/Parquet.
        output_path: Path to write flagged results.
    """
    logger.info(f"Loading predictions from {predictions_path}")

    if not os.path.exists(predictions_path):
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")

    # Load data
    if predictions_path.endswith('.parquet'):
        df = pd.read_parquet(predictions_path)
    else:
        df = pd.read_csv(predictions_path)

    # Ensure required columns exist
    required_cols = ['reduction', 'confidence']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in predictions: {missing}")

    # Process
    flagged_df = flag_predictions(df)

    # Save
    logger.info(f"Writing flagged results to {output_path}")
    if output_path.endswith('.parquet'):
        flagged_df.to_parquet(output_path, index=False)
    else:
        flagged_df.to_csv(output_path, index=False)

    logger.info("Extrapolation check complete.")


def main():
    """Command line entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run extrapolation flagging on predictions.")
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to input predictions file (CSV or Parquet)'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Path to output flagged results file'
    )

    args = parser.parse_args()

    try:
        run_extrapolation_check(args.input, args.output)
    except Exception as e:
        logger.error(f"Extrapolation check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
