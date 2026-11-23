import json
import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import mne
from scipy.signal import butter, filtfilt

from config_utils import load_config
from loaders import load_raw_edf, load_annotations
from llmxive_toolkit import paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Existing helper functions (kept for internal use)
# ----------------------------------------------------------------------
def bandpass_filter(
    data: np.ndarray,
    sfreq: float,
    lowcut: float,
    highcut: float,
    order: int = 4,
) -> np.ndarray:
    """
    Apply a Butterworth band‑pass filter to a NumPy array.
    """
    nyq = 0.5 * sfreq
    low = lowcut / nyq
    high = highcut / nyq

    b, a = butter(order, [low, high], btype="band")
    filtered_data = filtfilt(b, a, data, axis=-1)
    return filtered_data

def compute_kurtosis(data: np.ndarray) -> float:
    """Compute the kurtosis of a 1‑D signal."""
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
    Compute average power in the high‑frequency band (default ≥30 Hz).
    """
    from scipy.signal import welch

    f, pxx = welch(data, sfreq, nperseg=min(256, len(data)))
    high_freq_mask = f >= high_freq_start
    if np.any(high_freq_mask):
        return np.mean(pxx[high_freq_mask])
    return 0.0

# ----------------------------------------------------------------------
# Public API required by the task description
# ----------------------------------------------------------------------
def apply_bandpass_filter(raw: mne.io.BaseRaw, low: float = 0.5, high: float = 45.0) -> mne.io.BaseRaw:
    """
    Apply a band‑pass filter to an MNE ``Raw`` object.

    Parameters
    ----------
    raw : mne.io.BaseRaw
        The raw EEG data to filter.
    low : float, optional
        Low‑cut frequency in Hz (default 0.5).
    high : float, optional
        High‑cut frequency in Hz (default 45.0).

    Returns
    -------
    mne.io.BaseRaw
        A **copy** of the input Raw object with the filter applied.
    """
    logger.info(f"Applying band‑pass filter: {low}–{high} Hz")
    # ``filter`` works in‑place; we return a copy to keep the original untouched.
    raw_filt = raw.copy().filter(l_freq=low, h_freq=high, method="iir")
    return raw_filt

def remove_ica_artifacts(
    filtered: mne.io.BaseRaw,
    kurtosis_thr: float = 5.0,
    power_ratio_thr: float = 3.0,
) -> mne.io.BaseRaw:
    """
    Identify ICA components with excessive kurtosis **or** high‑frequency power
    and drop them.

    Parameters
    ----------
    filtered : mne.io.BaseRaw
        Band‑pass filtered Raw object.
    kurtosis_thr : float, optional
        Kurtosis threshold (default 5.0).
    power_ratio_thr : float, optional
        Ratio of component high‑frequency power to baseline (default 3.0).

    Returns
    -------
    mne.io.BaseRaw
        Raw object with flagged ICA components removed.
    """
    logger.info("Running ICA for artifact detection...")
    ica = mne.preprocessing.ICA(
        n_components=0.95, random_state=42, method="fastica"
    )
    ica.fit(filtered)

    # Baseline high‑frequency power (average across channels)
    baseline_powers = [
        compute_high_freq_power(ch, filtered.info["sfreq"])
        for ch in filtered.get_data()
    ]
    baseline_mean_power = np.mean(baseline_powers)

    components_to_drop: List[int] = []
    for idx, evoked in enumerate(ica.get_components().values()):
        # Kurtosis check
        kurt = compute_kurtosis(evoked)
        if kurt > kurtosis_thr:
            components_to_drop.append(idx)
            logger.info(f"Component {idx} flagged by kurtosis ({kurt:.2f})")
            continue

        # High‑frequency power check
        comp_power = compute_high_freq_power(evoked, filtered.info["sfreq"])
        if comp_power > power_ratio_thr * baseline_mean_power:
            components_to_drop.append(idx)
            logger.info(
                f"Component {idx} flagged by high‑freq power ({comp_power:.2f})"
            )

    if components_to_drop:
        logger.info(f"Dropping ICA components: {components_to_drop}")
        ica.exclude = components_to_drop
        filtered = ica.apply(filtered)
    else:
        logger.info("No ICA components met artifact criteria.")

    return filtered

def epoch_by_sleep_stage(
    cleaned: mne.io.BaseRaw,
    annotations,
    epoch_sec: float = 30.0,
) -> Tuple[np.ndarray, List[str]]:
    """
    Segment the cleaned Raw data into fixed‑length epochs labeled by sleep stage.

    Parameters
    ----------
    cleaned : mne.io.BaseRaw
        Pre‑processed Raw object (filter + ICA).
    annotations : mne.Annotations or ``None``
        Sleep‑stage annotations associated with the recording.
    epoch_sec : float, optional
        Desired epoch length in seconds (default 30 s).

    Returns
    -------
    tuple
        ``(epochs_data, labels)`` where ``epochs_data`` is a ``(n_epochs, n_channels, n_times)`` array
        and ``labels`` is a list of stage strings (e.g., ``'N2'``).
    """
    # Attach annotations to the Raw object if they are provided
    if annotations is not None:
        cleaned.set_annotations(annotations)

    # Convert annotations to events
    events, event_id = mne.events_from_annotations(
        cleaned, event_id=None, chunk_duration=epoch_sec
    )
    if len(events) == 0:
        logger.warning("No annotation‑derived events found; returning empty epoch set.")
        return np.empty((0, cleaned.info["nchan"], 0)), []

    # Build epochs
    epochs = mne.Epochs(
        cleaned,
        events,
        event_id=event_id,
        tmin=0.0,
        tmax=epoch_sec - 1.0 / cleaned.info["sfreq"],
        baseline=None,
        preload=True,
        verbose=False,
    )
    epochs_data = epochs.get_data()
    # Map integer event codes back to stage labels
    inv_map = {v: k for k, v in event_id.items()}
    labels = [inv_map[int(code)] for code in epochs.events[:, 2]]

    # ------------------------------------------------------------------
    # Save results to the prescribed locations
    # ------------------------------------------------------------------
    subject_id = cleaned.info.get("subject_info", {}).get("id", "unknown")
    epochs_path = paths.data("processed", f"epochs_{subject_id}.npz")
    metadata_path = paths.data("processed", f"metadata_{subject_id}.json")

    # Save epochs
    np.savez_compressed(
        epochs_path,
        data=epochs_data,
        labels=labels,
        sfreq=cleaned.info["sfreq"],
    )
    logger.info(f"Saved epochs to {epochs_path}")

    # Save minimal metadata (night IDs if present)
    meta = {
        "waking_night_id": cleaned.info.get("description", None),
        "sleep_night_id": cleaned.info.get("description", None),
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")

    return epochs_data, labels

def validate_no_nans(arr: np.ndarray) -> None:
    """
    Raise an error if any NaN values are present in the supplied array.

    The function also appends a status line to ``data/processed/validation_log.txt``.
    """
    if np.isnan(arr).any():
        log_path = paths.data("processed", "validation_log.txt")
        with open(log_path, "a", encoding="utf-8") as log_f:
            log_f.write(f"NaN detected in array at {Path.cwd()}\n")
        raise ValueError("NaN values detected in processed data.")
    else:
        log_path = paths.data("processed", "validation_log.txt")
        with open(log_path, "a", encoding="utf-8") as log_f:
            log_f.write("No NaN values detected.\n")

# ----------------------------------------------------------------------
# Existing ``main`` entry point – updated to use the new API
# ----------------------------------------------------------------------
def main():
    """Run the full preprocessing pipeline for all EDF files in ``data/raw``."""
    config = load_config()
    logger.info("Starting preprocessing pipeline...")

    # Load configuration parameters
    lowcut = config["signal_processing"]["filter"]["lowcut"]
    highcut = config["signal_processing"]["filter"]["highcut"]
    kurtosis_thr = config["signal_processing"]["ica"]["kurtosis_threshold"]
    power_ratio_thr = config["signal_processing"]["ica"]["high_freq_multiplier"]
    epoch_duration = config["signal_processing"]["epoching"]["duration"]

    raw_dir = Path(config["paths"]["raw"])
    processed_dir = Path(config["paths"]["processed"])
    processed_dir.mkdir(parents=True, exist_ok=True)

    edf_files = list(raw_dir.glob("*.edf"))
    if not edf_files:
        logger.warning("No .edf files found in data/raw. Skipping preprocessing.")
        return

    for edf_file in edf_files:
        logger.info(f"Processing {edf_file.name}...")
        try:
            # Load raw EDF (returns an MNE Raw object)
            raw = load_raw_edf(edf_file.parent.parent, edf_file.name)

            # Band‑pass filter
            raw_filt = apply_bandpass_filter(raw, lowcut, highcut)

            # ICA artifact removal
            raw_clean = remove_ica_artifacts(
                raw_filt,
                kurtosis_thr=kurtosis_thr,
                power_ratio_thr=power_ratio_thr,
            )

            # Load annotations (may be ``None``)
            annotations = load_annotations(
                edf_file.parent.parent,  # base_dir
                subject_id=edf_file.stem.split("-")[0],
                night_id=1,  # simplistic; real implementation would infer night
            )

            # Epoching
            epochs_data, labels = epoch_by_sleep_stage(
                raw_clean, annotations, epoch_sec=epoch_duration
            )

            # Validate NaNs
            validate_no_nans(epochs_data)

        except Exception as e:
            logger.error(f"Error processing {edf_file.name}: {e}")
            continue

    logger.info("Preprocessing pipeline completed.")

if __name__ == "__main__":
    main()
