"""
preprocessing.py

Core signal processing and feature extraction for DEAP EMG data.
Implements filtering, windowing, feature extraction, and data integrity checks.
"""

import os
import logging
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, iirnotch
from config import get_config_summary
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/processed/preprocessing.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
EMG_CHANNELS = {
    'corrugator': 10,
    'zygomaticus': 11,
    'orbicularis': 12
}
MISSING_THRESHOLD = 0.1  # Max fraction of missing data allowed before exclusion

def butter_bandpass(lowcut, highcut, fs, order=4):
    """
    Design a Butterworth bandpass filter.

    Args:
        lowcut: Lower frequency cutoff (Hz)
        highcut: Upper frequency cutoff (Hz)
        fs: Sampling frequency (Hz)
        order: Filter order

    Returns:
        b, a: Filter coefficients
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def apply_bandpass_filter(data, lowcut, highcut, fs, order=4):
    """
    Apply a Butterworth bandpass filter to the data.

    Args:
        data: 1D numpy array of signal data
        lowcut: Lower frequency cutoff (Hz)
        highcut: Upper frequency cutoff (Hz)
        fs: Sampling frequency (Hz)
        order: Filter order

    Returns:
        filtered_data: Filtered signal
    """
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    return filtfilt(b, a, data)

def apply_notch_filter(data, freq, fs, quality=30):
    """
    Apply a notch filter to remove power line interference.

    Args:
        data: 1D numpy array of signal data
        freq: Notch frequency (Hz) - typically 50 or 60
        fs: Sampling frequency (Hz)
        quality: Quality factor for the notch filter

    Returns:
        filtered_data: Filtered signal
    """
    b, a = iirnotch(freq, quality, fs)
    return filtfilt(b, a, data)

def baseline_correct(data, baseline_indices):
    """
    Correct signal baseline using pre-stimulus interval.

    Args:
        data: 1D numpy array of signal data
        baseline_indices: Indices corresponding to pre-stimulus interval

    Returns:
        corrected_data: Baseline-corrected signal
    """
    baseline_mean = np.mean(data[baseline_indices])
    return data - baseline_mean

def extract_rms(data):
    """Calculate Root Mean Square (RMS) of the signal."""
    return np.sqrt(np.mean(data**2))

def extract_zcr(data):
    """Calculate Zero Crossing Rate (ZCR) of the signal."""
    return np.sum(np.diff(np.sign(data)) != 0) / len(data)

def extract_wamp(data, threshold=0.0001):
    """
    Calculate Willison Amplitude (WAMP) of the signal.

    Args:
        data: 1D numpy array of signal data
        threshold: Threshold for amplitude difference

    Returns:
        wamp: Willison Amplitude value
    """
    diffs = np.abs(np.diff(data))
    return np.sum(diffs > threshold)

def extract_mav(data):
    """Calculate Mean Absolute Value (MAV) of the signal."""
    return np.mean(np.abs(data))

def create_windows(data, window_size, overlap=0):
    """
    Create non-overlapping windows from the signal.

    Args:
        data: 1D numpy array of signal data
        window_size: Size of each window (samples)
        overlap: Overlap between windows (samples) - set to 0 for non-overlapping

    Returns:
        windows: List of 1D numpy arrays, each representing a window
    """
    if overlap < 0:
        raise ValueError("Overlap must be non-negative")

    step = window_size - overlap
    if step <= 0:
        raise ValueError("Step size must be positive")

    windows = []
    for i in range(0, len(data) - window_size + 1, step):
        windows.append(data[i:i + window_size])
    return windows

def extract_features(windows):
    """
    Extract features from a list of windows.

    Args:
        windows: List of 1D numpy arrays

    Returns:
        features: 1D numpy array of extracted features [RMS, ZCR, WAMP, MAV]
    """
    if not windows:
        return np.array([0.0, 0.0, 0.0, 0.0])

    rms_values = [extract_rms(w) for w in windows]
    zcr_values = [extract_zcr(w) for w in windows]
    wamp_values = [extract_wamp(w) for w in windows]
    mav_values = [extract_mav(w) for w in windows]

    return np.array([
        np.mean(rms_values),
        np.mean(zcr_values),
        np.mean(wamp_values),
        np.mean(mav_values)
    ])

def check_skewed_valence(valence_scores, threshold=5.0):
    """
    Check if valence scores are skewed (all > threshold or all < threshold).

    Args:
        valence_scores: Array of valence scores
        threshold: Valence threshold (default 5.0)

    Returns:
        is_skewed: Boolean indicating if scores are skewed
        reason: String explaining the skew if detected
    """
    if len(valence_scores) == 0:
        return False, "No valence scores available"

    all_above = np.all(valence_scores > threshold)
    all_below = np.all(valence_scores < threshold)

    if all_above:
        return True, f"All valence scores ({len(valence_scores)}) are > {threshold}"
    elif all_below:
        return True, f"All valence scores ({len(valence_scores)}) are < {threshold}"

    return False, "Valence scores are balanced"

def impute_missing_channels(subject_data: pd.DataFrame, channel_names: List[str]) -> Tuple[pd.DataFrame, bool, str]:
    """
    Impute missing values in EMG channels using a median filter.
    If a channel has too many missing values, the subject is marked for exclusion.

    Args:
        subject_data: DataFrame containing the subject's EMG data
        channel_names: List of channel column names to check

    Returns:
        imputed_data: DataFrame with missing values imputed
        should_exclude: Boolean indicating if subject should be excluded
        exclusion_reason: String explaining why the subject was excluded (if applicable)
    """
    logger.info(f"Checking for missing channels in subject data with columns: {channel_names}")
    imputed_data = subject_data.copy()
    should_exclude = False
    exclusion_reason = ""

    missing_channels = []
    for col in channel_names:
        if col not in imputed_data.columns:
            missing_channels.append(col)
            continue

        missing_mask = imputed_data[col].isna()
        missing_fraction = missing_mask.sum() / len(imputed_data)

        if missing_fraction > MISSING_THRESHOLD:
            should_exclude = True
            exclusion_reason = f"Channel '{col}' has {missing_fraction:.2%} missing data (>{MISSING_THRESHOLD:.0%} threshold)"
            logger.warning(f"Exclusion triggered: {exclusion_reason}")
            return imputed_data, should_exclude, exclusion_reason

        if missing_mask.any():
            # Apply median filter for imputation
            logger.info(f"Imputing missing values in channel '{col}' using median filter")
            imputed_data[col] = imputed_data[col].fillna(imputed_data[col].median())

    if missing_channels:
        should_exclude = True
        exclusion_reason = f"Missing channels: {', '.join(missing_channels)}"
        logger.warning(f"Exclusion triggered: {exclusion_reason}")

    return imputed_data, should_exclude, exclusion_reason

def process_subject_signals(raw_data: pd.DataFrame, fs: int, baseline_duration: float = 2.0) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Process raw EMG signals for a single subject: filter, baseline correct, window, and extract features.

    Args:
        raw_data: DataFrame with raw EMG data
        fs: Sampling frequency (Hz)
        baseline_duration: Duration of pre-stimulus baseline in seconds

    Returns:
        features_dict: Dictionary of extracted features per channel, or None if processing failed
        error_msg: Error message if processing failed, or None
    """
    try:
        # Determine baseline indices
        baseline_samples = int(baseline_duration * fs)
        if baseline_samples > len(raw_data):
            baseline_samples = len(raw_data)
        baseline_indices = list(range(baseline_samples))

        features_dict = {}
        channel_names = [f"EMG_{ch}" for ch in ['corrugator', 'zygomaticus', 'orbicularis']]

        # Check for missing channels first
        imputed_data, should_exclude, exclusion_reason = impute_missing_channels(raw_data, channel_names)
        if should_exclude:
            return None, exclusion_reason

        for muscle, channel_idx in EMG_CHANNELS.items():
            channel_col = f"EMG_{muscle}"
            if channel_col not in imputed_data.columns:
                continue

            signal = imputed_data[channel_col].values

            # Apply filters
            filtered_signal = apply_bandpass_filter(signal, 20, 450, fs)
            filtered_signal = apply_notch_filter(filtered_signal, 50, fs)  # Default to 50Hz, can be parameterized

            # Baseline correct
            corrected_signal = baseline_correct(filtered_signal, baseline_indices)

            # Create windows (1 second windows, non-overlapping)
            window_size = fs  # 1 second
            windows = create_windows(corrected_signal, window_size, overlap=0)

            # Extract features for each window
            if windows:
                features = extract_features(windows)
                features_dict[muscle] = {
                    'rms': features[0],
                    'zcr': features[1],
                    'wamp': features[2],
                    'mav': features[3]
                }

        return features_dict, None

    except Exception as e:
        logger.error(f"Error processing subject signals: {str(e)}")
        return None, str(e)

def preprocess_all_subjects(raw_data_path: str, output_path: str, fs: int = 512):
    """
    Preprocess all subjects in the dataset and save results.
    Also generates the exclusions log.

    Args:
        raw_data_path: Path to the raw dataset
        output_path: Path to save processed features
        fs: Sampling frequency (Hz)
    """
    logger.info(f"Starting preprocessing of data from {raw_data_path}")

    # Load raw data
    try:
        raw_data = pd.read_csv(raw_data_path)
    except Exception as e:
        logger.error(f"Failed to load raw data: {str(e)}")
        raise

    processed_features = []
    exclusions = []
    skewed_subjects = []

    # Iterate over subjects (assuming data is structured with subject_id column)
    # This is a simplified example; actual implementation depends on data structure
    subject_ids = raw_data['subject_id'].unique() if 'subject_id' in raw_data.columns else range(1, 33)

    for subject_id in subject_ids:
        logger.info(f"Processing subject {subject_id}")

        # Get subject data
        if 'subject_id' in raw_data.columns:
            subject_data = raw_data[raw_data['subject_id'] == subject_id]
        else:
            # Assume data is ordered by subject
            start_idx = (subject_id - 1) * 1280  # Example: 1280 samples per subject
            end_idx = subject_id * 1280
            subject_data = raw_data.iloc[start_idx:end_idx]

        if len(subject_data) == 0:
            logger.warning(f"No data found for subject {subject_id}")
            continue

        # Check for skewed valence
        if 'valence' in subject_data.columns:
            is_skewed, skew_reason = check_skewed_valence(subject_data['valence'].values)
            if is_skewed:
                skewed_subjects.append({
                    'subject_id': subject_id,
                    'reason': skew_reason
                })
                logger.info(f"Subject {subject_id} has skewed valence: {skew_reason}")
                # Exclude from training, but keep for testing if valid

        # Process signals
        features_dict, error_msg = process_subject_signals(subject_data, fs)

        if error_msg:
            exclusions.append({
                'subject_id': subject_id,
                'reason': error_msg,
                'type': 'missing_channels'
            })
            logger.warning(f"Subject {subject_id} excluded: {error_msg}")
            continue

        if features_dict:
          # Combine features with subject metadata
          subject_features = {
              'subject_id': subject_id,
              'features': features_dict
          }
          processed_features.append(subject_features)

    # Save processed features
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            import pickle
            pickle.dump(processed_features, f)
        logger.info(f"Processed features saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save processed features: {str(e)}")
        raise

    # Write exclusions log
    exclusions_log_path = str(Path(output_path).parent / 'exclusions.log')
    try:
        with open(exclusions_log_path, 'w') as f:
            f.write(f"# Exclusions Log - Generated {pd.Timestamp.now()}\n")
            f.write(f"# Format: subject_id, reason, type\n")
            f.write(f"# Note: Skewed valence subjects are excluded from training only.\n\n")

            for exc in exclusions:
                f.write(f"{exc['subject_id']}, {exc['reason']}, {exc['type']}\n")

            if skewed_subjects:
                f.write("\n# Skewed Valence Subjects (excluded from training only)\n")
                for skew in skewed_subjects:
                    f.write(f"{skew['subject_id']}, {skew['reason']}, skewed_valence\n")

        logger.info(f"Exclusions log saved to {exclusions_log_path}")
    except Exception as e:
        logger.error(f"Failed to write exclusions log: {str(e)}")
        raise

def main():
    """Main entry point for preprocessing."""
    config = get_config_summary()
    raw_data_path = config.get('data_paths', {}).get('raw', 'data/raw/deap_processed.csv')
    output_path = config.get('data_paths', {}).get('processed', 'data/processed/features.pkl')
    fs = config.get('dataset', {}).get('fs', 512)

    if not os.path.exists(raw_data_path):
        logger.error(f"Raw data file not found: {raw_data_path}")
        logger.info("Please run download.py first to fetch the dataset.")
        return

    preprocess_all_subjects(raw_data_path, output_path, fs)
    logger.info("Preprocessing completed successfully.")

if __name__ == "__main__":
    main()