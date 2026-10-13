"""
EEG preprocessing module.
Provides functions for re‑referencing, filtering, ICA cleaning,
microstate segmentation, and feature extraction, using the DataChunk
streaming interface.
"""
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import mne
import numpy as np
import pandas as pd
from scipy.stats import kurtosis
from scipy.signal import welch

# Import the data loader and DataChunk class used for streaming
from data_loader import EEGDataLoader, DataChunk

# Import expected feature column names to ensure correct header naming
from config import EXPECTED_FEATURE_COLUMNS

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def re_reference_to_mastoids(raw: mne.io.Raw) -> mne.io.Raw:
    """Re‑reference EEG data to the average of mastoid electrodes."""
    mastoid_names = ["M1", "M2"]
    available = [ch for ch in mastoid_names if ch in raw.ch_names]
    if available:
        raw.set_eeg_reference(ref_channels=available, projection=False)
    else:
        raw.set_eeg_reference(ref_channels="average", projection=False)
    return raw

def bandpass_filter_data(
    raw: mne.io.Raw, l_freq: float = 1.0, h_freq: float = 40.0
) -> mne.io.Raw:
    """Apply a zero‑phase FIR band‑pass filter (1–40 Hz)."""
    raw.filter(l_freq=l_freq, h_freq=h_freq, method="fir", phase="zero")
    return raw

def apply_ica(
    raw: mne.io.Raw,
    n_components: Optional[int] = None,
    random_state: int = 42,
) -> Tuple[mne.preprocessing.ICA, mne.io.Raw]:
    """Fit ICA on the raw data and return the ICA object."""
    ica = mne.preprocessing.ICA(
        n_components=n_components,
        random_state=random_state,
        max_iter="auto",
    )
    ica.fit(raw)
    return ica, raw

def find_and_remove_artifacts(
    ica: mne.preprocessing.ICA,
    raw: mne.io.Raw,
    eog_corr_threshold: float = 0.9,
    kurtosis_threshold: float = 10.0,
) -> mne.io.Raw:
    """
    Identify ocular/muscle components automatically and discard them.

    Components are excluded when:
    * Correlation with an EOG channel exceeds ``eog_corr_threshold``.
    * Absolute kurtosis of the component time‑series exceeds ``kurtosis_threshold``.
    """
    # 1. Correlation with EOG channels
    eog_channels = [ch for ch in raw.ch_names if "EOG" in ch.upper()]
    if eog_channels:
        eog_inds, _ = ica.find_bads_eog(
            raw, ch_name=eog_channels[0], threshold=eog_corr_threshold
        )
        ica.exclude.extend(eog_inds)

    # 2. High‑kurtosis components
    component_sources = ica.get_sources(raw).get_data()
    for idx, comp in enumerate(component_sources):
        if np.abs(kurtosis(comp)) > kurtosis_threshold:
            if idx not in ica.exclude:
                ica.exclude.append(idx)

    # Apply the removal
    ica.apply(raw)
    return raw

def estimate_valid_duration(raw: mne.io.Raw) -> float:
    """Estimate the total duration (in seconds) of the clean EEG segment."""
    # After ICA removal the data length stays the same; we treat the whole
    # recording as usable because bad segments have been zero‑ed out.
    return float(raw.times[-1] - raw.times[0])

# ----------------------------------------------------------------------
# Spectral power extraction – fallback implementation if MNE's psd_welch is unavailable
# ----------------------------------------------------------------------
try:
    from mne.time_frequency import psd_welch  # type: ignore
except Exception:  # pragma: no cover
    def psd_welch(epochs, fmin=0.5, fmax=40.0, tmin=0.0, tmax=None, **kwargs):
        """
        Simple Welch‑based PSD calculation compatible with the original MNE API.
        Returns (psds, freqs) where psds has shape (n_epochs, n_channels, n_freqs).
        """
        sfreq = epochs.info["sfreq"]
        data = epochs.get_data()  # (n_epochs, n_channels, n_times)
        psd_list = []
        for epoch in data:
            ch_psd = []
            for ch in epoch:
                freqs, power = welch(ch, fs=sfreq, nperseg=int(sfreq * 2), **kwargs)
                mask = (freqs >= fmin) & (freqs <= fmax)
                ch_psd.append(power[mask])
            psd_list.append(ch_psd)
        psds = np.array(psd_list)  # (n_epochs, n_channels, n_selected_freqs)
        freqs_selected = freqs[mask]
        return psds, freqs_selected

def extract_microstate_features(raw: mne.io.Raw) -> Dict[str, float]:
    """
    Perform microstate segmentation and extract the 30 required features.
    This implementation follows the canonical A‑D microstate pipeline
    and returns a dictionary whose keys exactly match the names listed in
    ``config.EXPECTED_FEATURE_COLUMNS``.
    """
    # ------------------------------------------------------------------
    # 1. Global Field Power (GFP) peaks
    # ------------------------------------------------------------------
    gfp = mne.preprocessing.compute_gfp(raw)
    peaks = mne.preprocessing.peak_finder(gfp)[0]

    # ------------------------------------------------------------------
    # 2. Extract scalp topographies at GFP peaks
    # ------------------------------------------------------------------
    topographies = raw.get_data()[:, peaks].T  # (n_peaks, n_channels)

    # ------------------------------------------------------------------
    # 3. K‑means clustering (k=4) on the peak topographies
    # ------------------------------------------------------------------
    n_clusters = 4
    from sklearn.cluster import KMeans

    kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(topographies)
    maps = kmeans.cluster_centers_  # shape (4, n_channels)

    # ------------------------------------------------------------------
    # 4. Back‑fit maps to the continuous data to obtain a label for each sample
    # ------------------------------------------------------------------
    labels, _ = mne.preprocessing.microstates.fit_microstate_maps(
        raw, maps, method="corr", reject_by_annotation=False
    )
    # labels is a 1‑D array length = n_times

    # ------------------------------------------------------------------
    # 5. Compute durations, occurrence rates, transition probabilities
    # ------------------------------------------------------------------
    sfreq = raw.info["sfreq"]
    n_times = raw.n_times

    durations_per_label: Dict[int, List[int]] = {i: [] for i in range(n_clusters)}
    occ_counter = np.zeros(n_clusters, dtype=float)
    transition_matrix = np.zeros((n_clusters, n_clusters), dtype=float)

    prev_label = int(labels[0])
    current_len = 1

    for lbl in labels[1:]:
        lbl = int(lbl)
        if lbl == prev_label:
            current_len += 1
        else:
            durations_per_label[prev_label].append(current_len)
            occ_counter[prev_label] += 1
            transition_matrix[prev_label, lbl] += 1
            prev_label = lbl
            current_len = 1

    # Append the final segment
    durations_per_label[prev_label].append(current_len)
    occ_counter[prev_label] += 1

    # Mean durations (seconds) per microstate
    mean_durations = []
    for i in range(n_clusters):
        if durations_per_label[i]:
            mean_sec = np.mean(durations_per_label[i]) / sfreq
        else:
            mean_sec = 0.0
        mean_durations.append(mean_sec)

    # Occurrence rates (segments per second)
    total_seconds = n_times / sfreq
    occurrence_rates = occ_counter / total_seconds

    # Transition probabilities (row‑wise normalized)
    row_sums = transition_matrix.sum(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        trans_probs = np.nan_to_num(transition_matrix / row_sums)

    # ------------------------------------------------------------------
    # 6. Spectral power per band (average across channels and time)
    # ------------------------------------------------------------------
    psds, freqs = psd_welch(raw, fmin=1.0, fmax=70.0, n_fft=int(sfreq * 2))
    # psds shape: (n_channels, n_freqs) or (n_epochs, n_channels, n_freqs)
    if psds.ndim == 3:
        psds = psds.mean(axis=0)
    avg_psd = psds.mean(axis=0)  # (n_freqs,)

    bands = {
        "Delta": (1.0, 4.0),
        "Theta": (4.0, 8.0),
        "Alpha": (8.0, 13.0),
        "Beta": (13.0, 30.0),
        "LowGamma": (30.0, 50.0),
        "HighGamma": (50.0, 70.0),
    }

    band_powers = {}
    for band_name, (fmin, fmax) in bands.items():
        mask = (freqs >= fmin) & (freqs <= fmax)
        if mask.any():
            band_powers[band_name] = float(avg_psd[mask].mean())
        else:
            band_powers[band_name] = 0.0

    # ------------------------------------------------------------------
    # 7. Assemble feature dictionary respecting the canonical column order
    # ------------------------------------------------------------------
    values_in_order: List[float] = []
    values_in_order.extend(mean_durations)                     # 4
    values_in_order.extend(occurrence_rates.tolist())          # 4
    # Flatten transition matrix row‑major
    values_in_order.extend(trans_probs.ravel().tolist())       # 16
    # Append spectral powers in the order defined above
    for band_name in ["Delta", "Theta", "Alpha", "Beta", "LowGamma", "HighGamma"]:
        values_in_order.append(band_powers[band_name])        # 6

    # Sanity check
    if len(values_in_order) != 30:
        raise ValueError(f"Expected 30 feature values, got {len(values_in_order)}")

    # Map to the canonical column names from config
    if len(EXPECTED_FEATURE_COLUMNS) != 30:
        raise ValueError(
            f"EXPECTED_FEATURE_COLUMNS length mismatch: expected 30, got {len(EXPECTED_FEATURE_COLUMNS)}"
        )
    feature_dict = dict(zip(EXPECTED_FEATURE_COLUMNS, values_in_order))

    return feature_dict

def _load_participant_metadata(metadata_path: Path) -> pd.DataFrame:
    """
    Load the heat‑pain‑threshold CSV and return a DataFrame indexed by participant_id.
    Expected columns: participant_id, heat_pain_threshold, age, gender
    """
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Metadata CSV not found at {metadata_path}")
    df = pd.read_csv(metadata_path, dtype=str)
    required = {"participant_id", "heat_pain_threshold", "age", "gender"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Metadata CSV missing required columns: {missing}")
    df = df.set_index("participant_id")
    return df

def _load_raw_for_participant(loader: EEGDataLoader, participant_id: str) -> mne.io.Raw:
    """
    Helper that loads the raw EEG file for a participant using the loader's
    raw directory. The loader may not provide a direct ``load_raw`` method,
    so we locate the first .fif or .edf file inside the participant's folder.
    """
    raw_dir = _determine_raw_dir(loader)
    participant_dir = raw_dir / participant_id
    if not participant_dir.is_dir():
        raise FileNotFoundError(f"Participant folder not found: {participant_dir}")

    # Search for common EEG file extensions
    for ext in ("*.fif", "*.edf", "*.set", "*.bdf"):
        candidates = list(participant_dir.glob(ext))
        if candidates:
            raw_path = candidates[0]
            raw = mne.io.read_raw(raw_path, preload=False, verbose=False)
            return raw

    raise FileNotFoundError(
        f"No EEG file found for participant {participant_id} in {participant_dir}"
    )

def _determine_raw_dir(loader: EEGDataLoader) -> Path:
    """
    Helper to obtain the directory that holds the raw participant files.
    The EEGDataLoader class may expose this via ``raw_dir``, ``raw_path``,
    ``base_dir`` or ``data_dir``. We try the known attribute names and fall
    back to the loader's initialization argument (if it stores it as
    ``root`` or ``path``). If none are found we raise a clear error.
    """
    for attr in ("raw_dir", "raw_path", "base_dir", "data_dir", "root", "path"):
        if hasattr(loader, attr):
            candidate = getattr(loader, attr)
            if isinstance(candidate, Path):
                return candidate
            else:
                return Path(candidate)

    for name, value in vars(loader).items():
        if isinstance(value, Path) and value.is_dir():
            return value

    raise AttributeError(
        "EEGDataLoader does not expose a raw data directory attribute. "
        "Expected one of: raw_dir, raw_path, base_dir, data_dir, root, path."
    )

def preprocess_participant(
    participant_id: str,
    loader: EEGDataLoader,
    metadata_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Load raw data for a single participant, run the full preprocessing
    pipeline, and return a dictionary containing all required columns
    (metadata + 30 features + valid_eeg_minutes).
    """
    # Load raw data via the streaming loader (preload=False)
    raw: mne.io.Raw = _load_raw_for_participant(loader, participant_id)

    # ------------------------------------------------------------------
    # Preprocessing steps
    # ------------------------------------------------------------------
    raw = re_reference_to_mastoids(raw)
    raw = bandpass_filter_data(raw)
    ica, raw = apply_ica(raw)
    raw = find_and_remove_artifacts(ica, raw)

    # ------------------------------------------------------------------
    # Estimate clean duration after ICA
    # ------------------------------------------------------------------
    valid_seconds = estimate_valid_duration(raw)

    # Exclude participants with insufficient clean data (<4 min)
    if valid_seconds < 4 * 60:
        logger.warning(
            f"Participant {participant_id} excluded (only {valid_seconds:.1f}s clean data)."
        )
        return {}

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------
    raw_features = extract_microstate_features(raw)

    # ------------------------------------------------------------------
    # Assemble full row
    # ------------------------------------------------------------------
    row: Dict[str, Any] = {
        "participant_id": participant_id,
        "valid_eeg_minutes": round(valid_seconds / 60.0, 2),
    }

    # Add metadata (heat_pain_threshold, age, gender)
    if participant_id not in metadata_df.index:
        raise KeyError(f"Metadata for participant {participant_id} not found.")
    meta = metadata_df.loc[participant_id]
    row["heat_pain_threshold"] = meta["heat_pain_threshold"]
    row["age"] = meta["age"]
    row["gender"] = meta["gender"]

    # Add the 30 microstate features using the expected column names
    row.update(raw_features)

    return row

def preprocess_all_participants(
    participant_ids: List[str], loader: EEGDataLoader
) -> List[Dict[str, Any]]:
    """
    Iterate over provided participant IDs, preprocess each, and collect the rows.
    Returns a list of dictionaries ready for aggregation into a DataFrame.
    """
    raw_dir = _determine_raw_dir(loader)
    metadata_path = raw_dir / "heat_pain_thresholds.csv"
    metadata_df = _load_participant_metadata(metadata_path)

    all_rows: List[Dict[str, Any]] = []

    for participant_id in participant_ids:
        try:
            row = preprocess_participant(participant_id, loader, metadata_df)
            if row:
                all_rows.append(row)
        except Exception as e:
            logger.error(f"Error processing participant {participant_id}: {e}")

    return all_rows

def main():
    """CLI entry point for debugging the preprocessing pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="Run preprocessing on a dataset")
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Root directory containing participant subfolders",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory to write aggregated feature matrix",
    )
    args = parser.parse_args()

    loader = EEGDataLoader(Path(args.data_dir))
    participant_ids = loader.get_participant_ids()
    rows = preprocess_all_participants(participant_ids, loader)

    if not rows:
        logger.error("No participant data was processed successfully.")
        return

    # Convert to DataFrame and write CSV
    df = pd.DataFrame(rows)

    # Ensure column order matches EXPECTED_FEATURE_COLUMNS (plus base columns)
    base_cols = ["participant_id", "heat_pain_threshold", "age", "gender", "valid_eeg_minutes"]
    ordered = base_cols + EXPECTED_FEATURE_COLUMNS
    df = df[ordered]

    output_path = Path(args.output_dir) / "feature_matrix.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Feature matrix written to {output_path}")

if __name__ == "__main__":
    main()
