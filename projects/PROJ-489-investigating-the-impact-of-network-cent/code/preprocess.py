import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import mne
from scipy.signal import butter, filtfilt

from config_utils import load_config
from loaders import load_raw_edf, load_annotations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def bandpass_filter(
    data: np.ndarray,
    sfreq: float,
    lowcut: float,
    highcut: float,
    order: int = 4,
) -> np.ndarray:
    """
    Apply a band-pass filter to the data.

    Args:
        data: Input signal array (channels x time).
        sfreq: Sampling frequency in Hz.
        lowcut: Low cutoff frequency in Hz.
        highcut: High cutoff frequency in Hz.
        order: Order of the Butterworth filter.

    Returns:
        Filtered signal array.
    """
    nyq = 0.5 * sfreq
    low = lowcut / nyq
    high = highcut / nyq

    b, a = butter(order, [low, high], btype="band")
    filtered_data = filtfilt(b, a, data, axis=-1)
    return filtered_data


def compute_kurtosis(data: np.ndarray) -> float:
    """Compute the kurtosis of the data."""
    n = len(data)
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 0.0
    kurtosis = np.sum(((data - mean) / std) ** 4) / n
    return kurtosis


def compute_high_freq_power(
    data: np.ndarray, sfreq: float, high_freq_start: float = 30.0
) -> float:
    """
    Compute the power in the high-frequency range.

    Args:
        data: Input signal array.
        sfreq: Sampling frequency.
        high_freq_start: Start of high-frequency band.

    Returns:
        Power in the high-frequency band.
    """
    from scipy.signal import welch

    f, pxx = welch(data, sfreq, nperseg=min(256, len(data)))
    high_freq_mask = f >= high_freq_start
    if np.any(high_freq_mask):
        return np.mean(pxx[high_freq_mask])
    return 0.0


def remove_ica_artifacts(
    raw: mne.io.BaseRaw,
    kurtosis_threshold: float = 5.0,
    high_freq_multiplier: float = 3.0,
) -> mne.io.BaseRaw:
    """
    Identify and remove ICA components with high kurtosis or high-frequency power.

    Args:
        raw: MNE Raw object.
        kurtosis_threshold: Threshold for kurtosis.
        high_freq_multiplier: Multiplier for baseline high-freq power.

    Returns:
        Raw object with artifacts removed.
    """
    logger.info("Running ICA to identify artifacts...")
    ica = mne.preprocessing.ICA(n_components=0.95, random_state=42, method="fastica")
    ica.fit(raw)

    # Estimate baseline high-freq power
    baseline_powers = []
    for ch in raw.get_data():
        baseline_powers.append(compute_high_freq_power(ch, raw.info["sfreq"]))
    baseline_mean_power = np.mean(baseline_powers)

    components_to_drop = []
    for idx, evoked in enumerate(ica.get_components().values()):
        # Check kurtosis
        kurt = compute_kurtosis(evoked)
        if kurt > kurtosis_threshold:
            components_to_drop.append(idx)
            logger.info(f"Component {idx} flagged by kurtosis: {kurt:.2f}")
            continue

        # Check high-freq power
        comp_power = compute_high_freq_power(evoked, raw.info["sfreq"])
        if comp_power > high_freq_multiplier * baseline_mean_power:
            components_to_drop.append(idx)
            logger.info(f"Component {idx} flagged by high-freq power: {comp_power:.2f}")

    if components_to_drop:
        logger.info(f"Dropping components: {components_to_drop}")
        ica.exclude = components_to_drop
        raw = ica.apply(raw)
    else:
        logger.info("No artifacts detected by ICA criteria.")

    return raw


def epoch_data(
    raw: mne.io.BaseRaw,
    annotations: List[Dict],
    epoch_duration: float = 30.0,
) -> Tuple[np.ndarray, List[str]]:
    """
    Segment data into epochs labeled by sleep stage.

    Args:
        raw: Preprocessed MNE Raw object.
        annotations: List of annotation dicts with 'onset', 'duration', 'description'.
        epoch_duration: Duration of each epoch in seconds.

    Returns:
        Tuple of (epochs_data, labels).
    """
    events = []
    event_id = {}

    # Convert annotations to events
    for ann in annotations:
        onset = ann["onset"]
        duration = ann["duration"]
        label = ann["description"]

        if label not in event_id:
            event_id[label] = len(event_id)

        # Create events at the start of each annotation
        events.append([int(onset * raw.info["sfreq"]), 0, event_id[label]])

    events = np.array(events)
    epochs = mne.Epochs(
        raw,
        events,
        event_id=event_id,
        tmin=0.0,
        tmax=epoch_duration - 1.0 / raw.info["sfreq"],
        baseline=None,
        preload=True,
        verbose=False,
    )

    epochs_data = epochs.get_data()
    labels = [event_id[k] for k in event_id.keys()]

    return epochs_data, labels


def validate_no_nan(data: np.ndarray) -> bool:
    """Check if there are any NaN values in the data."""
    return not np.any(np.isnan(data))


def main():
    """Main function to run the preprocessing pipeline."""
    config = load_config()
    logger.info("Starting preprocessing pipeline...")

    # Load parameters
    lowcut = config["signal_processing"]["filter"]["lowcut"]
    highcut = config["signal_processing"]["filter"]["highcut"]
    kurtosis_threshold = config["signal_processing"]["ica"]["kurtosis_threshold"]
    high_freq_multiplier = config["signal_processing"]["ica"]["high_freq_multiplier"]
    epoch_duration = config["signal_processing"]["epoching"]["duration"]

    raw_dir = Path(config["paths"]["raw"])
    processed_dir = Path(config["paths"]["processed"])
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Iterate over subject files
    edf_files = list(raw_dir.glob("*.edf"))
    if not edf_files:
        logger.warning("No .edf files found in data/raw. Skipping preprocessing.")
        return

    for edf_file in edf_files:
        logger.info(f"Processing {edf_file.name}...")
        try:
            # Load raw data
            raw = load_raw_edf(edf_file)

            # Band-pass filter
            logger.info(f"Applying band-pass filter ({lowcut}-{highcut} Hz)...")
            raw.filter(lowcut, highcut, method="iir")

            # ICA artifact removal
            logger.info("Removing ICA artifacts...")
            raw = remove_ica_artifacts(
                raw,
                kurtosis_threshold=kurtosis_threshold,
                high_freq_multiplier=high_freq_multiplier,
            )

            # Load annotations
            annotations = load_annotations(edf_file)

            # Epoch data
            logger.info("Epoching data...")
            epochs_data, labels = epoch_data(raw, annotations, epoch_duration)

            # Validate no NaNs
            if not validate_no_nan(epochs_data):
                logger.error(f"NaN values detected in {edf_file.name}. Skipping save.")
                continue

            # Save preprocessed data
            output_path = processed_dir / f"{edf_file.stem}_epochs.npz"
            np.savez_compressed(
                output_path,
                data=epochs_data,
                labels=labels,
                sfreq=raw.info["sfreq"],
            )
            logger.info(f"Saved preprocessed data to {output_path}")

        except Exception as e:
            logger.error(f"Error processing {edf_file.name}: {e}")
            continue

    logger.info("Preprocessing pipeline completed.")


if __name__ == "__main__":
    main()
