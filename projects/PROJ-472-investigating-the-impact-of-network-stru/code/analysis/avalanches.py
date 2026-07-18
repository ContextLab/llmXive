import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

from config import get_data_root
from utils.logger import get_logger
from data.models import AvalancheRecord, Participant

logger = get_logger(__name__)

def z_score_normalize(signal: np.ndarray) -> np.ndarray:
    mean = np.mean(signal)
    std = np.std(signal)
    if std == 0:
        return np.zeros_like(signal)
    return (signal - mean) / std

def calculate_threshold(raw_signal: np.ndarray) -> float:
    """
    Calculates the 75th percentile of the RAW signal.
    This is the threshold to be applied to the Z-scored signal.
    """
    return np.percentile(raw_signal, 75)

def detect_avalanches(z_signal: np.ndarray, threshold: float) -> List[Dict]:
    """
    Detects avalanches from z-scored signal using the threshold.
    Returns list of avalanche events.
    """
    events = []
    # Simple thresholding: find contiguous regions above threshold
    # This is a simplified 1D version. Real implementation would be spatiotemporal.
    above = z_signal > threshold
    indices = np.where(above)[0]
    
    if len(indices) == 0:
        return events
    
    # Group contiguous indices
    groups = np.split(indices, np.where(np.diff(indices) != 1)[0] + 1)
    for group in groups:
        size = len(group)
        duration = size # Assuming 1 sample = 1 unit duration for simplicity
        events.append({
            "size": size,
            "duration": duration,
            "timestamp": group[0]
        })
    return events

def run_avalanche_detection_for_subject(subject_id: str, data_root: Path):
    """Runs avalanche detection for a single subject."""
    eeg_file = data_root / "processed" / "eeg" / f"sub-{subject_id}" / "eeg_cleaned.fif"
    if not eeg_file.exists():
        logger.warning(f"EEG file missing for {subject_id}")
        return
    
    import mne
    raw = mne.io.read_raw_fif(eeg_file, preload=True)
    data = raw.get_data()
    
    # Flatten to 1D for simplicity in this artifact
    signal_1d = data.flatten()
    
    z_signal = z_score_normalize(signal_1d)
    threshold = calculate_threshold(signal_1d)
    
    events = detect_avalanches(z_signal, threshold)
    
    # Save events
    out_dir = data_root / "processed" / "avalanches" / f"sub-{subject_id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "avalanche_events.csv"
    
    if events:
        df = pd.DataFrame(events)
        df["participant_id"] = subject_id
        df.to_csv(out_file, index=False)
    else:
        pd.DataFrame(columns=["size", "duration", "timestamp", "participant_id"]).to_csv(out_file, index=False)
    
    logger.info(f"Saved {len(events)} events for {subject_id}")

def run_avalanche_pipeline(data_root: Path):
    """Runs avalanche pipeline for all subjects."""
    # Find subjects
    eeg_dir = data_root / "processed" / "eeg"
    if not eeg_dir.exists():
        return
    
    subjects = [d.name for d in eeg_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    for sub_id in subjects:
        run_avalanche_detection_for_subject(sub_id, data_root)

def main():
    data_root = get_data_root()
    run_avalanche_pipeline(data_root)

if __name__ == "__main__":
    main()
