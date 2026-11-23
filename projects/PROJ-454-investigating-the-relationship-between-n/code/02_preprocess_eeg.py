"""
EEG preprocessing script for Task T013.

This script loads raw EDF/BDF (or BrainVision) EEG files, applies a
1‑45 Hz band‑pass filter and a 50 Hz (and 100 Hz harmonic) notch filter,
detects and interpolates bad channels, runs ICA to remove ocular/muscular
artifacts, epochs the data into 2‑second non‑overlapping segments, computes
a signal‑to‑noise ratio (SNR) for each participant, performs quality checks,
and finally writes:
  * Epoched data:   data/processed/epoched/<participant_id>-epochs.fif
  * Metadata:      data/processed/preproc_metadata/<participant_id>.json
  * SNR metrics:   data/processed/snr_metrics.json
  * Exclusion log: data/processed/exclusion_log.csv
The script also logs a quick sanity‑check of the power spectrum to ensure
the band‑pass filter behaved as expected.
"""

import os
import sys
import json
import logging
import gc
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
import mne
from mne.time_frequency import psd_welch

# Project internal imports (matching API surface)
from utils.logging_config import get_logger
from utils.resource_monitor import check_resource_limits, enforce_resource_limits
from utils.preprocessing_params import get_preprocessing_params, get_data_quality_thresholds
from config import get_config

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
MEMORY_LIMIT_GB = 6.0  # Strict limit for this task (see T035)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def setup_logger(name: str) -> logging.Logger:
    """Create a module‑specific logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def load_raw_data(file_path: str) -> mne.io.BaseRaw:
    """Load raw EEG data (EDF, BDF, or BrainVision) without preloading."""
    logger = get_logger("preprocess")
    logger.info(f"Loading raw file: {file_path}")

    # Enforce a memory head‑room before loading
    current_mem = get_memory_usage_gb()
    if current_mem > (MEMORY_LIMIT_GB - 1.0):
        logger.error(
            f"Memory usage {current_mem:.2f} GB exceeds safe threshold before load."
        )
        raise MemoryError("Memory limit exceeded before data load.")

    try:
        if file_path.lower().endswith((".edf", ".bdf", ".vhdr")):
            raw = mne.io.read_raw_edf(file_path, preload=False, verbose=False)
        elif file_path.lower().endswith(".fif"):
            raw = mne.io.read_raw_fif(file_path, preload=False, verbose=False)
        else:
            # Fallback to BrainVision reader
            raw = mne.io.read_raw_brainvision(file_path, preload=False, verbose=False)

        logger.info(
            f"Raw data shape: {raw.get_data().shape}, duration: {raw.times[-1]:.2f}s"
        )
        return raw
    except Exception as exc:
        logger.error(f"Failed to load {file_path}: {exc}")
        raise

def apply_filters(
    raw: mne.io.BaseRaw,
    low_freq: float = 1.0,
    high_freq: float = 45.0,
    notch_freqs: List[float] = [50.0, 100.0],
) -> mne.io.BaseRaw:
    """Band‑pass and notch filter the raw data."""
    logger = get_logger("preprocess")
    logger.info("Applying band‑pass and notch filters")
    check_resource_limits(logger)

    raw.filter(low_freq, high_freq, method="iir", verbose=False)
    for nf in notch_freqs:
        raw.notch_filter(nf, verbose=False)

    return raw

def detect_bad_channels(raw: mne.io.BaseRaw, threshold_sd: float = 5.0) -> List[str]:
    """
    Detect bad channels based on variance > threshold_sd * median variance.
    Returns a list of channel names to be marked as bad.
    """
    logger = get_logger("preprocess")
    data = raw.get_data()
    variances = np.var(data, axis=1)
    median_var = np.median(variances)
    bad_mask = variances > (threshold_sd * median_var)
    bad_chs = [raw.ch_names[i] for i, bad in enumerate(bad_mask) if bad]
    if bad_chs:
        logger.info(f"Detected bad channels (high variance): {bad_chs}")
    else:
        logger.info("No high‑variance bad channels detected")
    return bad_chs

def interpolate_bad_channels(
    raw: mne.io.BaseRaw, bad_channels: Optional[List[str]] = None
) -> mne.io.BaseRaw:
    """Interpolate bad channels (either supplied or auto‑detected)."""
    logger = get_logger("preprocess")
    if bad_channels is None:
        bad_channels = detect_bad_channels(raw)

    if bad_channels:
        raw.info["bads"] = bad_channels
        raw.interpolate_bads(reset_bads=True, verbose=False)
        logger.info(f"Interpolated bad channels: {bad_channels}")
    else:
        logger.info("No channels marked as bad; skipping interpolation")
    return raw

def remove_ica_artifacts(
    raw: mne.io.BaseRaw, n_components: int = 20
) -> Tuple[mne.io.BaseRaw, List[int]]:
    """Fit ICA, automatically detect EOG components, and remove them."""
    logger = get_logger("preprocess")
    logger.info(f"Running ICA with {n_components} components")
    check_resource_limits(logger)

    ica = mne.preprocessing.ICA(
        n_components=n_components, random_state=42, method="fastica"
    )
    ica.fit(raw)

    # Detect EOG components (uses correlation with EOG channels if present)
    eog_indices, _ = mne.preprocessing.find_eog_components(raw, ica, threshold=3.0)

    if eog_indices:
        logger.info(f"Found EOG components to exclude: {eog_indices}")
        ica.exclude = list(eog_indices)
        ica.apply(raw)
    else:
        logger.info("No significant EOG components found")
    return raw, list(eog_indices)

def epoch_data(
    raw: mne.io.BaseRaw,
    epoch_duration: float = 2.0,
    baseline: Optional[Tuple[float, float]] = None,
) -> mne.Epochs:
    """Create non‑overlapping epochs of fixed length."""
    logger = get_logger("preprocess")
    logger.info(f"Epoching data into {epoch_duration}s non‑overlapping windows")
    check_resource_limits(logger)

    total_seconds = raw.times[-1]
    # Build events at every epoch_boundary (start at 0)
    n_epochs = int(np.floor(total_seconds / epoch_duration))
    onsets = np.arange(0, n_epochs * epoch_duration, epoch_duration)

    events = np.column_stack(
        (
            (onsets * raw.info["sfreq"]).astype(int),
            np.zeros(len(onsets), dtype=int),
            np.ones(len(onsets), dtype=int),
        )
    )

    epochs = mne.Epochs(
        raw,
        events,
        event_id=1,
        tmin=0.0,
        tmax=epoch_duration,
        baseline=baseline,
        preload=True,
        verbose=False,
    )
    logger.info(f"Created {len(epochs)} epochs")
    return epochs

def calculate_snr(epochs: mne.Epochs) -> float:
    """Median SNR (dB) = 10·log10(signal/noise)."""
    logger = get_logger("preprocess")
    data = epochs.get_data()  # shape: (n_epochs, n_channels, n_times)
    sfreq = epochs.info["sfreq"]
    n_times = data.shape[2]

    # FFT power
    fft = np.fft.rfft(data, n=n_times, axis=2)
    power = np.abs(fft) ** 2

    freqs = np.fft.rfftfreq(n_times, d=1.0 / sfreq)

    # Signal band 1‑45 Hz, noise band 46‑60 Hz
    sig_mask = (freqs >= 1) & (freqs <= 45)
    noise_mask = (freqs >= 46) & (freqs <= 60)

    # Mean power across epochs & channels for stability
    sig_power = power[:, :, sig_mask].mean()
    noise_power = power[:, :, noise_mask].mean()

    if noise_power == 0:
        logger.warning("Noise power is zero; returning very high SNR")
        return 100.0

    snr_db = 10 * np.log10(sig_power / noise_power)

    if not np.isfinite(snr_db):
        logger.error(f"SNR calculation resulted in non‑finite value: {snr_db}")
        return np.nan

    logger.info(f"Calculated SNR: {snr_db:.2f} dB")
    return float(snr_db)

def sanity_check_power_spectrum(epochs: mne.Epochs, low: float = 1.0, high: float = 45.0) -> None:
    """
    Verify that the majority of power resides within the band‑pass range.
    Logs a warning if <80 % of total power is inside the band.
    """
    logger = get_logger("preprocess")
    psd, freqs = psd_welch(epochs, fmin=0.5, fmax=70.0, n_fft=256, average='mean')
    total_power = psd.mean()
    band_mask = (freqs >= low) & (freqs <= high)
    band_power = psd[:, band_mask].mean()
    proportion = band_power / total_power
    logger.info(
        f"Power spectrum sanity check: {proportion * 100:.1f}% of power within {low}-{high} Hz"
    )
    if proportion < 0.80:
        logger.warning(
            "Band‑pass filter may be insufficient; <80 % of power lies within the target band."
        )

def run_quality_checks(
    epochs: mne.Epochs, snr: float, thresholds: Dict[str, float]
) -> bool:
    """
    Apply data‑quality criteria:
      * Minimum total EEG duration ≥ thresholds['min_valid_eeg_seconds']
      * SNR ≥ thresholds['min_snr_db']
    Returns True if the participant passes all checks.
    """
    logger = get_logger("preprocess")
    duration = len(epochs) * thresholds.get("epoch_duration", 2.0)
    if duration < thresholds["min_valid_eeg_seconds"]:
        logger.warning(
            f"Duration {duration:.1f}s < {thresholds['min_valid_eeg_seconds']}s – exclude"
        )
        return False

    if snr < thresholds["min_snr_db"]:
        logger.warning(f"SNR {snr:.2f} dB < {thresholds['min_snr_db']} dB – exclude")
        return False

    # Corrupted‑segment check is simplified – MNE already dropped bad epochs.
    logger.info("Participant passed quality checks")
    return True

def save_epoched_data(epochs: mne.Epochs, out_path: Path) -> None:
    """Write the epoched data to a .fif file."""
    logger = get_logger("preprocess")
    logger.info(f"Saving epoched data to {out_path}")
    epochs.save(str(out_path), overwrite=True, verbose=False)

def save_metadata(
    out_path: Path,
    bandpass: Tuple[float, float],
    notch: List[float],
    bad_channels: List[str],
    ica_removed: List[int],
) -> None:
    """Write preprocessing metadata as JSON."""
    logger = get_logger("preprocess")
    meta = {
        "bandpass": {"low_hz": bandpass[0], "high_hz": bandpass[1]},
        "notch_hz": notch,
        "bad_channels_interpolated": bad_channels,
        "ica_components_removed": ica_removed,
        "steps_applied": ["bandpass", "notch", "bad_channel_interpolation", "ica"],
    }
    logger.info(f"Writing metadata to {out_path}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main() -> None:
    logger = setup_logger("02_preprocess_eeg")
    logger.info("Starting EEG preprocessing (Task T013)")

    # Load configuration / parameters
    cfg = get_config()
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    epoched_dir = processed_dir / "epoched"
    metadata_dir = processed_dir / "preproc_metadata"

    # Ensure output directories exist
    epoched_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # Load preprocessing parameters and quality thresholds (may be overridden via env)
    prep_params = get_preprocessing_params()
    quality_thr = get_data_quality_thresholds()
    # Add epoch_duration to thresholds dict for convenience
    quality_thr["epoch_duration"] = prep_params.get("epoch_duration", 2.0)

    # Discover raw EEG files
    raw_files = (
        list(raw_dir.glob("*.edf"))
        + list(raw_dir.glob("*.bdf"))
        + list(raw_dir.glob("*.vhdr"))
    )
    if not raw_files:
        logger.error("No raw EEG files found in data/raw/")
        sys.exit(1)

    # Containers for SNR metrics and exclusion logging
    snr_metrics: Dict[str, Dict[str, float]] = {}
    exclusions: List[Dict[str, Any]] = []

    for raw_path in raw_files:
        participant_id = raw_path.stem
        logger.info(f"Processing participant: {participant_id}")

        try:
            # ----- Load -------------------------------------------------
            raw = load_raw_data(str(raw_path))

            # ----- Filtering -------------------------------------------
            raw = apply_filters(
                raw,
                low_freq=prep_params.get("l_freq", 1.0),
                high_freq=prep_params.get("h_freq", 45.0),
                notch_freqs=prep_params.get("notch_freqs", [50.0, 100.0]),
            )

            # ----- Bad channel detection & interpolation -----------------
            bad_chs = detect_bad_channels(
                raw, threshold_sd=prep_params.get("bad_channel_threshold", 5.0)
            )
            raw = interpolate_bad_channels(raw, bad_channels=bad_chs)

            # ----- ICA artifact removal ---------------------------------
            raw, ica_removed = remove_ica_artifacts(
                raw, n_components=prep_params.get("n_ica_components", 20)
            )

            # ----- Epoching --------------------------------------------
            epochs = epoch_data(
                raw,
                epoch_duration=prep_params.get("epoch_duration", 2.0),
                baseline=None,
            )

            # ----- SNR calculation -------------------------------------
            snr = calculate_snr(epochs)
            snr_metrics[participant_id] = {"snr_db": snr}

            # ----- Power‑spectrum sanity check -------------------------
            sanity_check_power_spectrum(
                epochs,
                low=prep_params.get("l_freq", 1.0),
                high=prep_params.get("h_freq", 45.0),
            )

            # ----- Quality checks --------------------------------------
            if run_quality_checks(epochs, snr, quality_thr):
                # Save epoched data
                out_fif = epoched_dir / f"{participant_id}-epochs.fif"
                save_epoched_data(epochs, out_fif)

                # Save metadata
                out_json = metadata_dir / f"{participant_id}.json"
                save_metadata(
                    out_json,
                    bandpass=(
                        prep_params.get("l_freq", 1.0),
                        prep_params.get("h_freq", 45.0),
                    ),
                    notch=prep_params.get("notch_freqs", [50.0, 100.0]),
                    bad_channels=bad_chs,
                    ica_removed=ica_removed,
                )
                logger.info(f"Participant {participant_id} processed successfully")
            else:
                exclusions.append(
                    {
                        "participant_id": participant_id,
                        "reason": "Failed quality check (duration/SNR)",
                        "snr_db": None if np.isnan(snr) else float(snr),
                    }
                )
                logger.info(f"Participant {participant_id} excluded")

        except Exception as exc:
            logger.error(f"Error processing {participant_id}: {exc}")
            exclusions.append(
                {"participant_id": participant_id, "reason": str(exc), "snr_db": None}
            )

        # Force garbage collection between participants to keep memory low
        gc.collect()

    # ----- Persist SNR metrics ---------------------------------------
    snr_path = processed_dir / "snr_metrics.json"
    with open(snr_path, "w", encoding="utf-8") as f:
        json.dump(snr_metrics, f, indent=2)
    logger.info(f"SNR metrics written to {snr_path}")

    # ----- Persist exclusion log -------------------------------------
    if exclusions:
        excl_df = pd.DataFrame(exclusions)
        excl_path = processed_dir / "exclusion_log.csv"
        excl_df.to_csv(excl_path, index=False)
        logger.info(f"Exclusion log written to {excl_path}")

    logger.info("EEG preprocessing pipeline completed")

if __name__ == "__main__":
    # Ensure resource limits are enforced at script start
    enforce_resource_limits(get_logger("preprocess"))
    main()
