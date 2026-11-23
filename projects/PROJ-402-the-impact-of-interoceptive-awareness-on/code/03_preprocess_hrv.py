import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from utils.hrv_utils import validate_signal_structure, reject_artifacts, compute_clean_rr_stats
from utils.hrv_metrics import compute_rmssd, compute_sdsn

def load_wesad_ecg_data(subject_id: str, data_dir: Path) -> np.ndarray:
    """
    Load ECG data for a specific subject from WESAD dataset.
    
    Args:
        subject_id: Subject identifier
        data_dir: Path to the data directory
        
    Returns:
        ECG signal as numpy array
        
    Raises:
        FileNotFoundError: If the ECG file does not exist
        ValueError: If the data format is invalid
    """
    ecg_path = data_dir / f"sub-{subject_id}" / "sub-{subject_id}_ECG.csv"
    if not ecg_path.exists():
        raise FileNotFoundError(f"ECG file not found for subject {subject_id}")
    
    # Load the data
    try:
        df = pd.read_csv(ecg_path)
        if 'ECG' not in df.columns:
            raise ValueError(f"ECG column not found in file for subject {subject_id}")
        return df['ECG'].values
    except Exception as e:
        raise ValueError(f"Failed to load ECG data for subject {subject_id}: {str(e)}")

def bandpass_filter(signal: np.ndarray, fs: float = 700.0, lowcut: float = 0.5, highcut: float = 40.0) -> np.ndarray:
    """
    Apply bandpass filter to ECG signal.
    
    Args:
        signal: Input signal
        fs: Sampling frequency
        lowcut: Low cutoff frequency
        highcut: High cutoff frequency
        
    Returns:
        Filtered signal
    """
    from scipy.signal import butter, filtfilt
    
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(4, [low, high], btype='band')
    return filtfilt(b, a, signal)

def detect_peaks_ecg(signal: np.ndarray, fs: float = 700.0) -> np.ndarray:
    """
    Detect R-peaks in ECG signal.
    
    Args:
        signal: Filtered ECG signal
        fs: Sampling frequency
        
    Returns:
        Indices of detected R-peaks
    """
    from scipy.signal import find_peaks
    
    # Simple peak detection with prominence
    peaks, _ = find_peaks(signal, prominence=np.std(signal) * 0.5, distance=fs * 0.3)
    return peaks

def compute_rr_intervals(peaks: np.ndarray, fs: float = 700.0) -> np.ndarray:
    """
    Compute RR intervals from detected peaks.
    
    Args:
        peaks: Indices of R-peaks
        fs: Sampling frequency
        
    Returns:
        RR intervals in seconds
    """
    if len(peaks) < 2:
        return np.array([])
    return np.diff(peaks) / fs

def process_subject_ecg(subject_id: str, data_dir: Path, fs: float = 700.0) -> Dict[str, Any]:
    """
    Process ECG data for a single subject.
    
    Args:
        subject_id: Subject identifier
        data_dir: Path to data directory
        fs: Sampling frequency
        
    Returns:
        Dictionary containing processed data and metrics
    """
    try:
        # Load data
        ecg_signal = load_wesad_ecg_data(subject_id, data_dir)
        
        # Validate signal structure
        if not validate_signal_structure(ecg_signal):
            logging.warning(f"Subject {subject_id}: Signal structure validation failed")
            return {"subject_id": subject_id, "status": "excluded", "reason": "invalid_signal"}
        
        # Filter signal
        filtered_signal = bandpass_filter(ecg_signal, fs)
        
        # Detect peaks
        peaks = detect_peaks_ecg(filtered_signal, fs)
        
        # Reject artifacts
        valid_peaks, valid_indices = reject_artifacts(peaks, filtered_signal, fs)
        if len(valid_peaks) < 5:  # Minimum 5 beats for valid HRV
            logging.warning(f"Subject {subject_id}: Not enough valid beats ({len(valid_peaks)})")
            return {"subject_id": subject_id, "status": "excluded", "reason": "insufficient_beats"}
        
        # Compute RR intervals
        rr_intervals = compute_rr_intervals(valid_peaks, fs)
        
        # Validate HRV output
        if not validate_hrv_output(rr_intervals):
            logging.warning(f"Subject {subject_id}: HRV validation failed")
            return {"subject_id": subject_id, "status": "excluded", "reason": "invalid_hrv"}
        
        # Compute HRV metrics
        rmssd = compute_rmssd(rr_intervals)
        sdnn = compute_sdsn(rr_intervals)
        
        return {
            "subject_id": subject_id,
            "status": "success",
            "rmssd": rmssd,
            "sdnn": sdnn,
            "n_beats": len(valid_peaks),
            "rr_intervals": rr_intervals
        }
    except Exception as e:
        logging.error(f"Subject {subject_id}: Processing failed - {str(e)}")
        return {"subject_id": subject_id, "status": "excluded", "reason": str(e)}

def extract_stress_hrv_metrics(processed_data: Dict[str, Any], phase: str = "stress") -> Dict[str, float]:
    """
    Extract HRV metrics for a specific phase.
    
    Args:
        processed_data: Processed data dictionary
        phase: Phase name (e.g., "stress", "baseline")
        
    Returns:
        Dictionary with HRV metrics for the phase
    """
    if processed_data.get("status") != "success":
        return {}
    return {
        "phase": phase,
        "RMSSD": processed_data.get("rmssd", 0.0),
        "SDNN": processed_data.get("sdnn", 0.0)
    }

def save_cleaned_data(results: List[Dict[str, Any]], output_path: Path):
    """
    Save cleaned HRV data to CSV.
    
    Args:
        results: List of processed data dictionaries
        output_path: Path to output CSV file
    """
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logging.info(f"Saved HRV metrics to {output_path}")

def main():
    """Main entry point for HRV preprocessing."""
    logging.basicConfig(level=logging.INFO)
    
    data_dir = Path("data/raw/wesad")
    output_dir = Path("data/derived")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "hrv_metrics.csv"
    results = []
    
    # Process subjects (example: process subjects 1-10)
    for subject_id in range(1, 11):
        sid = f"sub-{subject_id:03d}"
        logging.info(f"Processing {sid}...")
        processed = process_subject_ecg(sid, data_dir)
        if processed["status"] == "success":
            stress_metrics = extract_stress_hrv_metrics(processed, "stress")
            baseline_metrics = extract_stress_hrv_metrics(processed, "baseline")
            if stress_metrics:
                results.append({"subject_id": sid, "phase": "stress", "RMSSD": stress_metrics["RMSSD"], "SDNN": stress_metrics["SDNN"]})
            if baseline_metrics:
                results.append({"subject_id": sid, "phase": "baseline", "RMSSD": baseline_metrics["RMSSD"], "SDNN": baseline_metrics["SDNN"]})
        else:
            logging.warning(f"Excluded {sid}: {processed.get('reason', 'unknown')}")
    
    if results:
        save_cleaned_data(results, output_file)
    else:
        logging.warning("No valid HRV metrics computed. Output file not created.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
