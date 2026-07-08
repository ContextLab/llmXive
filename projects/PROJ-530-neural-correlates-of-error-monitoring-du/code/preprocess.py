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

    # Placeholder for actual MNE filtering
    # In real implementation: use mne.filter.filter_data()
    filtered_data = raw_data.copy()

    # Simulate filtering (remove this in real implementation)
    # This is just to satisfy the function signature for now
    from scipy.signal import butter, filtfilt

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

    filtered_data = butter_bandpass_filter(
        filtered_data, bandpass[0], bandpass[1], sfreq
    )

    return filtered_data

def run_ica(raw_data: np.ndarray, n_components: Optional[int] = None) -> Dict[str, Any]:
    """
    Run ICA to identify and remove artifacts.

    Args:
        raw_data: Preprocessed EEG data.
        n_components: Number of ICA components (None for automatic).

    Returns:
        Dictionary with ICA results and removed components.
    """
    logger = logging.getLogger(__name__)
    logger.info("Running ICA for artifact removal")

    # Placeholder for actual MNE ICA
    # In real implementation: use mne.preprocessing.ICA
    result = {
        'n_components': n_components,
        'removed_components': [],
        'ica_info': 'Placeholder ICA result'
    }

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

    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(log_data, f, default_flow_style=False)

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
        raw_file: Path to raw EEG data file.
        config: Preprocessing configuration dictionary.

    Returns:
        Dictionary with processed data and metadata.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing EEG data from {raw_file}")

    # Placeholder for actual data loading and processing
    # In real implementation: use mne.io.read_raw()

    result = {
        'raw_file': raw_file,
        'config': config,
        'processed': True,
        'message': 'Placeholder processing result'
    }

    return result

def main():
    """
    Main function to run preprocessing pipeline.
    """
    import argparse
    parser = argparse.ArgumentParser(description='Preprocess EEG data')
    parser.add_argument('--config', type=str, required=True, help='Path to config file')
    parser.add_argument('--input', type=str, required=True, help='Path to input data')
    parser.add_argument('--output', type=str, required=True, help='Path to output directory')

    args = parser.parse_args()

    # Load config
    from .config_loader import load_config
    config = load_config(args.config)

    # Run processing
    result = process_eeg_data(args.input, config)

    # Save results
    save_preprocessing_log(result, f"{args.output}/preprocessing_log.yaml")

    print(f"Preprocessing complete. Results saved to {args.output}")

if __name__ == '__main__':
    main()