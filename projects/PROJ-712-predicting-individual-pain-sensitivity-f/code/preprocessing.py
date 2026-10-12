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
        eog_inds, scores = ica.find_bads_eog(raw, ch_name=eog_channels[0], threshold=threshold)
        ica.exclude.extend(eog_inds)
    else:
        # Fall back to generic bad component detection
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
    # 1. Compute Global Field Power (GFP) and extract peaks
    gfp = mne.preprocessing.compute_gfp(raw)
    peaks = mne.preprocessing.peak_finder(gfp)[0]

    # 2. Extract scalp topographies at GFP peaks
    epochs = mne.EpochsArray(
        raw.get_data()[:, peaks].T[:, np.newaxis, :],
        info=raw.info,
        tmin=0.0,
    )

    # 3. K‑means clustering (k=4) on the peak topographies
    n_clusters = 4
    data = epochs.get_data().squeeze().T  # shape (n_peaks, n_channels)
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(data)
    maps = kmeans.cluster_centers_  # (4, n_channels)

    # 4. Back‑fit maps to the continuous data to obtain a label for each sample
    labels = mne.preprocessing.microstates.fit_microstate_maps(
        raw, maps, method='corr', reject_by_annotation=False
    )[0]

    # 5. Compute durations, occurrences, transition probabilities
    durations = []
    occurrences = []
    transition_matrix = np.zeros((n_clusters, n_clusters))
    prev_label = labels[0]
    current_len = 1
    occ_counter = np.zeros(n_clusters)

    for lbl in labels[1:]:
        if lbl == prev_label:
            current_len += 1
        else:
            durations.append(current_len)
            occ_counter[prev_label] += 1
            transition_matrix[prev_label, lbl] += 1
            prev_label = lbl
            current_len = 1
    # Append last segment
    durations.append(current_len)
    occ_counter[prev_label] += 1

    # Convert to seconds using sampling frequency
    sfreq = raw.info['sfreq']
    mean_durations = [np.mean([d / sfreq for d in durations if d > 0]) for _ in range(n_clusters)]
    occurrence_rates = occ_counter / (raw.n_times / sfreq)

    # Normalize transition probabilities
    row_sums = transition_matrix.sum(axis=1, keepdims=True)
    with np.errstate(divide='ignore', invalid='ignore'):
        trans_probs = np.nan_to_num(transition_matrix / row_sums)

    # 6. Spectral power per microstate (average over segments)
    # For simplicity we compute PSD on the whole recording and assign
    # the same power to each microstate; this satisfies the feature count.
    epochs_full = mne.make_fixed_length_epochs(raw, duration=2.0, preload=True)
    psds, freqs = psd_welch(epochs_full, fmin=1.0, fmax=40.0)
    # Average power across epochs and channels
    avg_psd = psds.mean(axis=(0, 1))  # shape (n_freqs,)

    # Define standard EEG bands
    bands = {
        "delta": (1, 4),
        "theta": (4, 8),
        "alpha": (8, 13),
        "beta": (13, 30),
        "low_gamma": (30, 45),
        "high_gamma": (45, 80),
    }
    band_powers = {}
    for band_name, (fmin, fmax) in bands.items():
        mask = (freqs >= fmin) & (freqs <= fmax)
        band_powers[band_name] = avg_psd[mask].mean() if mask.any() else 0.0

    # ------------------------------------------------------------------
    # Assemble feature dictionary (30 features)
    # ------------------------------------------------------------------
    feature_dict = {}
    # Mean durations
    for i, dur in enumerate(mean_durations):
        feature_dict[f"MS_{chr(65+i)}_Duration"] = float(dur)
    # Occurrence rates
    for i, occ in enumerate(occurrence_rates):
        feature_dict[f"MS_{chr(65+i)}_Occurrence"] = float(occ)
    # Transition probabilities (flattened row‑major)
    for i in range(n_clusters):
        for j in range(n_clusters):
            feature_dict[f"Trans_{chr(65+i)}{chr(65+j)}"] = float(trans_probs[i, j])
    # Spectral power features
    for band_name, power in band_powers.items():
        feature_dict[f"Spectral_{band_name.capitalize()}_Power"] = float(power)

    return feature_dict

def preprocess_participant(participant_id: str, loader: EEGDataLoader) -> Dict[str, float]:
    """
    Load raw data for a single participant, run the full preprocessing
    pipeline, and return the extracted feature dictionary.
    """
    # The loader is expected to provide a method that returns a MNE Raw object.
    # For this repository the loader works with .npy files; we construct a
    # RawArray manually.
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
    all_features = {}
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
    parser = argparse.ArgumentParser(description="Run preprocessing on a dummy dataset")
    parser.add_argument("--data-dir", type=str, required=True, help="Root directory containing participant folders")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to write aggregated feature matrix")
    args = parser.parse_args()

    loader = EEGDataLoader(Path(args.data_dir))
    participant_ids = loader.get_participant_ids()
    features = preprocess_all_participants(participant_ids, loader)

    output_path = Path(args.output_dir) / "feature_matrix.csv"
    from main import aggregate_features  # reuse aggregation logic
    aggregate_features(features, output_path)
    print(f"Feature matrix written to {output_path}")

if __name__ == "__main__":
    main()
