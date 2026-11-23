"""
Preprocessing module for Sleep-EDF SC data.

Implements:
- Linear interpolation for missing data
- Bandpass filtering (0.5–45 Hz)
- Notch filtering (50/60 Hz)
- Segmentation into 30s epochs and 60s transition windows
"""

import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from scipy import signal
from scipy.interpolate import interp1d

# Import config and logging utilities from existing project modules
from src.utils.config import get_paths, get_data_config
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Constants derived from config or defaults
DEFAULT_SAMPLING_RATE = 100  # Hz, typical for Sleep-EDF SC
BANDPASS_LOW = 0.5
BANDPASS_HIGH = 45.0
NOTCH_FREQS = [50, 60]  # Hz
EPOCH_DURATION_S = 30
TRANSITION_WINDOW_DURATION_S = 60


def linear_interpolate_missing(
    data: np.ndarray,
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
    max_gap_samples: Optional[int] = None
) -> np.ndarray:
    """
    Fill missing data (NaNs) using linear interpolation.

    Args:
        data: 1D or 2D array (channels x samples). NaNs indicate missing data.
        sampling_rate: Sampling rate in Hz.
        max_gap_samples: Maximum gap size (in samples) to interpolate.
                         Gaps larger than this are left as NaN.
                         If None, no limit is applied.

    Returns:
        Interpolated array (same shape as input).
    """
    if data.ndim == 1:
        data = data[np.newaxis, :]

    n_channels, n_samples = data.shape
    result = np.zeros_like(data)

    for ch in range(n_channels):
        ch_data = data[ch, :]
        valid_mask = ~np.isnan(ch_data)
        if np.all(valid_mask):
            result[ch, :] = ch_data
            continue
        if not np.any(valid_mask):
            logger.warning(f"Channel {ch} is entirely NaN. Leaving as NaN.")
            result[ch, :] = ch_data
            continue

        # Indices of valid data
        valid_indices = np.where(valid_mask)[0]

        # Create interpolation function
        f_interp = interp1d(
            valid_indices,
            ch_data[valid_mask],
            kind='linear',
            bounds_error=False,
            fill_value=np.nan
        )

        # Interpolate all points
        interpolated = f_interp(np.arange(n_samples))

        # Apply max_gap constraint if specified
        if max_gap_samples is not None:
            # Identify gaps (sequences of NaNs)
            gap_mask = ~valid_mask
            # Find start and end of each gap
            diff = np.diff(gap_mask.astype(int))
            gap_starts = np.where(diff == 1)[0] + 1
            gap_ends = np.where(diff == -1)[0] + 1
            if gap_mask[0]:
                gap_starts = np.insert(gap_starts, 0, 0)
            if gap_mask[-1]:
                gap_ends = np.append(gap_ends, n_samples)

            # Filter gaps larger than max_gap
            for start, end in zip(gap_starts, gap_ends):
                gap_len = end - start
                if gap_len > max_gap_samples:
                    interpolated[start:end] = np.nan

        result[ch, :] = interpolated

    return result.squeeze()


def bandpass_filter(
    data: np.ndarray,
    lowcut: float = BANDPASS_LOW,
    highcut: float = BANDPASS_HIGH,
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
    order: int = 4
) -> np.ndarray:
    """
    Apply a Butterworth bandpass filter.

    Args:
        data: 1D or 2D array (channels x samples).
        lowcut: Lower cutoff frequency (Hz).
        highcut: Upper cutoff frequency (Hz).
        sampling_rate: Sampling rate in Hz.
        order: Filter order.

    Returns:
        Filtered array (same shape as input).
    """
    nyquist = 0.5 * sampling_rate
    low = lowcut / nyquist
    high = highcut / nyquist

    # Ensure cutoffs are within valid range
    if low >= high or low <= 0 or high >= 1:
        raise ValueError(f"Invalid bandpass cutoffs: {lowcut}-{highcut} Hz at {sampling_rate} Hz sampling rate.")

    b, a = signal.butter(order, [low, high], btype='band')

    if data.ndim == 1:
        data = data[np.newaxis, :]

    n_channels, n_samples = data.shape
    result = np.zeros_like(data)

    for ch in range(n_channels):
        # Use filtfilt for zero-phase filtering
        result[ch, :] = signal.filtfilt(b, a, data[ch, :], padlen=min(3 * len(a), n_samples - 1))

    return result.squeeze()


def notch_filter(
    data: np.ndarray,
    freqs: List[float] = NOTCH_FREQS,
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
    q: float = 30.0
) -> np.ndarray:
    """
    Apply a notch filter to remove line noise.

    Args:
        data: 1D or 2D array (channels x samples).
        freqs: List of frequencies to notch (Hz).
        sampling_rate: Sampling rate in Hz.
        q: Quality factor. Higher Q means narrower notch.

    Returns:
        Filtered array (same shape as input).
    """
    if data.ndim == 1:
        data = data[np.newaxis, :]

    n_channels, n_samples = data.shape
    result = data.copy()

    for freq in freqs:
        nyquist = 0.5 * sampling_rate
        if freq >= nyquist:
            logger.warning(f"Notch frequency {freq} Hz is >= Nyquist {nyquist} Hz. Skipping.")
            continue

        w0 = freq / nyquist
        b, a = signal.iirnotch(w0, q)

        for ch in range(n_channels):
            result[ch, :] = signal.filtfilt(b, a, result[ch, :], padlen=min(3 * len(a), n_samples - 1))

    return result.squeeze()


def preprocess_signal(
    data: np.ndarray,
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
    apply_interpolation: bool = True,
    apply_bandpass: bool = True,
    apply_notch: bool = True,
    max_gap_samples: Optional[int] = None
) -> np.ndarray:
    """
    Apply full preprocessing pipeline to a signal.

    Order: Interpolation -> Notch -> Bandpass

    Args:
        data: 1D or 2D array (channels x samples).
        sampling_rate: Sampling rate in Hz.
        apply_interpolation: Whether to interpolate missing data.
        apply_bandpass: Whether to apply bandpass filter.
        apply_notch: Whether to apply notch filter.
        max_gap_samples: Max gap size for interpolation (if applicable).

    Returns:
        Preprocessed signal.
    """
    if data.ndim == 1:
        data = data[np.newaxis, :]

    result = data.copy()

    if apply_interpolation:
        logger.debug("Applying linear interpolation for missing data.")
        result = linear_interpolate_missing(result, sampling_rate, max_gap_samples)

    if apply_notch:
        logger.debug("Applying notch filter.")
        result = notch_filter(result, sampling_rate=sampling_rate)

    if apply_bandpass:
        logger.debug("Applying bandpass filter.")
        result = bandpass_filter(result, sampling_rate=sampling_rate)

    return result.squeeze()


def segment_into_epochs(
    data: np.ndarray,
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
    epoch_duration_s: int = EPOCH_DURATION_S,
    labels: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Segment continuous data into fixed-duration epochs.

    Args:
        data: 2D array (channels x total_samples).
        sampling_rate: Sampling rate in Hz.
        epoch_duration_s: Duration of each epoch in seconds.
        labels: Optional 1D array of stage labels (one per epoch).
                If provided, must match the number of epochs.

    Returns:
        Tuple of (epochs, labels):
            epochs: 3D array (n_epochs, channels, samples_per_epoch)
            labels: 1D array of stage labels (if provided)
    """
    n_channels, n_samples = data.shape
    samples_per_epoch = int(epoch_duration_s * sampling_rate)
    n_epochs = n_samples // samples_per_epoch

    if n_epochs == 0:
        raise ValueError(f"Data length ({n_samples} samples) is shorter than epoch duration ({samples_per_epoch} samples).")

    # Truncate data to fit exact number of epochs
    truncated_samples = n_epochs * samples_per_epoch
    data_truncated = data[:, :truncated_samples]

    # Reshape to (n_epochs, channels, samples_per_epoch)
    epochs = data_truncated.reshape(n_epochs, n_channels, samples_per_epoch)

    if labels is not None:
        if len(labels) != n_epochs:
            raise ValueError(f"Number of labels ({len(labels)}) does not match number of epochs ({n_epochs}).")
        return epochs, labels

    return epochs, None


def extract_transition_windows(
    data: np.ndarray,
    hypnogram: np.ndarray,
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
    window_duration_s: int = TRANSITION_WINDOW_DURATION_S,
    center_on_change: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract windows centered on hypnogram stage changes.

    Args:
        data: 2D array (channels x total_samples).
        hypnogram: 1D array of stage labels (one per 30s epoch).
        sampling_rate: Sampling rate in Hz.
        window_duration_s: Duration of the transition window in seconds.
        center_on_change: If True, center the window on the change point.
                         If False, window ends at the change point (pre-transition).
                         Note: For T014 (centered), this should be True.
                            For T014b (pre-transition), this should be False.

    Returns:
        Tuple of (windows, change_indices, labels):
            windows: 3D array (n_transitions, channels, samples_per_window)
            change_indices: 1D array of sample indices where transitions occur
            labels: 1D array of (from_stage, to_stage) tuples for each transition
    """
    n_channels, n_samples = data.shape
    samples_per_epoch = int(30 * sampling_rate)  # Hypnogram is 30s epochs
    window_samples = int(window_duration_s * sampling_rate)

    # Find indices where hypnogram changes
    transitions = np.where(hypnogram[:-1] != hypnogram[1:])[0]

    if len(transitions) == 0:
        logger.info("No transitions found in hypnogram.")
        return np.empty((0, n_channels, window_samples)), np.array([]), np.array([])

    windows_list = []
    change_indices_list = []
    labels_list = []

    for t_idx in transitions:
        # t_idx is the epoch index where the change occurs (hypnogram[t_idx] -> hypnogram[t_idx+1])
        # Sample index of the change (start of the new epoch)
        change_sample = (t_idx + 1) * samples_per_epoch

        # Determine window boundaries
        if center_on_change:
            # Center window on change_sample
            start_sample = change_sample - window_samples // 2
            end_sample = start_sample + window_samples
        else:
            # For pre-transition (T014b): window ends 30s BEFORE the change
            # Change occurs at change_sample. We want window ending at change_sample - samples_per_epoch
            end_sample = change_sample - samples_per_epoch
            start_sample = end_sample - window_samples

        # Check bounds
        if start_sample < 0 or end_sample > n_samples:
            logger.warning(f"Transition window at sample {change_sample} out of bounds. Skipping.")
            continue

        # Extract window
        window = data[:, start_sample:end_sample]
        windows_list.append(window)

        # Record change index (for reference)
        change_indices_list.append(change_sample)

        # Record labels: (from_stage, to_stage)
        labels_list.append((hypnogram[t_idx], hypnogram[t_idx + 1]))

    if len(windows_list) == 0:
        logger.warning("No valid transition windows could be extracted.")
        return np.empty((0, n_channels, window_samples)), np.array([]), np.array([])

    windows = np.stack(windows_list)
    change_indices = np.array(change_indices_list)
    # labels as object array of tuples
    labels = np.array(labels_list, dtype=object)

    return windows, change_indices, labels


def extract_pre_transition_windows(
    data: np.ndarray,
    hypnogram: np.ndarray,
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
    window_duration_s: int = 60,
    gap_before_transition_s: int = 30
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Extract windows that end `gap_before_transition_s` seconds BEFORE a stage change.
    This avoids tautology by ensuring the window does not contain the transition itself.

    Args:
        data: 2D array (channels x total_samples).
        hypnogram: 1D array of stage labels (one per 30s epoch).
        sampling_rate: Sampling rate in Hz.
        window_duration_s: Duration of the input window in seconds.
        gap_before_transition_s: Seconds before the transition where the window ends.

    Returns:
        Tuple of (windows, change_indices, labels):
            windows: 3D array (n_transitions, channels, samples_per_window)
            change_indices: 1D array of sample indices where transitions occur
            labels: 1D array of (from_stage, to_stage) tuples for each transition
    """
    n_channels, n_samples = data.shape
    samples_per_epoch = int(30 * sampling_rate)
    window_samples = int(window_duration_s * sampling_rate)
    gap_samples = int(gap_before_transition_s * sampling_rate)

    # Find indices where hypnogram changes
    transitions = np.where(hypnogram[:-1] != hypnogram[1:])[0]

    if len(transitions) == 0:
        logger.info("No transitions found in hypnogram.")
        return np.empty((0, n_channels, window_samples)), np.array([]), np.array([])

    windows_list = []
    change_indices_list = []
    labels_list = []

    for t_idx in transitions:
        change_sample = (t_idx + 1) * samples_per_epoch

        # Window ends `gap_samples` before the change
        end_sample = change_sample - gap_samples
        start_sample = end_sample - window_samples

        # Check bounds
        if start_sample < 0 or end_sample > n_samples:
            logger.warning(f"Pre-transition window at sample {change_sample} out of bounds. Skipping.")
            continue

        window = data[:, start_sample:end_sample]
        windows_list.append(window)
        change_indices_list.append(change_sample)
        labels_list.append((hypnogram[t_idx], hypnogram[t_idx + 1]))

    if len(windows_list) == 0:
        logger.warning("No valid pre-transition windows could be extracted.")
        return np.empty((0, n_channels, window_samples)), np.array([]), np.array([])

    windows = np.stack(windows_list)
    change_indices = np.array(change_indices_list)
    labels = np.array(labels_list, dtype=object)

    return windows, change_indices, labels


def preprocess_subject(
    subject_data: np.ndarray,
    hypnogram: np.ndarray,
    subject_id: str,
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
    output_dir: Optional[Union[str, Path]] = None,
    save_epochs: bool = True,
    save_transitions: bool = True,
    save_pre_transitions: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    Preprocess a single subject's data and optionally save results.

    Args:
        subject_data: 2D array (channels x samples).
        hypnogram: 1D array of stage labels (one per 30s epoch).
        subject_id: Subject identifier.
        sampling_rate: Sampling rate in Hz.
        output_dir: Directory to save outputs (if provided).
        save_epochs: Whether to save 30s stable epochs.
        save_transitions: Whether to save 60s centered transition windows.
        save_pre_transitions: Whether to save 60s pre-transition windows (for T014b).

    Returns:
        Dictionary of DataFrames containing processed data.
    """
    logger.info(f"Preprocessing subject {subject_id}")

    # Preprocess signal
    preprocessed_data = preprocess_signal(subject_data, sampling_rate=sampling_rate)

    results = {}

    # Segment into 30s epochs
    epochs, epoch_labels = segment_into_epochs(preprocessed_data, sampling_rate, epoch_duration_s=30)
    n_epochs = epochs.shape[0]

    # Create epoch-level metadata
    epoch_metadata = pd.DataFrame({
        'subject_id': [subject_id] * n_epochs,
        'epoch_index': range(n_epochs),
        'stage': epoch_labels if epoch_labels is not None else [np.nan] * n_epochs,
        'is_stable': [True] * n_epochs  # Stable by definition for 30s epochs in this context
    })

    results['epochs'] = pd.concat([
        epoch_metadata,
        pd.DataFrame(epochs.reshape(n_epochs, -1))  # Flatten channels x samples
    ], axis=1)

    if save_transitions:
        trans_windows, trans_indices, trans_labels = extract_transition_windows(
            preprocessed_data, hypnogram, sampling_rate, window_duration_s=60, center_on_change=True
        )
        n_trans = len(trans_windows)
        if n_trans > 0:
            trans_metadata = pd.DataFrame({
                'subject_id': [subject_id] * n_trans,
                'transition_index': range(n_trans),
                'change_sample_index': trans_indices,
                'from_stage': [l[0] for l in trans_labels],
                'to_stage': [l[1] for l in trans_labels],
                'is_transition': [True] * n_trans
            })
            results['transition_windows'] = pd.concat([
                trans_metadata,
                pd.DataFrame(trans_windows.reshape(n_trans, -1))
            ], axis=1)

    if save_pre_transitions:
        pre_trans_windows, pre_trans_indices, pre_trans_labels = extract_pre_transition_windows(
            preprocessed_data, hypnogram, sampling_rate, window_duration_s=60, gap_before_transition_s=30
        )
        n_pre_trans = len(pre_trans_windows)
        if n_pre_trans > 0:
            pre_trans_metadata = pd.DataFrame({
                'subject_id': [subject_id] * n_pre_trans,
                'pre_transition_index': range(n_pre_trans),
                'change_sample_index': pre_trans_indices,
                'from_stage': [l[0] for l in pre_trans_labels],
                'to_stage': [l[1] for l in pre_trans_labels],
                'is_pre_transition': [True] * n_pre_trans
            })
            results['pre_transition_windows'] = pd.concat([
                pre_trans_metadata,
                pd.DataFrame(pre_trans_windows.reshape(n_pre_trans, -1))
            ], axis=1)

    # Save to disk if output_dir provided
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for key, df in results.items():
            file_path = output_dir / f"{subject_id}_{key}.parquet"
            df.to_parquet(file_path, index=False)
            logger.info(f"Saved {key} for {subject_id} to {file_path}")

    return results


def main():
    """
    Main entry point for preprocessing.
    This function is intended to be called by a pipeline script.
    """
    paths = get_paths()
    data_config = get_data_config()

    raw_dir = paths['data_raw']
    processed_dir = paths['data_processed']

    logger.info(f"Starting preprocessing. Raw data: {raw_dir}, Output: {processed_dir}")

    # Example: Process a specific subject if arguments are provided
    # In a real pipeline, this would iterate over all subjects
    # For now, we log the configuration
    logger.info(f"Sampling rate: {DEFAULT_SAMPLING_RATE} Hz")
    logger.info(f"Bandpass: {BANDPASS_LOW}-{BANDPASS_HIGH} Hz")
    logger.info(f"Notch: {NOTCH_FREQS} Hz")

    # Note: Actual processing of files is done by calling preprocess_subject
    # This main function serves as a placeholder for CLI or pipeline integration.
    logger.info("Preprocessing module ready. Call preprocess_subject() for actual data processing.")


if __name__ == "__main__":
    main()