"""
HRV Metrics Computation Module.

Computes Heart Rate Variability (HRV) metrics (RMSSD, SDNN) for specific
phases (Baseline, Stress) from cleaned RR interval data.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def compute_rmssd(rr_intervals: np.ndarray) -> float:
    """
    Compute the Root Mean Square of Successive Differences (RMSSD).

    RMSSD is the primary time-domain measure of heart rate variability
    related to parasympathetic (vagal) tone.

    Parameters
    ----------
    rr_intervals : np.ndarray
        Array of RR intervals in milliseconds.

    Returns
    -------
    float
        RMSSD value in milliseconds. Returns np.nan if calculation fails.
    """
    if len(rr_intervals) < 2:
        logger.warning("Insufficient RR intervals for RMSSD calculation.")
        return np.nan

    try:
        # Calculate successive differences
        diff = np.diff(rr_intervals)
        # Square the differences
        sq_diff = diff ** 2
        # Mean of squared differences
        mean_sq_diff = np.mean(sq_diff)
        # Square root of the mean
        rmssd = np.sqrt(mean_sq_diff)
        return float(rmssd)
    except Exception as e:
        logger.error(f"Error computing RMSSD: {e}")
        return np.nan


def compute_sdsn(rr_intervals: np.ndarray) -> float:
    """
    Compute the Standard Deviation of NN intervals (SDNN).

    SDNN reflects the overall variability of the heart rate over the period.

    Parameters
    ----------
    rr_intervals : np.ndarray
        Array of RR intervals in milliseconds.

    Returns
    -------
    float
        SDNN value in milliseconds. Returns np.nan if calculation fails.
    """
    if len(rr_intervals) < 2:
        logger.warning("Insufficient RR intervals for SDNN calculation.")
        return np.nan

    try:
        sdnn = float(np.std(rr_intervals, ddof=1))
        return sdnn
    except Exception as e:
        logger.error(f"Error computing SDNN: {e}")
        return np.nan


def compute_phase_metrics(
    rr_intervals: np.ndarray,
    phase_name: str,
    subject_id: str
) -> Dict[str, float]:
    """
    Compute HRV metrics for a specific phase.

    Parameters
    ----------
    rr_intervals : np.ndarray
        Array of RR intervals in milliseconds for the specific phase.
    phase_name : str
        Name of the phase (e.g., "Baseline", "Stress").
    subject_id : str
        Identifier for the subject.

    Returns
    -------
    Dict[str, float]
        Dictionary containing subject_id, phase, RMSSD, and SDNN.
    """
    rmssd = compute_rmssd(rr_intervals)
    sdnn = compute_sdsn(rr_intervals)

    return {
        "subject_id": subject_id,
        "phase": phase_name,
        "RMSSD": rmssd,
        "SDNN": sdnn
    }


def aggregate_hrv_metrics(
    processed_data: List[Dict],
    output_path: str
) -> None:
    """
    Aggregate HRV metrics from processed subject data and save to CSV.

    Expects processed_data to be a list of dictionaries where each dictionary
    contains 'subject_id', 'phase', and 'rr_intervals' (numpy array).

    Parameters
    ----------
    processed_data : List[Dict]
        List of dictionaries with processed RR interval data.
    output_path : str
        Path to the output CSV file.
    """
    import pandas as pd
    import os

    metrics_list = []

    for entry in processed_data:
        subject_id = entry.get("subject_id")
        phase = entry.get("phase")
        rr_intervals = entry.get("rr_intervals")

        if subject_id is None or phase is None or rr_intervals is None:
            logger.warning(f"Skipping incomplete entry: {entry}")
            continue

        if not isinstance(rr_intervals, np.ndarray):
            try:
                rr_intervals = np.array(rr_intervals)
            except Exception as e:
                logger.error(f"Could not convert RR intervals for {subject_id}-{phase}: {e}")
                continue

        metrics = compute_phase_metrics(rr_intervals, phase, subject_id)
        metrics_list.append(metrics)

    if not metrics_list:
        logger.error("No valid metrics computed. Ensure processed_data contains valid RR intervals.")
        # Create an empty file with headers to satisfy downstream expectations if needed,
        # though typically this indicates a pipeline failure upstream.
        pd.DataFrame(columns=["subject_id", "phase", "RMSSD", "SDNN"]).to_csv(output_path, index=False)
        return

    df = pd.DataFrame(metrics_list)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_csv(output_path, index=False)
    logger.info(f"HRV metrics saved to {output_path} with {len(df)} rows.")
