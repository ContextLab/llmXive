"""
EEG preprocessing module.
Provides functions for re-referencing, filtering, ICA cleaning,
microstate segmentation, and feature extraction.
"""
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import mne
import numpy as np
from scipy.signal import welch

# Import the data loader type used by the pipeline
from data_loader import EEGDataLoader

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
        raw.set_eeg_reference(ref_channels='average', projection=False)
    return raw

def bandpass_filter_data(raw: mne.io.Raw, l_freq: float = 1.0, h_freq: float = 40.0) -> mne.io.Raw:
    """Apply a zero‑phase FIR band‑pass filter (1–40 Hz)."""
    raw.filter(l_freq=l_freq, h_freq=h_freq, method='fir', phase='zero')
    return raw

def apply_ica(raw: mne.io.Raw, n_components: Optional[int] = None, random_state: int = 42) -> Tuple[mne.preprocessing.ICA, mne.io.Raw]:
    """Fit ICA on the raw data and return the ICA object."""
    ica = mne.preprocessing.ICA(
        n_components=n_components,
        random_state=random_state,
        max_iter='auto',
    )
    ica.fit(raw)
    return ica, raw

def find_and_remove_artifacts(ica: mne.preprocessing.ICA, raw: mne.io.Raw, threshold: float = 0.9) -> mne.io.Raw:
    """Identify ocular/muscle components automatically and remove them."""
    eog_channels = [ch for ch in raw.ch_names if 'EOG' in ch.upper()]
    if eog_channels:
        eog_inds, _ = ica.find_bads_eog(raw, ch_name=eog_channels[0], threshold=threshold)
        ica.exclude.extend(eog_inds)
    else:
        # Generic bad component detection based on explained variance
        ica.exclude = ica.get_components_by_score(threshold=threshold)
    ica.apply(raw)
    return raw

def estimate_valid_duration(raw: mne.io.Raw) -> float:
    """Estimate the total duration (in seconds) of the clean EEG segment."""
    return raw.times[-1] - raw.times[0]

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
        sfreq = epochs.info['sfreq']
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
    This implementation follows the canonical A‑D microstate pipeline.
    """
    # ------------------------------------------------------------------
    # 1. Global Field Power (GFP) peaks
    # ------------------------------------------------------------------
    gfp = mne.preprocessing.compute_gfp(raw)
    peaks = mne.preprocessing.peak_finder(gfp)[0]

    # ------------------------------------------------------------------
    # 2. Extract scalp topographies at GFP peaks
    # ------------------------------------------------------------------
    # Shape: (n_peaks, n_channels)
    topographies = raw.get_data()[:, peaks].T

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
        raw, maps, method='corr', reject_by_annotation=False
    )
    # labels is a 1‑D array length = n_times

    # ------------------------------------------------------------------
    # 5. Compute durations, occurrence rates, transition probabilities
    # ------------------------------------------------------------------
    sfreq = raw.info['sfreq']
    n_times = raw.n_times

    # Containers
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
            # Record the finished segment
            durations_per_label[prev_label].append(current_len)
            occ_counter[prev_label] += 1
            # Transition
            transition_matrix[prev_label, lbl] += 1
            # Reset for new segment
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
    with np.errstate(divide='ignore', invalid='ignore'):
        trans_probs = np.nan_to_num(transition_matrix / row_sums)

    # ------------------------------------------------------------------
    # 6. Spectral power per band (average across channels and time)
    # ------------------------------------------------------------------
    # Use Welch via MNE's helper (or fallback defined above)
    psds, freqs = psd_welch(raw, fmin=1.0, fmax=70.0, n_fft=int(sfreq * 2))
    # psds shape: (n_channels, n_freqs)
    avg_psd = psds.mean(axis=0)  # shape (n_freqs,)

    # Define EEG bands exactly as required by the spec/tests
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
    # Assemble feature dictionary (30 features)
    # ------------------------------------------------------------------
    feature_dict: Dict[str, float] = {}

    # Mean durations
    for i, dur in enumerate(mean_durations):
        feature_dict[f"MS_{chr(65 + i)}_Duration"] = float(dur)

    # Occurrence rates
    for i, occ in enumerate(occurrence_rates):
        feature_dict[f"MS_{chr(65 + i)}_Occurrence"] = float(occ)

    # Transition probabilities (flattened row‑major with underscore)
    for i in range(n_clusters):
        for j in range(n_clusters):
            feature_dict[f"Trans_{chr(65 + i)}_{chr(65 + j)}"] = float(trans_probs[i, j])

    # Spectral power features
    for band_name, power in band_powers.items():
        feature_dict[f"Spectral_{band_name}_Power"] = float(power)

    # Sanity check: ensure we have exactly 30 entries
    assert len(feature_dict) == 30, f"Expected 30 features, got {len(feature_dict)}"

    return feature_dict

def preprocess_participant(participant_id: str, loader: EEGDataLoader) -> Dict[str, float]:
    """
    Load raw data for a single participant, run the full preprocessing
    pipeline, and return the extracted feature dictionary.
    """
    participant_dir = loader.data_path / participant_id
    eeg_path = participant_dir / "eeg_data.npy"
    ch_path = participant_dir / "channel_info.npy"
    if not eeg_path.is_file() or not ch_path.is_file():
        raise FileNotFoundError(f"EEG or channel info missing for {participant_id}")

    data = np.load(eeg_path)  # shape (n_channels, n_times)
    ch_names = np.load(ch_path).tolist()
    info = mne.create_info(ch_names=ch_names, sfreq=500.0, ch_types="eeg")
    raw = mne.io.RawArray(data, info)

    # Preprocessing steps
    raw = re_reference_to_mastoids(raw)
    raw = bandpass_filter_data(raw)
    ica, raw = apply_ica(raw)
    raw = find_and_remove_artifacts(ica, raw)

    # Exclude participants with insufficient clean data (<4 min)
    valid_seconds = estimate_valid_duration(raw)
    if valid_seconds < 4 * 60:
        logger.warning(f"Participant {participant_id} excluded (only {valid_seconds:.1f}s clean data).")
        return {}

    # Feature extraction
    features = extract_microstate_features(raw)
    return features

def preprocess_all_participants(participant_ids: List[str], loader: EEGDataLoader) -> Dict[str, Dict[str, float]]:
    """
    Iterate over all participants, preprocess each, and collect their feature dictionaries.
    Returns a mapping from participant ID to its feature dict.
    """
    all_features: Dict[str, Dict[str, float]] = {}
    for pid in participant_ids:
        try:
            feats = preprocess_participant(pid, loader)
            if feats:  # empty dict indicates exclusion
                all_features[pid] = feats
        except Exception as e:
            logger.error(f"Error processing {pid}: {e}")
    return all_features

def main():
    """CLI entry point for debugging the preprocessing pipeline."""
    import argparse
    parser = argparse.ArgumentParser(description="Run preprocessing on a dataset")
    parser.add_argument("--data-dir", type=str, required=True, help="Root directory containing participant folders")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to write aggregated feature matrix")
    args = parser.parse_args()

    loader = EEGDataLoader(Path(args.data_dir))
    participant_ids = loader.get_participant_ids()
    features = preprocess_all_participants(participant_ids, loader)

    output_path = Path(args.output_dir) / "feature_matrix.csv"
    # Re‑use aggregation logic from the main pipeline
    from main import aggregate_features
    aggregate_features(features, output_path)
    print(f"Feature matrix written to {output_path}")

if __name__ == "__main__":
    main()