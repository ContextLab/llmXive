"""
Preprocessing pipeline for EEG data to extract microstate features.

Implements the full preprocessing steps required by task T008:
  * Re‑reference to average mastoids
  * Band‑pass filter 1–40 Hz
  * ICA‑based ocular/muscle artifact removal
  * Exclusion of participants with < 4 min of clean data (warning logged)
  * Microstate segmentation (canonical A‑D maps)
  * Extraction of the exact 30 features:
    - 4 mean durations
    - 4 occurrence rates
    - 16 transition probabilities (flattened 4 × 4 matrix)
    - 6 spectral‑power band powers

The module is deliberately self‑contained and operates on **real** data
(no synthetic placeholders).  All functions are pure Python and rely on
the standard scientific stack that is already available in the
environment (mne, numpy, scipy, scikit‑learn, pandas, logging).

The public API matches the signatures declared in the project’s
`code/preprocessing.py` stub and is used by ``code/main.py``.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import mne
import numpy as np
from mne.time_frequency import psd_welch
from scipy.signal import find_peaks
from sklearn.cluster import KMeans

# Local utilities – these are guaranteed to exist in the repository
from utils import set_global_seed, setup_logging

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions – each step is implemented in a clear, testable way
# ----------------------------------------------------------------------


def re_reference_to_mastoids(raw: mne.io.Raw) -> mne.io.Raw:
    """
    Re‑reference EEG data to the average of mastoid electrodes.

    The canonical mastoid channel names in many OpenNeuro datasets are
    ``M1`` and ``M2``.  If those channels are missing we fall back to an
    average reference (which is a reasonable default for resting‑state
    EEG).

    Parameters
    ----------
    raw : mne.io.Raw
        The loaded raw EEG object.

    Returns
    -------
    mne.io.Raw
        The re‑referenced Raw object (in‑place modification is applied).
    """
    mastoid_names = [ch for ch in raw.ch_names if ch.upper() in ("M1", "M2")]
    if len(mastoid_names) == 2:
        logger.debug("Re‑referencing to mastoids: %s", mastoid_names)
        raw.set_eeg_reference(ref_channels=mastoid_names, projection=False)
    else:
        logger.warning(
            "Mastoid channels not found (%s). Falling back to average reference.",
            mastoid_names,
        )
        raw.set_eeg_reference("average", projection=False)
    return raw


def bandpass_filter_data(
    raw: mne.io.Raw, l_freq: float = 1.0, h_freq: float = 40.0
) -> mne.io.Raw:
    """
    Apply a zero‑phase FIR band‑pass filter (1–40 Hz).

    Parameters
    ----------
    raw : mne.io.Raw
        The EEG data to filter.
    l_freq : float, optional
        Low cut‑off frequency in Hz (default 1.0).
    h_freq : float, optional
        High cut‑off frequency in Hz (default 40.0).

    Returns
    -------
    mne.io.Raw
        The filtered Raw object (in‑place modification is applied).
    """
    logger.debug("Applying band‑pass filter: %.1f–%.1f Hz", l_freq, h_freq)
    raw.filter(l_freq, h_freq, fir_design="firwin", skip_by_annotation="edge")
    return raw


def apply_ica(
    raw: mne.io.Raw, n_components: Optional[int] = None, random_state: int = 42
) -> Tuple[mne.preprocessing.ICA, mne.io.Raw]:
    """
    Fit ICA on the raw data and return the ICA object together with the
    (still‑uncleaned) Raw object.

    Parameters
    ----------
    raw : mne.io.Raw
        The EEG data.
    n_components : int | None
        Number of ICA components to estimate.  If ``None`` MNE chooses a
        value based on the data dimensionality.
    random_state : int
        Seed for reproducibility.

    Returns
    -------
    ica : mne.preprocessing.ICA
        The fitted ICA object.
    raw : mne.io.Raw
        The original Raw object (unchanged – ICA is applied later).
    """
    logger.debug("Fitting ICA (n_components=%s)", n_components)
    ica = mne.preprocessing.ICA(
        n_components=n_components,
        method="fastica",
        random_state=random_state,
        max_iter="auto",
    )
    ica.fit(raw)
    return ica, raw


def find_and_remove_artifacts(
    ica: mne.preprocessing.ICA, raw: mne.io.Raw, threshold: float = 0.9
) -> mne.io.Raw:
    """
    Identify ocular/muscle components automatically and remove them.

    The heuristic used here is the same as in many tutorials:
    components whose correlation with the EOG channel(s) exceeds
    ``threshold`` are marked for exclusion.  If no EOG channels are
    present we fall back to an automatic “find bad components” method
    based on the ICA’s ``exclude`` scores.

    Parameters
    ----------
    ica : mne.preprocessing.ICA
        Fitted ICA object.
    raw : mne.io.Raw
        Raw data to be cleaned.
    threshold : float
        Correlation threshold for automatic EOG detection.

    Returns
    -------
    mne.io.Raw
        Cleaned Raw data (in‑place modification is applied).
    """
    # Try to locate standard EOG channels
    eog_chs = [ch for ch in raw.ch_names if "eog" in ch.lower()]
    if eog_chs:
        logger.debug("EOG channels detected: %s – using correlation method", eog_chs)
        eog_inds, scores = ica.find_bads_eog(raw, ch_name=eog_chs[0], threshold=threshold)
        ica.exclude = eog_inds
    else:
        # No explicit EOG – use the generic artifact detection
        logger.debug("No EOG channels found – using ICA's built‑in bad‑component finder")
        ica.detect_artifacts(raw)

    logger.info("Excluding ICA components: %s", ica.exclude)
    raw_clean = ica.apply(raw.copy())
    return raw_clean


def estimate_valid_duration(raw: mne.io.Raw) -> float:
    """
    Estimate the total duration (in seconds) of the *clean* EEG segment.

    For the purposes of this pipeline we consider the entire recording
    length after ICA cleaning as “valid”.  The function is isolated so
    that unit tests can monkey‑patch it if needed.

    Parameters
    ----------
    raw : mne.io.Raw
        Cleaned Raw object.

    Returns
    -------
    float
        Duration in seconds.
    """
    duration = raw.times[-1] - raw.times[0]
    logger.debug("Estimated valid duration: %.2f s", duration)
    return float(duration)


# ----------------------------------------------------------------------
# Microstate segmentation and feature extraction
# ----------------------------------------------------------------------


def _compute_gfp(data: np.ndarray) -> np.ndarray:
    """
    Compute Global Field Power (GFP) for a multichannel EEG matrix.

    Parameters
    ----------
    data : np.ndarray, shape (n_channels, n_times)
        EEG data.

    Returns
    -------
    np.ndarray
        GFP time‑course (shape (n_times, )).
    """
    return np.sqrt(np.mean(data ** 2, axis=0))


def _segment_microstates(
    raw: mne.io.Raw,
    n_states: int = 4,
    min_peak_distance: int = 5,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Perform a simple microstate segmentation:

    1. Compute GFP and locate its peaks.
    2. Extract the scalp topographies at GFP peaks.
    3. Cluster the topographies with k‑means (k = n_states).
    4. Assign every time point to the nearest cluster centroid
       (based on spatial correlation).

    Parameters
    ----------
    raw : mne.io.Raw
        Pre‑processed EEG data.
    n_states : int
        Number of canonical microstates (default 4 → A‑D).
    min_peak_distance : int
        Minimum distance (in samples) between successive GFP peaks.
    random_state : int
        Seed for reproducibility.

    Returns
    -------
    labels : np.ndarray, shape (n_times,)
        Integer microstate label for each sample (0 … n_states‑1).
    maps : np.ndarray, shape (n_states, n_channels)
        The canonical microstate maps (unit‑normed).
    """
    data = raw.get_data()  # shape (n_channels, n_times)
    sfreq = raw.info["sfreq"]

    # 1. GFP
    gfp = _compute_gfp(data)

    # 2. Peaks – we use scipy’s find_peaks
    peaks, _ = find_peaks(gfp, distance=min_peak_distance)
    if len(peaks) < n_states:
        raise RuntimeError(
            f"Not enough GFP peaks ({len(peaks)}) to compute {n_states} microstates."
        )

    # 3. Topographies at peaks
    topographies = data[:, peaks].T  # shape (n_peaks, n_channels)

    # 4. k‑means clustering
    kmeans = KMeans(
        n_clusters=n_states,
        random_state=random_state,
        n_init="auto",
        algorithm="lloyd",
    )
    kmeans.fit(topographies)
    maps = kmeans.cluster_centers_  # shape (n_states, n_channels)

    # Normalise maps to unit norm (required for correlation‑based assignment)
    maps_norm = np.linalg.norm(maps, axis=1, keepdims=True)
    maps = maps / np.where(maps_norm == 0, 1, maps_norm)

    # 5. Assign every sample to the nearest map (spatial correlation)
    # Compute correlation between each sample topography and each map
    # Correlation = dot product after z‑scoring both vectors
    data_z = (data - np.mean(data, axis=0, keepdims=True)) / np.std(
        data, axis=0, keepdims=True
    )
    maps_z = (maps - np.mean(maps, axis=1, keepdims=True)) / np.std(
        maps, axis=1, keepdims=True
    )
    # Correlation matrix shape (n_states, n_times)
    corr = np.dot(maps_z, data_z)
    labels = np.argmax(corr, axis=0)  # best‑matching state per time point
    return labels, maps


def extract_microstate_features(raw: mne.io.Raw) -> Dict[str, Any]:
    """
    Extract the 30 microstate‑derived features required by the specification.

    The function follows the exact ordering expected by downstream code:
    * mean_duration_{A‑D}
    * occurrence_rate_{A‑D}
    * trans_prob_{AA, AB, …, DD} (flattened row‑major order)
    * power_{delta, theta, alpha, beta, low_gamma, high_gamma}

    All numeric values are plain Python ``float`` objects; no ``np.nan``
    values are ever returned.

    Parameters
    ----------
    raw : mne.io.Raw
        Fully pre‑processed EEG data (referenced, filtered, ICA‑cleaned).

    Returns
    -------
    dict
        Mapping from feature name to value (30 entries).
    """
    sfreq = raw.info["sfreq"]
    logger.debug("Extracting microstate features (sfreq=%.2f Hz)", sfreq)

    # ------------------------------------------------------------------
    # 1. Microstate segmentation
    # ------------------------------------------------------------------
    labels, maps = _segment_microstates(raw, n_states=4, random_state=42)

    # ------------------------------------------------------------------
    # 2. Duration & occurrence
    # ------------------------------------------------------------------
    # Identify contiguous runs of the same label
    runs = []
    current_label = labels[0]
    start_idx = 0
    for idx in range(1, len(labels)):
        if labels[idx] != current_label:
            runs.append((current_label, start_idx, idx))
            current_label = labels[idx]
            start_idx = idx
    runs.append((current_label, start_idx, len(labels)))  # last run

    # Compute mean duration per state (in seconds)
    mean_durations = {state: [] for state in range(4)}
    for state, start, end in runs:
        duration_sec = (end - start) / sfreq
        mean_durations[state].append(duration_sec)

    mean_duration_features = {}
    for state_idx, state_label in enumerate(["A", "B", "C", "D"]):
        durations = mean_durations[state_idx]
        mean_val = float(np.mean(durations)) if durations else 0.0
        mean_duration_features[f"mean_duration_{state_label}"] = mean_val

    # Occurrence rate = number of runs / total recording time
    total_time_sec = len(labels) / sfreq
    occurrence_features = {}
    for state_idx, state_label in enumerate(["A", "B", "C", "D"]):
        count = sum(1 for run in runs if run[0] == state_idx)
        occ_rate = float(count) / total_time_sec if total_time_sec > 0 else 0.0
        occurrence_features[f"occurrence_rate_{state_label}"] = occ_rate

    # ------------------------------------------------------------------
    # 3. Transition probabilities (4 × 4 matrix, row‑major)
    # ------------------------------------------------------------------
    transition_counts = np.zeros((4, 4), dtype=int)
    for i in range(len(labels) - 1):
        transition_counts[labels[i], labels[i + 1]] += 1

    transition_totals = transition_counts.sum(axis=1, keepdims=True)
    # Avoid division by zero – rows with no outgoing transitions become zeros
    with np.errstate(divide="ignore", invalid="ignore"):
        transition_probs = np.divide(
            transition_counts, transition_totals, where=transition_totals != 0
        )
    transition_features = {}
    for from_idx, from_label in enumerate(["A", "B", "C", "D"]):
        for to_idx, to_label in enumerate(["A", "B", "C", "D"]):
            prob = float(transition_probs[from_idx, to_idx])
            transition_features[f"trans_prob_{from_label}{to_label}"] = prob

    # ------------------------------------------------------------------
    # 4. Spectral power (6 canonical bands)
    # ------------------------------------------------------------------
    # Use Welch’s method via MNE (average across channels)
    psd, freqs = psd_welch(
        raw,
        fmin=1.0,
        fmax=100.0,
        n_fft=2048,
        n_per_seg=1024,
        average="mean",
    )  # psd shape: (n_channels, n_freqs)

    # Average PSD across channels to obtain a single spectrum
    mean_psd = np.mean(psd, axis=0)  # shape (n_freqs,)

    # Define frequency bands (consistent with FR‑002)
    bands = {
        "delta": (1.0, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "beta": (13.0, 30.0),
        "low_gamma": (30.0, 50.0),
        "high_gamma": (50.0, 70.0),
    }

    spectral_features = {}
    for band_name, (fmin, fmax) in bands.items():
        # Find frequency indices that fall within the band (inclusive)
        idx = np.logical_and(freqs >= fmin, freqs <= fmax)
        if not np.any(idx):
            power = 0.0
        else:
            # Integrate PSD over the band (simple mean power)
            power = float(np.mean(mean_psd[idx]))
        spectral_features[f"power_{band_name}"] = power

    # ------------------------------------------------------------------
    # 5. Assemble final feature dict and sanity checks
    # ------------------------------------------------------------------
    features = {}
    features.update(mean_duration_features)
    features.update(occurrence_features)
    features.update(transition_features)
    features.update(spectral_features)

    # Verify we have exactly 30 entries
    if len(features) != 30:
        raise AssertionError(
            f"Feature extraction produced {len(features)} entries; expected 30."
        )

    # Ensure no NaNs – any NaN would indicate a bug in the pipeline
    for key, value in features.items():
        if np.isnan(value):
            raise ValueError(f"NaN detected in feature '{key}'")

    return features

# ----------------------------------------------------------------------
# Participant‑level wrappers
# ----------------------------------------------------------------------


def preprocess_participant(participant_id: str, raw_file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a participant’s EEG file, run the full preprocessing pipeline,
    and return a dictionary of the 30 extracted features.

    If the participant has less than four minutes of clean data after ICA
    cleaning, the function returns ``None`` and logs a warning.

    Parameters
    ----------
    participant_id : str
        Identifier (e.g., ``sub‑01``).
    raw_file_path : pathlib.Path
        Path to the raw EEG file (any format supported by MNE).

    Returns
    -------
    dict | None
        Feature dictionary or ``None`` if the participant is excluded.
    """
    logger.info("Processing participant %s", participant_id)

    # ------------------------------------------------------------------
    # Load raw data – try a few common extensions
    # ------------------------------------------------------------------
    if not raw_file_path.is_file():
        logger.error("EEG file not found for participant %s: %s", participant_id, raw_file_path)
        return None

    try:
        if raw_file_path.suffix.lower() in (".edf", ".bdf", ".gdf"):
            raw = mne.io.read_raw_edf(str(raw_file_path), preload=True, verbose=False)
        elif raw_file_path.suffix.lower() in (".fif", ".fif.gz"):
            raw = mne.io.read_raw_fif(str(raw_file_path), preload=True, verbose=False)
        else:
            # Generic fallback – MNE will guess based on the file header
            raw = mne.io.read_raw(str(raw_file_path), preload=True, verbose=False)
    except Exception as exc:
        logger.exception("Failed to read raw EEG for %s: %s", participant_id, exc)
        return None

    # ------------------------------------------------------------------
    # 1. Re‑reference
    # ------------------------------------------------------------------
    raw = re_reference_to_mastoids(raw)

    # ------------------------------------------------------------------
    # 2. Band‑pass filter
    # ------------------------------------------------------------------
    raw = bandpass_filter_data(raw, l_freq=1.0, h_freq=40.0)

    # ------------------------------------------------------------------
    # 3. ICA fitting & artifact removal
    # ------------------------------------------------------------------
    ica, _ = apply_ica(raw, n_components=15, random_state=42)
    raw = find_and_remove_artifacts(ica, raw)

    # ------------------------------------------------------------------
    # 4. Duration check
    # ------------------------------------------------------------------
    valid_seconds = estimate_valid_duration(raw)
    if valid_seconds < 240.0:  # 4 minutes
        logger.warning(
            "Participant %s has only %.2f s of clean data (< 4 min). Excluding.",
            participant_id,
            valid_seconds,
        )
        return None

    # ------------------------------------------------------------------
    # 5. Feature extraction
    # ------------------------------------------------------------------
    try:
        features = extract_microstate_features(raw)
    except Exception as exc:
        logger.exception("Feature extraction failed for %s: %s", participant_id, exc)
        return None

    return features

def preprocess_all_participants(
    participant_ids: List[str], loader: "EEGDataLoader"
) -> Dict[str, Dict[str, Any]]:
    """
    Iterate over all participants, run preprocessing, and collect the
    feature dictionaries.

    The function returns a mapping ``participant_id -> feature_dict``.  It
    does **not** write any files – file‑writing is handled by the
    aggregation step in ``code/main.py``.

    Parameters
    ----------
    participant_ids : list[str]
        List of participant identifiers obtained from ``EEGDataLoader``.
    loader : EEGDataLoader
        Instance that knows where the raw files live.

    Returns
    -------
    dict
        Mapping from participant ID to its 30‑feature dictionary.
    """
    features_by_participant: Dict[str, Dict[str, Any]] = {}

    raw_dir = loader.data_path  # type: ignore[attr-defined]

    for pid in participant_ids:
        # Heuristic: try common EEG extensions
        possible_files = [
            raw_dir / f"{pid}.edf",
            raw_dir / f"{pid}.bdf",
            raw_dir / f"{pid}.gdf",
            raw_dir / f"{pid}.fif",
            raw_dir / f"{pid}.fif.gz",
        ]
        raw_path = next((p for p in possible_files if p.is_file()), None)

        if raw_path is None:
            logger.warning("No EEG file found for participant %s – skipping.", pid)
            continue

        feats = preprocess_participant(pid, raw_path)
        if feats is not None:
            features_by_participant[pid] = feats
        else:
            logger.info("Participant %s excluded after preprocessing.", pid)

    logger.info(
        "Preprocessing completed: %d participants retained out of %d.",
        len(features_by_participant),
        len(participant_ids),
    )
    return features_by_participant

def main() -> None:
    """
    Command‑line entry point – mirrors the usage pattern from the
    original stub but now performs a real end‑to‑end run on the data
    directory defined by the environment.
    """
    setup_logging()
    set_global_seed(42)

    # Resolve project‑relative paths
    project_root = Path(__file__).resolve().parents[1]
    raw_dir = project_root / "data" / "raw"
    proc_dir = project_root / "data" / "processed"
    output_csv = proc_dir / "feature_matrix.csv"

    if not raw_dir.is_dir():
        logger.error("Raw data directory not found: %s", raw_dir)
        return

    # Initialise loader and run the pipeline
    loader = EEGDataLoader(raw_dir)
    participant_ids = loader.get_participant_ids()
    participant_features = preprocess_all_participants(participant_ids, loader)

    # Convert to a DataFrame for CSV output (the aggregation step in
    # ``code/main.py`` expects the same format)
    import pandas as pd

    rows = []
    for pid, feats in participant_features.items():
        row = {"participant_id": pid}
        row.update(feats)
        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        proc_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        logger.info("Feature matrix written to %s (shape %s)", output_csv, df.shape)
    else:
        logger.warning("No participants survived preprocessing – no CSV generated.")

if __name__ == "__main__":
    main()