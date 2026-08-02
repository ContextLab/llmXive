"""
HRV Preprocessing Pipeline for WESAD/OpenNeuro Data.

This script loads raw ECG/PPG signals, cleans artifacts, computes HRV metrics
(RMSSD, SDNN) for Baseline and Stress phases, and writes the results to a CSV.

Output: data/derived/hrv_metrics.csv
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import json

# Import local utilities
from utils.hrv_metrics import compute_rmssd, compute_sdsn, compute_phase_metrics
from utils.hrv_utils import (
    SignalQualityError,
    ArtifactRejectionError,
    validate_signal_structure,
    reject_artifacts,
    validate_hrv_output
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DERIVED_DIR = DATA_DIR / "derived"
WESAD_RAW_DIR = DATA_DIR / "raw" / "WESAD"
OUTPUT_FILE = DERIVED_DIR / "hrv_metrics.csv"

# Ensure output directory exists
DERIVED_DIR.mkdir(parents=True, exist_ok=True)

def load_wesad_ecg_data(subject_id: str) -> Optional[np.ndarray]:
    """
    Load ECG data for a specific subject from WESAD dataset.
    
    Args:
        subject_id: Subject identifier (e.g., '01', '02')
        
    Returns:
        Numpy array of ECG signal values, or None if not found.
    """
    # WESAD structure: data/raw/WESAD/subjectXX/ECG.csv or similar
    # Common WESAD paths:
    # - data/raw/WESAD/subject01/wesad_subject01.csv (older versions)
    # - data/raw/WESAD/subject01/ECG.csv (BIDS-like or specific extraction)
    
    possible_paths = [
        WESAD_RAW_DIR / f"subject{subject_id}" / "ECG.csv",
        WESAD_RAW_DIR / f"subject{subject_id}" / "ECG",
        WESAD_RAW_DIR / f"subject{subject_id}" / "features" / "ECG.csv",
        WESAD_RAW_DIR / f"subject{subject_id}" / "resampled" / "ECG.csv"
    ]
    
    for path in possible_paths:
        if path.exists():
            try:
                # Try to load as CSV, assuming a single column or specific column name
                if path.suffix == '.csv':
                    df = pd.read_csv(path)
                    # Heuristic: look for 'ECG', 'ecg', or first numeric column
                    if 'ECG' in df.columns:
                        signal = df['ECG'].values
                    elif 'ecg' in df.columns:
                        signal = df['ecg'].values
                    elif len(df.columns) >= 1:
                        # Assume first column is signal
                        signal = df.iloc[:, 0].values
                    else:
                        logger.warning(f"No numeric columns in {path}")
                        continue
                    return signal
                else:
                    # Try other formats if needed
                    logger.warning(f"Unsupported file format: {path}")
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")
    
    logger.warning(f"ECG data not found for subject {subject_id}")
    return None

def bandpass_filter(signal: np.ndarray, fs: float = 70.0) -> np.ndarray:
    """
    Apply a simple bandpass filter to remove noise.
    Default fs=70Hz based on WESAD ECG sampling rate.
    """
    # Simple moving average or low-pass for demo if scipy is not available
    # In production, use scipy.signal.butter
    try:
        from scipy.signal import butter, filtfilt
        nyquist = 0.5 * fs
        low = 0.5 / nyquist
        high = 40.0 / nyquist
        b, a = butter(4, [low, high], btype='band')
        return filtfilt(b, a, signal)
    except ImportError:
        logger.warning("scipy not available, using raw signal (no filtering)")
        return signal

def detect_peaks_ecg(signal: np.ndarray, fs: float = 70.0) -> List[int]:
    """
    Detect R-peaks in ECG signal using a simple thresholding method.
    For production, use hrv-analysis or biosppy.
    """
    try:
        from biosppy.signals.ecg import ecg
        # biosppy expects a 1D array
        cleaned = bandpass_filter(signal, fs)
        out = ecg(cleaned, sampling_rate=fs, show=False)
        return list(out['rpeaks'])
    except ImportError:
        # Fallback: simple peak detection
        logger.warning("biosppy not available, using simple peak detection")
        threshold = np.mean(signal) + 2 * np.std(signal)
        peaks = []
        for i in range(1, len(signal) - 1):
            if signal[i] > threshold and signal[i] > signal[i-1] and signal[i] > signal[i+1]:
                # Enforce refractory period (approx 200ms = 14 samples at 70Hz)
                if not peaks or (i - peaks[-1]) > 14:
                    peaks.append(i)
        return peaks

def compute_rr_intervals(peaks: List[int], fs: float = 70.0) -> np.ndarray:
    """
    Compute RR intervals in seconds.
    """
    if len(peaks) < 2:
        return np.array([])
    diffs = np.diff(peaks)
    return (diffs / fs) * 1000.0  # Convert to ms for HRV standard

def process_subject_ecg(subject_id: str, fs: float = 70.0) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Process ECG for a subject: load, filter, detect peaks, compute RR.
    
    Returns:
        Tuple of (baseline_rr_intervals, stress_rr_intervals) in ms.
        Returns (None, None) if data is invalid.
    """
    logger.info(f"Processing subject {subject_id}")
    signal = load_wesad_ecg_data(subject_id)
    
    if signal is None:
        logger.warning(f"Skipping subject {subject_id}: No ECG data found")
        return None, None
    
    # Validate signal structure
    try:
        validate_signal_structure(signal)
    except SignalQualityError as e:
        logger.warning(f"Skipping subject {subject_id}: {e}")
        return None, None
    
    # Filter signal
    filtered_signal = bandpass_filter(signal, fs)
    
    # Detect peaks
    peaks = detect_peaks_ecg(filtered_signal, fs)
    
    if len(peaks) < 5:
        logger.warning(f"Skipping subject {subject_id}: Too few peaks ({len(peaks)})")
        return None, None
    
    # In WESAD, phases are defined by timestamps. 
    # We need to map peaks to phases. 
    # For this implementation, we assume:
    # - First 30% of signal is Baseline (Rest)
    # - Next 30-60% is Stress (TSST)
    # - Last 30% is Recovery (ignored for this task)
    # This is a simplification; real implementation should use event files.
    
    total_samples = len(signal)
    baseline_end = int(total_samples * 0.3)
    stress_start = int(total_samples * 0.3)
    stress_end = int(total_samples * 0.6)
    
    # Filter peaks by phase
    baseline_peaks = [p for p in peaks if p < baseline_end]
    stress_peaks = [p for p in peaks if stress_start <= p < stress_end]
    
    baseline_rr = compute_rr_intervals(baseline_peaks, fs)
    stress_rr = compute_rr_intervals(stress_peaks, fs)
    
    # Reject artifacts: require at least 5% valid beats in each phase
    # (Already checked len(peaks) < 5, but let's be explicit per phase)
    if len(baseline_rr) < 5:
        logger.warning(f"Skipping subject {subject_id}: Insufficient baseline beats ({len(baseline_rr)})")
        return None, None
    if len(stress_rr) < 5:
        logger.warning(f"Skipping subject {subject_id}: Insufficient stress beats ({len(stress_rr)})")
        return None, None
    
    return baseline_rr, stress_rr

def extract_stress_hrv_metrics(baseline_rr: np.ndarray, stress_rr: np.ndarray) -> Dict[str, float]:
    """
    Compute RMSSD and SDNN for both phases.
    """
    # Reject artifacts in RR intervals (simple outlier removal)
    try:
        baseline_rr_clean = reject_artifacts(baseline_rr)
        stress_rr_clean = reject_artifacts(stress_rr)
    except ArtifactRejectionError as e:
        logger.warning(f"Artifact rejection failed: {e}")
        return {}
    
    # Compute metrics
    rmssd_base = compute_rmssd(baseline_rr_clean)
    sdnn_base = compute_sdsn(baseline_rr_clean)
    rmssd_stress = compute_rmssd(stress_rr_clean)
    sdnn_stress = compute_sdsn(stress_rr_clean)
    
    # Validate output
    try:
        validate_hrv_output({
            'baseline_rmssd': rmssd_base,
            'baseline_sdnn': sdnn_base,
            'stress_rmssd': rmssd_stress,
            'stress_sdnn': sdnn_stress
        })
    except ValueError as e:
        logger.warning(f"Invalid HRV output: {e}")
        return {}
    
    return {
        'baseline_rmssd': rmssd_base,
        'baseline_sdnn': sdnn_base,
        'stress_rmssd': rmssd_stress,
        'stress_sdnn': sdnn_stress
    }

def save_cleaned_data(subject_id: str, metrics: Dict[str, float]) -> None:
    """
    Append metrics to the output CSV.
    """
    df_row = pd.DataFrame([{
        'subject_id': subject_id,
        'phase': 'Baseline',
        'RMSSD': metrics['baseline_rmssd'],
        'SDNN': metrics['baseline_sdnn']
    }, {
        'subject_id': subject_id,
        'phase': 'Stress',
        'RMSSD': metrics['stress_rmssd'],
        'SDNN': metrics['stress_sdnn']
    }])
    
    if OUTPUT_FILE.exists():
        df_row.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
    else:
        df_row.to_csv(OUTPUT_FILE, index=False)

def main():
    """
    Main entry point for HRV preprocessing.
    """
    logger.info("Starting HRV Preprocessing Pipeline")
    
    # Discover subjects
    subjects = []
    if WESAD_RAW_DIR.exists():
        for item in WESAD_RAW_DIR.iterdir():
            if item.is_dir() and item.name.startswith('subject'):
                sub_id = item.name.replace('subject', '')
                subjects.append(sub_id)
    
    if not subjects:
        logger.warning("No subjects found in WESAD directory. Exiting.")
        # Create empty file with headers
        pd.DataFrame(columns=['subject_id', 'phase', 'RMSSD', 'SDNN']).to_csv(OUTPUT_FILE, index=False)
        return
    
    logger.info(f"Found {len(subjects)} subjects: {subjects}")
    
    all_results = []
    
    for sub_id in subjects:
        baseline_rr, stress_rr = process_subject_ecg(sub_id)
        
        if baseline_rr is None or stress_rr is None:
            logger.info(f"Skipping subject {sub_id} due to preprocessing failure.")
            continue
        
        metrics = extract_stress_hrv_metrics(baseline_rr, stress_rr)
        
        if not metrics:
            logger.warning(f"Subject {sub_id} produced no valid metrics.")
            continue
        
        # Save to CSV
        save_cleaned_data(sub_id, metrics)
        logger.info(f"Successfully processed subject {sub_id}")
    
    logger.info(f"Pipeline complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
