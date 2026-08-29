import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any, Union
import pandas as pd
import numpy as np

from utils.config import (
    get_seroconversion_threshold,
    get_hai_threshold,
    get_use_synthetic_data,
    get_raw_path,
    get_processed_path,
    get_output_path,
)
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the preprocessed dataset (data_clr.csv) containing normalized,
    CLR-transformed taxa and titer information.
    """
    processed_path = get_processed_path()
    input_file = processed_path / "data_clr.csv"

    if not input_file.exists():
        msg = f"Processed data file not found: {input_file}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    logger.info(f"Loading processed data from {input_file}")
    df = pd.read_csv(input_file)

    required_cols = ["subject_id", "titer_baseline", "titer_post"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        msg = f"Missing required columns in processed data: {missing}"
        logger.error(msg)
        raise ValueError(msg)

    return df

def calculate_seroconversion_status(
    df: pd.DataFrame, threshold: Optional[float] = None
) -> pd.Series:
    """
    Calculate seroconversion status for each subject.

    Seroconversion is defined as:
        post_titer >= threshold * baseline_titer

    Default threshold is 4.0 (4-fold rise).

    Handles missing baseline titers by returning NaN for those rows.
    """
    if threshold is None:
        threshold = get_seroconversion_threshold()

    baseline = df["titer_baseline"]
    post = df["titer_post"]

    # Check for missing baseline values
    baseline_missing = baseline.isna() | (baseline == 0)

    # Calculate ratio where baseline is valid
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = post / baseline
        ratio[baseline_missing] = np.nan

    # Seroconversion: ratio >= threshold
    status = ratio >= threshold

    # Convert to string labels
    status_labels = pd.Series(index=df.index, dtype="object")
    status_labels[status] = "seroconverter"
    status_labels[~status & ~baseline_missing] = "non-seroconverter"
    status_labels[baseline_missing] = np.nan

    logger.info(
        f"Seroconversion calculation (threshold={threshold}): "
        f"{status_labels.notna().sum()} valid, {status_labels.isna().sum()} missing baseline"
    )

    return status_labels

def calculate_absolute_titer_status(
    df: pd.DataFrame, threshold: Optional[float] = None
) -> pd.Series:
    """
    Calculate absolute titer responder status.

    Responder if: post_titer >= threshold (default HAI >= 40)

    This is used when baseline titers are missing.
    """
    if threshold is None:
        threshold = get_hai_threshold()

    post = df["titer_post"]
    status = post >= threshold

    status_labels = pd.Series(index=df.index, dtype="object")
    status_labels[status] = "responder"
    status_labels[~status] = "non-responder"

    logger.info(
        f"Absolute titer calculation (threshold={threshold}): "
        f"{status_labels.eq('responder').sum()} responders"
    )

    return status_labels

def define_responder_labels(
    df: pd.DataFrame,
    seroconversion_threshold: Optional[float] = None,
    absolute_threshold: Optional[float] = None,
) -> Tuple[pd.Series, str]:
    """
    Define responder labels using the following logic:

    1. If baseline titers exist (not NaN and > 0), use seroconversion status.
    2. If baseline titers are missing, use absolute titer status.

    Returns:
        Tuple of (responder_labels, mode_used)
    """
    baseline = df["titer_baseline"]
    has_baseline = baseline.notna() & (baseline > 0)

    # Calculate seroconversion for those with baseline
    sero_status = calculate_seroconversion_status(
        df, threshold=seroconversion_threshold
    )

    # Calculate absolute titer for all (will be used where baseline is missing)
    abs_status = calculate_absolute_titer_status(
        df, threshold=absolute_threshold
    )

    # Combine: use seroconversion where available, else absolute titer
    responder_labels = pd.Series(index=df.index, dtype="object")
    responder_labels[has_baseline] = sero_status[has_baseline]
    responder_labels[~has_baseline] = abs_status[~has_baseline]

    # Determine mode used
    if has_baseline.all():
        mode = "seroconversion_only"
    elif (~has_baseline).all():
        mode = "absolute_titer_only"
    else:
        mode = "hybrid"

    logger.info(f"Responder definition mode: {mode}")
    logger.info(
        f"Final labels: {responder_labels.notna().sum()} valid, "
        f"{responder_labels.isna().sum()} missing"
    )

    return responder_labels, mode

def save_responder_labels(
    df: pd.DataFrame,
    responder_labels: pd.Series,
    mode: str,
    output_path: Optional[Path] = None,
) -> Path:
    """
    Save responder labels to CSV file.

    Output format:
        subject_id,responder_status
    """
    if output_path is None:
        output_path = get_processed_path() / "responder_labels.csv"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    result_df = pd.DataFrame(
        {
            "subject_id": df["subject_id"].values,
            "responder_status": responder_labels.values,
        }
    )

    result_df.to_csv(output_path, index=False)
    logger.info(f"Saved responder labels to {output_path}")

    return output_path

def run_responder_definition(
    seroconversion_threshold: Optional[float] = None,
    absolute_threshold: Optional[float] = None,
) -> Tuple[Path, str]:
    """
    Main entry point for responder definition task.

    1. Load processed data
    2. Define responder labels based on available data
    3. Save results to CSV

    Returns:
        Tuple of (output_path, mode_used)
    """
    logger.info("Starting responder definition pipeline")

    df = load_processed_data()
    responder_labels, mode = define_responder_labels(
        df,
        seroconversion_threshold=seroconversion_threshold,
        absolute_threshold=absolute_threshold,
    )

    output_path = save_responder_labels(df, responder_labels, mode)

    return output_path, mode

def calculate_model_metrics(
    predictions: pd.Series, actuals: pd.Series
) -> Dict[str, float]:
    """
    Calculate basic model metrics (accuracy, precision, recall, F1).
    """
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

    y_true = (actuals == "responder").astype(int)
    y_pred = (predictions == "responder").astype(int)

    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }

    return metrics

def save_model_metrics(
    metrics: Dict[str, float],
    output_path: Optional[Path] = None,
) -> Path:
    """
    Save model metrics to JSON file.
    """
    import json

    if output_path is None:
        output_path = get_output_path() / "model_metrics.json"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Saved model metrics to {output_path}")
    return output_path

def main():
    """
    Main entry point for the responder definition task.
    """
    logging.basicConfig(level=logging.INFO)

    try:
        output_path, mode = run_responder_definition()
        logger.info(
            f"Responer definition complete. Mode: {mode}, Output: {output_path}"
        )
        return 0
    except Exception as e:
        log_error_context(logger, e)
        return 1

if __name__ == "__main__":
    sys.exit(main())