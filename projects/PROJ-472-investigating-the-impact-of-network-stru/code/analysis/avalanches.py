"""
Neural Avalanche Detection Module.

Implements detection of neural avalanches from simulated EEG signals.
The process involves:
1. Z-score normalization (global mean/std) of the signal.
2. Thresholding at a high percentile amplitude (per-participant).
3. Identifying contiguous sequences of suprathreshold events (avalanches).
4. Computing avalanche statistics (size, duration).
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

# Import from project modules based on API surface
from data.models import AvalancheRecord, Participant
from data.store import load_eeg_time_series
from config import get_data_root
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants
DEFAULT_THRESHOLD_PERCENTILE = 99.5
DEFAULT_TIME_BIN_SIZE = 0.01  # 10ms bins (adjustable based on sampling rate)

def z_score_normalize(signal: np.ndarray) -> Tuple[np.ndarray, float, float]:
    """
    Applies z-score normalization to the signal.

    Args:
        signal: 1D or 2D numpy array of signal data.

    Returns:
        normalized_signal, mean, std
    """
    mean_val = np.mean(signal)
    std_val = np.std(signal)
    if std_val == 0:
        logger.warning("Standard deviation is zero. Returning signal as-is.")
        return signal, mean_val, std_val
    normalized = (signal - mean_val) / std_val
    return normalized, mean_val, std_val

def calculate_threshold(signal: np.ndarray, percentile: float = DEFAULT_THRESHOLD_PERCENTILE) -> float:
    """
    Calculates the threshold value based on a high percentile of the signal amplitude.

    Args:
        signal: 1D numpy array of signal data (z-scored).
        percentile: The percentile to use for thresholding.

    Returns:
        Threshold value.
    """
    return np.percentile(signal, percentile)

def detect_avalanches(signal: np.ndarray, threshold: float) -> List[Dict[str, Any]]:
    """
    Detects neural avalanches by finding contiguous sequences of suprathreshold events.

    Args:
        signal: 1D numpy array of z-scored signal.
        threshold: The amplitude threshold.

    Returns:
        List of dictionaries containing avalanche metadata (start_idx, end_idx, size, duration).
    """
    suprathreshold = signal > threshold
    avalanches = []
    current_start = None
    current_size = 0

    for i, is_active in enumerate(suprathreshold):
        if is_active:
            if current_start is None:
                current_start = i
            current_size += 1
        else:
            if current_start is not None:
                # End of an avalanche
                avalanches.append({
                    "start_idx": current_start,
                    "end_idx": i - 1,
                    "size": current_size,
                    "duration_steps": i - current_start
                })
                current_start = None
                current_size = 0

    # Handle case where signal ends with an avalanche
    if current_start is not None:
        avalanches.append({
            "start_idx": current_start,
            "end_idx": len(signal) - 1,
            "size": current_size,
            "duration_steps": len(signal) - current_start
        })

    return avalanches

def run_avalanche_detection_for_subject(
    subject_id: str,
    threshold_percentile: float = DEFAULT_THRESHOLD_PERCENTILE,
    sampling_rate: float = 250.0
) -> Optional[AvalancheRecord]:
    """
    Runs the full avalanche detection pipeline for a single subject.

    Args:
        subject_id: The subject identifier.
        threshold_percentile: Percentile for thresholding.
        sampling_rate: Sampling rate of the signal in Hz.

    Returns:
        AvalancheRecord if data is found and processed, None otherwise.
    """
    try:
        # Load data
        logger.info(f"Loading EEG data for subject {subject_id}")
        eeg_df = load_eeg_time_series(subject_id)

        if eeg_df is None or eeg_df.empty:
            logger.warning(f"No EEG data found for subject {subject_id}")
            return None

        # Flatten signal if multi-channel (summing or mean, here we use mean for simplicity of global stat)
        # Or process channel-wise. The prompt implies "global mean/std" for the signal.
        # Assuming the stored data might be multi-channel. We'll flatten to 1D for global stats
        # as per "z-score normalization (global mean/std) to the *simulated* EEG signal".
        signal = eeg_df.values.flatten()

        # Step 1: Z-score normalization
        normalized_signal, mean_val, std_val = z_score_normalize(signal)

        # Step 2: Calculate threshold
        threshold = calculate_threshold(normalized_signal, threshold_percentile)

        # Step 3: Detect avalanches
        avalanche_events = detect_avalanches(normalized_signal, threshold)

        if not avalanche_events:
            logger.info(f"No avalanches detected for subject {subject_id} at {threshold_percentile}% threshold")
            # Return a record indicating zero events or None?
            # Let's return a record with zero events to maintain data integrity
            return AvalancheRecord(
                subject_id=subject_id,
                avalanche_count=0,
                mean_size=0.0,
                mean_duration=0.0,
                max_size=0,
                max_duration=0,
                raw_events=[]
            )

        # Compute statistics
        sizes = [e["size"] for e in avalanche_events]
        durations_steps = [e["duration_steps"] for e in avalanche_events]
        durations_seconds = [d / sampling_rate for d in durations_steps]

        record = AvalancheRecord(
            subject_id=subject_id,
            avalanche_count=len(avalanche_events),
            mean_size=float(np.mean(sizes)),
            mean_duration=float(np.mean(durations_seconds)),
            max_size=int(np.max(sizes)),
            max_duration=float(np.max(durations_seconds)),
            raw_events=avalanche_events
        )

        logger.info(f"Avalanche detection complete for {subject_id}: {len(avalanche_events)} events found.")
        return record

    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {str(e)}", exc_info=True)
        return None

def run_avalanche_pipeline(
    subject_ids: Optional[List[str]] = None,
    threshold_percentile: float = DEFAULT_THRESHOLD_PERCENTILE,
    output_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Runs avalanche detection for a list of subjects and saves results.

    Args:
        subject_ids: List of subject IDs to process. If None, scans data directory.
        threshold_percentile: Percentile for thresholding.
        output_dir: Directory to save the results CSV.

    Returns:
        DataFrame containing avalanche statistics for all processed subjects.
    """
    data_root = get_data_root()
    if output_dir is None:
        output_dir = data_root / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    # If no subject IDs provided, try to infer from existing data files
    if subject_ids is None:
        processed_dir = data_root / "processed"
        if processed_dir.exists():
            # Heuristic: look for EEG files or connectome files to find subjects
            # Assuming files are named like 'sub-XXX_eeg.csv' or similar
            files = list(processed_dir.glob("sub-*_eeg.csv"))
            subject_ids = [f.stem.split('_')[0].replace('sub-', '') for f in files]
            subject_ids = list(set(subject_ids)) # Deduplicate

    if not subject_ids:
        logger.warning("No subject IDs provided and none could be inferred.")
        return pd.DataFrame()

    results = []
    for sub_id in subject_ids:
        record = run_avalanche_detection_for_subject(sub_id, threshold_percentile)
        if record:
            results.append({
                "subject_id": record.subject_id,
                "avalanche_count": record.avalanche_count,
                "mean_size": record.mean_size,
                "mean_duration": record.mean_duration,
                "max_size": record.max_size,
                "max_duration": record.max_duration
            })

    df = pd.DataFrame(results)
    output_path = output_dir / "avalanche_metrics.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Avalanche metrics saved to {output_path}")

    return df

def main():
    """Main entry point for running avalanche detection."""
    logger.info("Starting Neural Avalanche Detection Pipeline")
    # Run for all available subjects
    df = run_avalanche_pipeline()
    if not df.empty:
        print(f"Processed {len(df)} subjects.")
        print(df.head())
    else:
        print("No subjects processed.")

if __name__ == "__main__":
    main()
