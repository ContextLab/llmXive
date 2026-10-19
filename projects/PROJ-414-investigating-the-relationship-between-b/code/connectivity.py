"""Sliding‑window functional connectivity and vertex‑block descriptor generation.

This module implements the **T004** pipeline stage.  It reads the per‑subject
block‑mean time‑series CSV files produced by ``extract_rois.py``, applies a
rectangular sliding window, computes a Ledoit‑Wolf regularised covariance
for each window, converts it to a correlation matrix, and finally extracts
three graph‑theoretic descriptors (global efficiency, modularity, and
participation coefficient) for each window.

The output for each subject is written to
``data/derived/metrics_<subject_id>.csv`` and conforms to the JSON schema
located at ``specs/001-investigating-the-relationship-between-b/contracts/network_metrics.schema.yaml``.
"""
import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx
from sklearn.covariance import LedoitWolf

import config  # pinned parameters
from llmxive_toolkit import paths, get_logger
from . import graph_metrics

log = get_logger(__name__)

def _load_subject_timeseries(subject_id: str) -> np.ndarray:
    """Load the block‑mean matrix for *subject_id*.

    Returns a ``(n_timepoints, n_blocks)`` ``float64`` array.
    """
    ts_path = paths.data("derived", f"roi_timeseries_{subject_id}.csv")
    if not ts_path.is_file():
        raise FileNotFoundError(f"ROI timeseries not found for subject {subject_id}")
    df = pd.read_csv(ts_path)
    # Ensure deterministic block ordering.
    block_ids = sorted(df["roi_id"].unique(), key=lambda x: int(x.split("_")[1]))
    matrix = df.pivot(index="timepoint", columns="roi_id", values="value")
    matrix = matrix[block_ids].to_numpy(dtype=np.float64)
    return matrix

def _window_indices(n_timepoints: int, window_frames: int, step_frames: int):
    """Yield (start, end) indices for each sliding window."""
    if window_frames < config.MIN_TIMEPOINTS_PER_WINDOW:
        log.debug(
            "Window size %d frames < minimum %d frames – skipping all windows",
            window_frames,
            config.MIN_TIMEPOINTS_PER_WINDOW,
        )
        return iter([])  # no windows
    start = 0
    while start + window_frames <= n_timepoints:
        yield start, start + window_frames
        start += step_frames

def _process_subject(subject_id: str, window_seconds: float, step_seconds: float):
    """Compute descriptors for *subject_id* and write the result CSV."""
    matrix = _load_subject_timeseries(subject_id)
    n_timepoints, n_blocks = matrix.shape
    if n_blocks != config.N_VERTEX_BLOCKS:
        raise ValueError(
            f"Subject {subject_id} block matrix has {n_blocks} blocks "
            f"(expected {config.N_VERTEX_BLOCKS})"
        )
    # Convert seconds to frame counts (rounded to nearest integer).
    window_frames = max(1, int(round(window_seconds / config.TR_SECONDS)))
    step_frames = max(1, int(round(step_seconds / config.TR_SECONDS)))

    rows = []
    for win_id, (i_start, i_end) in enumerate(
        _window_indices(n_timepoints, window_frames, step_frames)
    ):
        window_data = matrix[i_start:i_end, :]  # (window_frames, n_blocks)

        # Ledoit‑Wolf regularised covariance.
        lw = LedoitWolf()
        lw.fit(window_data)
        cov = lw.covariance_

        # Convert covariance to correlation matrix.
        stddev = np.sqrt(np.diag(cov))
        with np.errstate(invalid="ignore", divide="ignore"):
            corr = cov / np.outer(stddev, stddev)
            corr = np.nan_to_num(corr)  # replace NaNs with 0.
        np.fill_diagonal(corr, 1.0)

        # Graph descriptors.
        ge = graph_metrics.global_efficiency(corr)
        modularity = graph_metrics.louvain_modularity(corr, seed=config.LOUVAIN_SEED)

        # Obtain Louvain community partition for participation coefficient.
        G = nx.from_numpy_array(np.abs(corr), create_using=nx.Graph)
        G.remove_edges_from(nx.selfloop_edges(G))
        communities = nx.algorithms.community.louvain_communities(
            G, seed=config.LOUVAIN_SEED
        )
        pc = graph_metrics.participation_coefficient(corr, communities)

        rows.append({
            "subject_id": subject_id,
            "window_id": int(win_id),
            "window_seconds": float(window_seconds),
            "step_seconds": float(step_seconds),
            "global_efficiency": float(ge),
            "modularity": float(modularity),
            "participation_coefficient": float(pc),
        })
        log.debug(
            "Subject %s – window %d: GE=%.4f, Mod=%.4f, PC=%.4f",
            subject_id,
            win_id,
            ge,
            modularity,
            pc,
        )

    # Write per‑subject CSV.
    out_path = paths.data("derived", f"metrics_{subject_id}.csv")
    pd.DataFrame(rows).to_csv(out_path, index=False)
    log.info(
        "Wrote %d window rows for subject %s to %s",
        len(rows),
        subject_id,
        out_path,
    )

def main(argv=None) -> int:
    """Entry point invoked by ``run_all.py``.

    The orchestrator supplies a parsed ``argparse.Namespace`` containing
    the global pipeline arguments (seed, window, step, etc.).  This function
    ignores the seed (already fixed in other stages) and uses the window
    and step values to drive the sliding‑window computation.
    """
    parser = argparse.ArgumentParser(description="Sliding‑window connectivity (T004)")
    parser.add_argument("--window", type=float, default=config.DEFAULT_WINDOW_SECONDS)
    parser.add_argument("--step", type=float, default=config.DEFAULT_STEP_SECONDS)
    args = parser.parse_args(argv)

    # Discover all ROI timeseries files produced by the extraction stage.
    roi_files = sorted(paths.data("derived", "roi_timeseries_*.csv"))
    if not roi_files:
        raise RuntimeError(
            "No ROI timeseries files found – ensure the 'extract' stage has run."
        )

    subject_ids = [
        f.stem.replace("roi_timeseries_", "")
        for f in roi_files
    ]

    log.info(
        "Computing connectivity descriptors for %d subjects (window=%.1fs, step=%.1fs)",
        len(subject_ids),
        args.window,
        args.step,
    )
    for sid in subject_ids:
        _process_subject(sid, args.window, args.step)

    log.info("Connectivity stage complete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
