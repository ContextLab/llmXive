"""
Preprocessing module for EEG data analysis.
Handles filtering, ICA, epoch extraction, and feature calculation.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import mne
from scipy.signal import butter, filtfilt
from scipy.stats import kurtosis

def calculate_angular_deviation(heading_vector: np.ndarray, optimal_vector: np.ndarray) -> Optional[float]:
    """
    Calculate the angular deviation (in degrees) between two vectors.

    Args:
        heading_vector: Current heading direction vector.
        optimal_vector: Optimal path direction vector.

    Returns:
        Angular deviation in degrees, or None if vectors are zero-length.
    """
    logger = logging.getLogger(__name__)

    # Check for zero-length vectors
    if np.linalg.norm(heading_vector) < 1e-10 or np.linalg.norm(optimal_vector) < 1e-10:
        logger.warning("Zero-length vector detected in angular deviation calculation. Returning None.")
        return None

    # Normalize vectors
    heading_norm = heading_vector / np.linalg.norm(heading_vector)
    optimal_norm = optimal_vector / np.linalg.norm(optimal_vector)

    # Calculate dot product and clip to [-1, 1] to avoid numerical errors
    dot_product = np.clip(np.dot(heading_norm, optimal_norm), -1.0, 1.0)

    # Calculate angle in radians and convert to degrees
    angle_rad = np.arccos(dot_product)
    angle_deg = np.degrees(angle_rad)

    return angle_deg

def apply_filters(raw_data: np.ndarray, sfreq: float, bandpass: List[float], notch: float) -> np.ndarray:
    """
    Apply bandpass and notch filters to raw EEG data.

    Args:
        raw_data: Raw EEG data array (n_channels, n_samples).
        sfreq: Sampling frequency in Hz.
        bandpass: [low_cutoff, high_cutoff] for bandpass filter.
        notch: Notch filter frequency (e.g., 50 or 60 Hz).

    Returns:
        Filtered EEG data.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Applying bandpass filter [{bandpass[0]}Hz, {bandpass[1]}Hz] and notch filter {notch}Hz")

    # Band‑pass filter using butterworth
    def butter_bandpass(lowcut, highcut, fs, order=4):
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        return b, a

    def butter_bandpass_filter(data, lowcut, highcut, fs, order=4):
        b, a = butter_bandpass(lowcut, highcut, fs, order=order)
        y = filtfilt(b, a, data, axis=1)
        return y

    filtered = butter_bandpass_filter(raw_data, bandpass[0], bandpass[1], sfreq)

    # Notch filter (simple FIR notch using mne)
    try:
        notch_filter = mne.filter.notch_filter(filtered, sfreq, np.array([notch]), verbose=False)
        filtered = notch_filter
    except Exception as e:
        logger.warning(f"Notch filter failed ({e}); proceeding without notch.")

    return filtered

def run_ica(raw_data: np.ndarray, sfreq: float, n_components: Optional[int] = None) -> Dict[str, Any]:
    """
    Run ICA to identify and remove artifacts.

    Args:
        raw_data: Preprocessed EEG data (n_channels, n_samples).
        sfreq: Sampling frequency in Hz.
        n_components: Number of ICA components (None for automatic).

    Returns:
        Dictionary with ICA results and removed components.
    """
    logger = logging.getLogger(__name__)
    logger.info("Running ICA for artifact removal")

    # Create MNE Raw object from numpy data
    n_channels = raw_data.shape[0]
    ch_names = [f'CH{i}' for i in range(n_channels)]
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    raw = mne.io.RawArray(raw_data, info, verbose=False)

    # Fit ICA
    ica = mne.preprocessing.ICA(n_components=n_components or 0.95,
                                random_state=0,
                                max_iter='auto',
                                verbose=False)
    ica.fit(raw)

    # Simple heuristic: mark components with high kurtosis as artifacts
    sources = ica.get_sources(raw).get_data()
    component_kurtosis = kurtosis(sources, axis=1)
    kurt_threshold = np.percentile(np.abs(component_kurtosis), 90)  # top 10% as bad
    bad_idxs = [idx for idx, val in enumerate(component_kurtosis) if np.abs(val) >= kurt_threshold]

    ica.exclude = bad_idxs
    cleaned_raw = ica.apply(raw.copy())

    result = {
        'n_components': ica.n_components_,
        'removed_components': bad_idxs,
        'ica_info': 'ICA performed with kurtosis‑based exclusion',
        'cleaned_data': cleaned_raw.get_data()
    }
    logger.info(f"ICA removed components: {bad_idxs}")

    return result

def save_preprocessing_log(log_data: Dict[str, Any], output_path: str) -> None:
    """
    Save preprocessing parameters and results to a YAML file.

    Args:
        log_data: Dictionary containing preprocessing parameters and results.
        output_path: Path to save the log file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing log if present and append
    if path.is_file():
        with open(path, 'r', encoding='utf-8') as f:
            existing = yaml.safe_load(f) or {}
    else:
        existing = {}

    # Ensure top‑level structure
    existing.setdefault('version', 1.0)
    existing.setdefault('generated_by', 'preprocess.py')
    existing.setdefault('timestamp', None)
    existing.setdefault('entries', [])

    entry = {
        'step': log_data.get('step', 'ICA'),
        'details': log_data
    }
    existing['entries'].append(entry)

    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(existing, f, default_flow_style=False)

    logger = logging.getLogger(__name__)
    logger.info(f"Preprocessing log saved to {output_path}")

def extract_mfn_features(epochs_data: np.ndarray, times: np.ndarray,
                         electrodes: List[str], mfn_window: tuple,
                         baseline: tuple) -> Dict[str, Any]:
    """
    Extract MFN (Medial Frontal Negativity) features from epochs.

    Args:
        epochs_data: Epoch data array (n_epochs, n_channels, n_times).
        times: Time points array.
        electrodes: List of electrode names to extract from.
        mfn_window: (start, end) window in seconds for mean amplitude.
        baseline: (start, end) window in seconds for baseline correction.

    Returns:
        Dictionary with extracted features (mean and peak amplitude).
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Extracting MFN features in window {mfn_window}s with baseline {baseline}s")

    features = {}

    # Find indices for windows
    mfn_start_idx = np.where(times >= mfn_window[0])[0][0] if len(times[times >= mfn_window[0]]) > 0 else 0
    mfn_end_idx = np.where(times <= mfn_window[1])[0][-1] if len(times[times <= mfn_window[1]]) > 0 else len(times) - 1
    baseline_start_idx = np.where(times >= baseline[0])[0][0] if len(times[times >= baseline[0]]) > 0 else 0
    baseline_end_idx = np.where(times <= baseline[1])[0][-1] if len(times[times <= baseline[1]]) > 0 else len(times) - 1

    # Calculate baseline mean for each epoch
    baseline_mean = np.mean(epochs_data[:, :, baseline_start_idx:baseline_end_idx], axis=2)

    # Baseline correction
    corrected_data = epochs_data - baseline_mean[:, :, np.newaxis]

    for electrode in electrodes:
        # Extract mean amplitude in MFN window
        mean_amplitude = np.mean(corrected_data[:, :, mfn_start_idx:mfn_end_idx], axis=(1, 2))

        # Extract peak (most negative) amplitude in MFN window
        peak_amplitude = np.min(corrected_data[:, :, mfn_start_idx:mfn_end_idx], axis=(1, 2))

        features[electrode] = {
            'mean_amplitude': mean_amplitude,
            'peak_amplitude': peak_amplitude
        }

    return features

def process_eeg_data(raw_file: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process raw EEG data according to configuration.

    Args:
        raw_file: Path to raw EEG data file (CSV with columns FCz, Cz, Fz).
        config: Preprocessing configuration dictionary.

    Returns:
        Dictionary with processed data and metadata, including ICA removal info.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing EEG data from {raw_file}")

    # Load CSV
    df = pd.read_csv(raw_file)

    # Extract EEG channels (assume columns FCz, Cz, Fz)
    eeg_channels = ['FCz', 'Cz', 'Fz']
    if not all(ch in df.columns for ch in eeg_channels):
        raise ValueError(f"EEG channel columns {eeg_channels} not found in {raw_file}")

    # Pivot to shape (n_channels, n_samples)
    # Assume data is ordered by time; we take the values as they appear
    eeg_data = df[eeg_channels].to_numpy().T  # shape (3, n_samples)

    sfreq = config.get('preprocessing', {}).get('sfreq', 1000.0)  # default 1000 Hz
    bandpass = config.get('preprocessing', {}).get('filter_bandpass', [1.0, 40.0])
    notch = config.get('preprocessing', {}).get('filter_notch', 50.0)

    # Filtering
    filtered = apply_filters(eeg_data, sfreq, bandpass, notch)

    # ICA
    ica_result = run_ica(filtered, sfreq)

    result = {
        'raw_file': raw_file,
        'config': config,
        'filtered_shape': filtered.shape,
        'ica': {
            'removed_components': ica_result['removed_components'],
            'n_components': ica_result['n_components']
        },
        'processed': True,
        'message': 'EEG data filtered and ICA applied'
    }

    return result

def main():
    """
    Main function to run preprocessing pipeline.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Preprocess EEG data')
    parser.add_argument('--config', type=str, required=False, help='Path to config file')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV data')
    parser.add_argument('--output', type=str, required=True, help='Path to output directory')
    args = parser.parse_args()

    # Load configuration (defaults if missing)
    from .config_loader import load_config
    config = load_config(args.config)

    # Run processing
    result = process_eeg_data(args.input, config)

    # Save ICA log to the canonical preprocessing log
    log_path = Path('data/preprocessing.yaml')
    log_data = {
        'step': 'ICA',
        'removed_components': result['ica']['removed_components'],
        'n_components': result['ica']['n_components'],
        'raw_file': args.input
    }
    save_preprocessing_log(log_data, str(log_path))

    # Ensure output directory exists (may be used by downstream steps)
    Path(args.output).mkdir(parents=True, exist_ok=True)

    print(f"Preprocessing complete. ICA log written to {log_path}")

if __name__ == '__main__':
    main()
