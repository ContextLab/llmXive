"""
functional.py
----------------
Implements the functional pipeline for dynamic functional connectivity analysis.

This module provides utilities to:
1. Compute sliding‑window correlation matrices from fMRI time‑series.
2. Generate Leave‑One‑Subject‑Out (LOSO) k‑means centroids using the data of all
   *other* subjects.
3. Assign each window of a target subject to the LOSO centroids.
4. Derive dynamic metrics (mean dwell time per state, number of visited states).
5. Persist artefacts required by downstream tasks:
   - ``data/derived/loo_centroids_all_subjects.npz``
   - ``data/logs/methodology_deviations.json``
   - ``data/derived/state_assignments.csv``
   - ``data/derived/dynamic_metrics.csv``
   - ``data/logs/exclusion_log.json`` (records subjects that could not be processed)

The implementation follows the specifications in **Task T016** and **Task T017**,
ensuring strict LOSO independence and proper logging of exclusion events.
All file paths are constructed with the ``llmxive_toolkit.paths`` helper which
guarantees that directories exist.
"""

import json
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from llmxive_toolkit import paths, get_logger
from config import get_config_dict

# Local imports for data loading
from data_loader import download_hcp_dataset, load_fmri, get_subject_paths

log = get_logger(__name__)

###########################################################################
# Helper functions
###########################################################################

def _sliding_window_correlation(
    fmri_data: np.ndarray,
    window_length: int,
    step: int,
) -> np.ndarray:
    """
    Compute correlation matrices for overlapping windows.

    Parameters
    ----------
    fmri_data : np.ndarray
        2‑D array of shape (T, V) where T is the number of time points and V
        is the number of brain regions (parcels).
    window_length : int
        Length of each sliding window in TRs.
    step : int
        Step size between consecutive windows in TRs.

    Returns
    -------
    np.ndarray
        3‑D array of shape (n_windows, V, V) containing the correlation matrices.
    """
    if fmri_data.ndim != 2:
        raise ValueError("fmri_data must be a 2‑D array (time × regions).")
    T, V = fmri_data.shape
    if window_length > T:
        raise ValueError("window_length cannot be larger than the time series length.")
    indices = range(0, T - window_length + 1, step)
    windows = []
    for start in indices:
        segment = fmri_data[start : start + window_length, :]  # (window_length, V)
        corr = np.corrcoef(segment.T)  # (V, V)
        corr = np.nan_to_num(corr)    # replace NaNs with 0
        windows.append(corr)
    return np.stack(windows, axis=0)  # (n_windows, V, V)

def _vectorise_matrices(matrices: np.ndarray) -> np.ndarray:
    """
    Flatten a stack of square matrices for clustering.

    Parameters
    ----------
    matrices : np.ndarray
        Shape (n_samples, V, V)

    Returns
    ----------
    np.ndarray
        Shape (n_samples, V * V)
    """
    n, V, _ = matrices.shape
    return matrices.reshape(n, V * V)

def _reshape_vectors(vectors: np.ndarray, V: int) -> np.ndarray:
    """
    Reshape flattened vectors back to square matrices.

    Parameters
    ----------
    vectors : np.ndarray
        Shape (n_samples, V * V)
    V : int
        Number of brain regions.

    Returns
    ----------
    np.ndarray
        Shape (n_samples, V, V)
    """
    return vectors.reshape(-1, V, V)

###########################################################################
# Core pipeline
###########################################################################

def generate_loso_centroids(
    target_subject_id: str,
    other_fmri_data: List[np.ndarray],
    window_length: int,
    step: int,
    k_means_k: int,
) -> np.ndarray:
    """
    Generate LOSO centroids for a given subject.

    The function concatenates the sliding‑window correlation matrices of *all*
    subjects except the target, runs k‑means clustering, and returns the
    centroids reshaped to (k, V, V).

    Parameters
    ----------
    target_subject_id : str
        Identifier of the subject for which centroids are being generated.
    other_fmri_data : List[np.ndarray]
        List of fMRI time‑series arrays (each shape (T, V)) belonging to all
        subjects *other* than the target.
    window_length : int
    step : int
    k_means_k : int

    Returns
    -------
    np.ndarray
        Centroids array of shape (k_means_k, V, V).
    """
    # Compute windows for every other subject and stack them
    all_windows = []
    for fmri in other_fmri_data:
        windows = _sliding_window_correlation(fmri, window_length, step)
        all_windows.append(windows)
    if not all_windows:
        raise ValueError("No other subjects provided for LOSO centroid generation.")
    all_windows = np.concatenate(all_windows, axis=0)  # (N_total_windows, V, V)

    V = all_windows.shape[1]
    vectors = _vectorise_matrices(all_windows)  # (N_total_windows, V*V)

    # Run k‑means
    kmeans = KMeans(n_clusters=k_means_k, random_state=42, n_init="auto")
    kmeans.fit(vectors)
    centroids = _reshape_vectors(kmeans.cluster_centers_, V)  # (k, V, V)

    # Persist the centroids to the shared .npz file
    centroids_path = paths.data("derived", "loo_centroids_all_subjects.npz")
    if centroids_path.exists():
        existing = dict(np.load(centroids_path, allow_pickle=False))
    else:
        existing = {}
    key = f"centroids_{target_subject_id}"
    existing[key] = centroids
    np.savez(centroids_path, **existing)
    log.info(f"Saved LOSO centroids for subject {target_subject_id} to {centroids_path}")

    # Record the methodological deviation (FR‑002) as required
    deviation_path = paths.data("logs", "methodology_deviations.json")
    deviation_entry = {
        "subject_id": target_subject_id,
        "deviation": "FR-002 deviation: Replaced 'common set of recurrent states' with 'subject-specific LOSO centroids' per Constitution Principle VI."
    }
    if deviation_path.exists():
        with open(deviation_path, "r") as f:
            deviations = json.load(f)
    else:
        deviations = []
    deviations.append(deviation_entry)
    with open(deviation_path, "w") as f:
        json.dump(deviations, f, indent=2)
    log.info(f"Logged methodology deviation for subject {target_subject_id}")

    return centroids

def assign_windows_to_centroids(
    windowed_corrs: np.ndarray,
    centroids: np.ndarray,
) -> np.ndarray:
    """
    Assign each sliding‑window correlation matrix to the nearest centroid.

    Parameters
    ----------
    windowed_corrs : np.ndarray
        Shape (n_windows, V, V) – correlation matrices of the target subject.
    centroids : np.ndarray
        Shape (k, V, V) – LOSO centroids.

    Returns
    -------
    np.ndarray
        1‑D array of length n_windows containing the assigned state IDs (0‑based).
    """
    n_windows, V, _ = windowed_corrs.shape
    k = centroids.shape[0]

    # Vectorise for efficient distance computation
    windows_vec = _vectorise_matrices(windowed_corrs)   # (n_windows, V*V)
    centroids_vec = _vectorise_matrices(centroids)    # (k, V*V)

    # Squared Euclidean distance via broadcasting
    a2 = np.sum(windows_vec ** 2, axis=1, keepdims=True)   # (n_windows, 1)
    b2 = np.sum(centroids_vec ** 2, axis=1)                # (k,)
    ab = windows_vec @ centroids_vec.T                      # (n_windows, k)
    dists = a2 + b2 - 2 * ab                               # (n_windows, k)

    assignments = np.argmin(dists, axis=1)  # (n_windows,)
    return assignments

def compute_dynamic_metrics(state_ids: np.ndarray) -> Dict[str, Any]:
    """
    Compute dwell‑time and visitation statistics from a sequence of state IDs.

    Parameters
    ----------
    state_ids : np.ndarray
        1‑D array of assigned state IDs for each window.

    Returns
    -------
    dict
        {
            "mean_dwell_time": float,
            "num_visited_states": int,
            "state_dwell_times": Dict[int, float]   # optional detailed per‑state info
        }
    """
    if state_ids.size == 0:
        raise ValueError("state_ids array is empty.")

    # Identify runs of the same state
    diffs = np.diff(state_ids, prepend=state_ids[0] - 1)
    run_starts = np.where(diffs != 0)[0]
    run_lengths = np.diff(np.append(run_starts, state_ids.size))

    mean_dwell = float(np.mean(run_lengths))
    visited = int(len(np.unique(state_ids)))

    # Per‑state average dwell time
    per_state: Dict[int, List[int]] = {}
    for sid, length in zip(state_ids[run_starts], run_lengths):
        per_state.setdefault(int(sid), []).append(int(length))
    per_state_avg = {sid: float(np.mean(lens)) for sid, lens in per_state.items()}

    return {
        "mean_dwell_time": mean_dwell,
        "num_visited_states": visited,
        "state_dwell_times": per_state_avg,
    }

###########################################################################
# Public API
###########################################################################

def process_subject_functional(
    subject_id: str,
    fmri_data: np.ndarray,
    other_fmri_data: List[np.ndarray],
    window_length: int = 30,
    step: int = 1,
    k_means_k: int = 5,
) -> Dict[str, Any]:
    """
    End‑to‑end functional processing for a single subject.

    This function:
    1. Computes sliding‑window correlation matrices for ``subject_id``.
    2. Generates LOSO centroids using ``other_fmri_data``.
    3. Assigns each window to a centroid (state).
    4. Derives dynamic metrics.
    5. Persists intermediate artefacts required downstream.

    Parameters
    ----------
    subject_id : str
        Identifier of the target subject.
    fmri_data : np.ndarray
        fMRI time‑series for the target subject (T × V).
    other_fmri_data : List[np.ndarray]
        fMRI time‑series for all *other* subjects in the cohort.
    window_length : int, optional
        Length of the sliding window in TRs (default: 30).
    step : int, optional
        Step size between windows (default: 1).
    k_means_k : int, optional
        Number of k‑means clusters / recurrent states (default: 5).

    Returns
    -------
    dict
        Dictionary containing:
        - ``subject_id``
        - ``state_assignments`` (np.ndarray of shape (n_windows,))
        - ``dynamic_metrics`` (dict from ``compute_dynamic_metrics``)
    """
    log.info(f"Processing functional data for subject {subject_id}")

    # 1. Sliding‑window correlations for the target subject
    windowed_corrs = _sliding_window_correlation(fmri_data, window_length, step)
    log.debug(
        f"Subject {subject_id}: computed {windowed_corrs.shape[0]} windows of size {windowed_corrs.shape[1]}"
    )

    # 2. LOSO centroids (saved internally)
    centroids = generate_loso_centroids(
        target_subject_id=subject_id,
        other_fmri_data=other_fmri_data,
        window_length=window_length,
        step=step,
        k_means_k=k_means_k,
    )

    # 3. Assign windows to centroids
    state_ids = assign_windows_to_centroids(windowed_corrs, centroids)

    # 4. Compute dynamic metrics
    dyn_metrics = compute_dynamic_metrics(state_ids)

    # 5. Persist per‑subject state assignments (Task T017 output)
    # ------------------------------------------------------------------
    # a) State assignments (subject_id, window_index, state_id)
    assignments_path = paths.data("derived", "state_assignments.csv")
    write_header = not assignments_path.exists()
    df_assign = pd.DataFrame(
        {
            "subject_id": [subject_id] * len(state_ids),
            "window_index": np.arange(len(state_ids)),
            "state_id": state_ids,
        }
    )
    with open(assignments_path, "a", newline="") as f:
        df_assign.to_csv(f, index=False, header=write_header)

    # b) Dynamic metrics per state (subject_id, state_id, mean_dwell_time, num_visits)
    dyn_metrics_path = paths.data("derived", "dynamic_metrics.csv")
    write_header_dyn = not dyn_metrics_path.exists()
    # Compute per‑state visit counts
    k = centroids.shape[0]
    visit_counts = np.bincount(state_ids, minlength=k)
    rows = []
    for state_id in range(k):
        mean_dwell = dyn_metrics["state_dwell_times"].get(state_id, np.nan)
        num_visits = int(visit_counts[state_id])
        rows.append({
            "subject_id": subject_id,
            "state_id": state_id,
            "mean_dwell_time": mean_dwell,
            "num_visits": num_visits,
        })
    df_dyn = pd.DataFrame(rows)
    with open(dyn_metrics_path, "a", newline="") as f:
        df_dyn.to_csv(f, index=False, header=write_header_dyn)

    log.info(f"Wrote state assignments for {subject_id} to {assignments_path}")
    log.info(f"Wrote dynamic metrics for {subject_id} to {dyn_metrics_path}")

    return {
        "subject_id": subject_id,
        "state_assignments": state_ids,
        "dynamic_metrics": dyn_metrics,
    }

###########################################################################
# Cohort‑level helper (Task T016)
###########################################################################

def _discover_subject_ids(raw_dir: Path) -> List[str]:
    """
    Scan the raw data directory for subject folders and return a list of
    subject identifiers (without the ``sub-`` prefix).

    Parameters
    ----------
    raw_dir : Path
        Path to ``data/raw`` where BIDS subject folders reside.

    Returns
    -------
    List[str]
        Subject IDs (e.g., ``'100307'``).
    """
    subjects = []
    for entry in raw_dir.iterdir():
        if entry.is_dir() and entry.name.startswith("sub-"):
            subjects.append(entry.name.replace("sub-", ""))
    subjects.sort()
    return subjects

def run_loso_pipeline() -> None:
    """
    Run the full LOSO pipeline for **all** subjects in the cohort.

    This function:
    1. Discovers subject IDs from ``data/raw``.
    2. For each subject, loads its fMRI data and the fMRI data of all other subjects.
    3. Calls :func:`process_subject_functional` to generate centroids,
       state assignments and dynamic metrics.
    4. Records any subjects that fail processing in ``data/logs/exclusion_log.json``.
    5. Ensures that the required artefacts
       ``loo_centroids_all_subjects.npz``,
       ``state_assignments.csv`` and
       ``dynamic_metrics.csv`` as well as ``methodology_deviations.json`` are written.

    The configuration parameters (window length, step, k) are taken from
    ``code/config.py`` via :func:`get_config_dict`.
    """
    config = get_config_dict()
    window_length = config.get("WINDOW_LENGTH_BASELINE", 30)
    step = config.get("WINDOW_STEP", 1)
    k_means_k = config.get("K_MEANS_K", 5)

    # Ensure the exclusion log exists
    exclusion_log_path = paths.data("logs", "exclusion_log.json")
    if exclusion_log_path.exists():
        with open(exclusion_log_path, "r") as f:
            exclusion_log = json.load(f)
    else:
        exclusion_log = []

    raw_dir = paths.data("raw")
    subject_ids = _discover_subject_ids(raw_dir)

    if not subject_ids:
        log.error(f"No subject folders found in {raw_dir}.")
        raise RuntimeError("LOSO pipeline cannot run without subject data.")

    # Pre‑load all fMRI data once to avoid repeated disk I/O
    fmri_cache: Dict[str, np.ndarray] = {}
    for sid in subject_ids:
        try:
            fmri_cache[sid] = load_fmri(sid)
        except Exception as exc:
            log.error(f"Failed to load fMRI for subject {sid}: {exc}")
            exclusion_log.append(
                {"subject_id": sid, "reason": "fMRI load failure", "exception": str(exc)}
            )

    # Process each subject
    for sid in subject_ids:
        if sid not in fmri_cache:
            # Already logged as exclusion
            continue
        try:
            target_fmri = fmri_cache[sid]
            other_fmri = [
                fmri_cache[other]
                for other in subject_ids
                if other != sid and other in fmri_cache
            ]
            if not other_fmri:
                raise RuntimeError("No other subjects' fMRI data available for LOSO.")
            process_subject_functional(
                subject_id=sid,
                fmri_data=target_fmri,
                other_fmri_data=other_fmri,
                window_length=window_length,
                step=step,
                k_means_k=k_means_k,
            )
        except Exception as exc:
            log.exception(f"LOSO processing failed for subject {sid}: {exc}")
            exclusion_log.append(
                {"subject_id": sid, "reason": "LOSO processing failure", "exception": str(exc)}
            )

    # Write (or overwrite) the exclusion log
    with open(exclusion_log_path, "w") as f:
        json.dump(exclusion_log, f, indent=2)
    log.info(f"Exclusion log written to {exclusion_log_path}")

###########################################################################
# CLI entry point
###########################################################################

if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Run functional LOSO pipeline."
    )
    parser.add_argument(
        "subject_id",
        nargs="?",
        type=str,
        help="Subject identifier (e.g., 100307). If omitted, the script runs the full cohort.",
    )
    parser.add_argument(
        "--window-length",
        type=int,
        default=None,
        help="Sliding window length in TRs (default from config).",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=None,
        help="Step size between windows (default from config).",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=None,
        help="Number of k‑means clusters (states) (default from config).",
    )
    args = parser.parse_args()

    # Ensure data are present; this will raise if download fails.
    try:
        download_hcp_dataset()
    except Exception as exc:
        log.error(f"Failed to download dataset: {exc}")
        sys.exit(1)

    # Load configuration defaults
    cfg = get_config_dict()
    win_len = args.window_length if args.window_length is not None else cfg.get("WINDOW_LENGTH_BASELINE", 30)
    step = args.step if args.step is not None else cfg.get("WINDOW_STEP", 1)
    k_clusters = args.k if args.k is not None else cfg.get("K_MEANS_K", 5)

    if args.subject_id:
        # Process a single subject
        try:
            fmri_target = load_fmri(args.subject_id)
        except Exception as exc:
            log.error(f"Could not load fMRI for subject {args.subject_id}: {exc}")
            sys.exit(1)

        # Load all other subjects' fMRI data
        raw_fmri_dir = Path(paths.data()).parent / "raw"
        other_subjects = []
        for sub_dir in raw_fmri_dir.iterdir():
            if not sub_dir.is_dir():
                continue
            sid = sub_dir.name.replace("sub-", "")
            if sid == args.subject_id:
                continue
            try:
                other_fmri = load_fmri(sid)
                other_subjects.append(other_fmri)
            except Exception:
                continue

        if not other_subjects:
            log.error("No other subjects available for LOSO centroid generation.")
            sys.exit(1)

        try:
            result = process_subject_functional(
                subject_id=args.subject_id,
                fmri_data=fmri_target,
                other_fmri_data=other_subjects,
                window_length=win_len,
                step=step,
                k_means_k=k_clusters,
            )
            log.info(f"Functional processing completed for {args.subject_id}")
            print(json.dumps(result, indent=2))
        except Exception as exc:
            log.exception(f"Functional processing failed for {args.subject_id}: {exc}")
            sys.exit(1)
    else:
        # Run the full cohort LOSO pipeline
        try:
            run_loso_pipeline()
        except Exception as exc:
            log.exception(f"Full LOSO pipeline failed: {exc}")
            sys.exit(1)