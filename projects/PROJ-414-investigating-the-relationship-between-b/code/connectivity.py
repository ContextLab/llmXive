"""Sliding‑window functional connectivity and vertex‑block descriptor computation (T004).

This module provides a ``main()`` entry point that reads per‑subject
block‑mean time‑series CSV files produced by ``extract_rois``, applies
a rectangular sliding window, computes a Ledoit‑Wolf regularized
Pearson correlation matrix for each window, and writes a CSV of
graph‑theoretic descriptors per subject.

The implementation is deliberately defensive: missing input files
are reported as warnings rather than fatal errors so that the
orchestrator can continue with later stages. All imports are
absolute (``import graph_metrics``) to avoid relative‑import failures
when the module is executed as a script or imported by the test
suite.
"""
import argparse
import csv
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf

import config
import graph_metrics
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _load_subject_timeseries(subject_id: str) -> np.ndarray:
    """Load the block‑mean matrix for *subject_id*.

    Returns a ``(n_timepoints, n_blocks)`` ``float64`` array.
    The CSV file is expected at ``data/derived/roi_timeseries_<id>.csv``.
    """
    ts_path = paths.data("derived", f"roi_timeseries_{subject_id}.csv")
    if not ts_path.is_file():
        raise FileNotFoundError(f"timeseries file missing for subject {subject_id}")
    df = pd.read_csv(ts_path)
    # Pivot to wide format: rows = timepoints, columns = roi_id
    wide = df.pivot(index="timepoint", columns="roi_id", values="value")
    # Ensure columns are ordered ``roi_1`` … ``roi_100``
    ordered_cols = [f"roi_{i}" for i in range(1, config.N_VERTEX_BLOCKS + 1)]
    return wide[ordered_cols].to_numpy(dtype=np.float64)

def _window_indices(n_timepoints: int, window_frames: int, step_frames: int):
    """Yield ``(start, end)`` indices for each sliding window."""
    start = 0
    while start + window_frames <= n_timepoints:
        yield start, start + window_frames
        start += step_frames

def _process_subject(subject_id: str, window_seconds: float, step_seconds: float):
    """Compute descriptors for *subject_id* and write the result CSV."""
    try:
        data = _load_subject_timeseries(subject_id)
    except Exception as exc:
        log.error("Failed to load timeseries for %s: %s", subject_id, exc)
        return

    tr = config.TR_SECONDS
    window_frames = int(round(window_seconds / tr))
    step_frames = int(round(step_seconds / tr))

    if window_frames < config.MIN_TIMEPOINTS_PER_WINDOW:
        log.warning(
            "Subject %s: window size %d frames < %d min; skipping",
            subject_id,
            window_frames,
            config.MIN_TIMEPOINTS_PER_WINDOW,
        )
        return

    rows = []
    for win_idx, (start, end) in enumerate(_window_indices(data.shape[0], window_frames, step_frames)):
        window_data = data[start:end, :]
        if window_data.shape[0] < config.MIN_TIMEPOINTS_PER_WINDOW:
            log.info("Subject %s window %d too short (%d pts); skipped", subject_id, win_idx, window_data.shape[0])
            continue
        # Ledoit‑Wolf shrinkage covariance → correlation
        lw = LedoitWolf()
        lw.fit(window_data)
        cov = lw.covariance_
        # Convert to correlation matrix
        stddev = np.sqrt(np.diag(cov))
        corr = cov / np.outer(stddev, stddev)
        np.fill_diagonal(corr, 1.0)

        # Graph descriptors
        efficiency = graph_metrics.global_efficiency(corr)
        modularity = graph_metrics.louvain_modularity(corr, seed=config.LOUVAIN_SEED)
        # Louvain returns communities; need to recompute for participation
        G = graph_metrics._build_weighted_graph(corr)
        communities = list(graph_metrics._louvain_communities(G, seed=config.LOUVAIN_SEED))
        participation = graph_metrics.participation_coefficient(corr, communities)

        rows.append({
            "subject_id": subject_id,
            "window_index": win_idx,
            "global_efficiency": efficiency,
            "modularity": modularity,
            "participation_coefficient": participation,
        })

    if not rows:
        log.warning("No windows produced for subject %s", subject_id)
        return

    out_path = paths.data("derived", f"metrics_{subject_id}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["subject_id", "window_index",
                                                    "global_efficiency", "modularity",
                                                    "participation_coefficient"])
        writer.writeheader()
        writer.writerows(rows)

def main(argv=None) -> int:
    """Entry point invoked by the orchestrator.

    ``argv`` is ignored – the orchestrator supplies the global
    configuration via ``config``.
    """
    if isinstance(argv, argparse.Namespace):
        argv = None
    parser = argparse.ArgumentParser(description="Compute sliding‑window connectivity descriptors")
    parser.add_argument("--shard", type=Path, default=None, help="unused placeholder")
    args = parser.parse_args(argv)

    # Discover subjects from the derived ROI timeseries files.
    derived_dir = paths.data("derived")
    pattern = "roi_timeseries_*.csv"
    subject_files = list(derived_dir.glob(pattern))
    if not subject_files:
        log.warning("No ROI timeseries files found; connectivity stage will do nothing.")
        return 0

    for ts_file in subject_files:
        sid = ts_file.stem.replace("roi_timeseries_", "")
        _process_subject(
            subject_id=sid,
            window_seconds=config.DEFAULT_WINDOW_SECONDS,
            step_seconds=config.DEFAULT_STEP_SECONDS,
        )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
