"""
Network‑level metric extraction for functional connectivity matrices.

Given a Fisher‑z transformed connectivity matrix and an atlas DataFrame,
the functions compute the mean intra‑network connectivity for the three
target networks (auditory, motor, executive) and return a dictionary that
can be written to JSON.
"""

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from .atlas import get_network_roi_indices, TARGET_NETWORKS

__all__ = [
    "compute_network_metrics",
    "save_network_metrics",
]


def _mean_intra_network(z_matrix: np.ndarray, roi_indices: List[int]) -> float:
    """
    Compute the mean Fisher‑z value for all unique ROI pairs within a network.

    Parameters
    ----------
    z_matrix: np.ndarray
        Square Fisher‑z transformed connectivity matrix (n_rois x n_rois).
    roi_indices: List[int]
        List of ROI indices belonging to the network.

    Returns
    -------
    float
        Mean intra‑network connectivity (excluding the diagonal).
    """
    if len(roi_indices) < 2:
        # With a single ROI the intra‑network mean is undefined; return NaN.
        return float("nan")

    submatrix = z_matrix[np.ix_(roi_indices, roi_indices)]
    # Extract upper triangle without diagonal
    triu = np.triu_indices_from(submatrix, k=1)
    values = submatrix[triu]
    return float(np.mean(values))


def compute_network_metrics(
    z_matrix: np.ndarray,
    atlas_df: pd.DataFrame,
    target_networks: List[str] = TARGET_NETWORKS,
) -> Dict[str, float]:
    """
    Compute mean intra‑network Fisher‑z connectivity for each target network.

    Parameters
    ----------
    z_matrix: np.ndarray
        Fisher‑z transformed connectivity matrix.
    atlas_df: pd.DataFrame
        Atlas description DataFrame (as returned by ``load_atlas``).
    target_networks: List[str], optional
        List of network names to process.  Defaults to the three primary
        networks defined in ``TARGET_NETWORKS``.

    Returns
    -------
    Dict[str, float]
        Mapping from network name to mean intra‑network connectivity.
    """
    metrics = {}
    for net in target_networks:
        roi_idxs = get_network_roi_indices(atlas_df, net)
        metrics[net] = _mean_intra_network(z_matrix, roi_idxs)
    return metrics


def save_network_metrics(
    metrics: Dict[str, float],
    subject_id: str,
    output_dir: Path,
) -> Path:
    """
    Write the network metrics dictionary to a JSON file.

    The file is named ``<subject_id>.json`` and placed inside
    ``output_dir`` (which is created if it does not exist).

    Parameters
    ----------
    metrics: Dict[str, float]
        Network‑level metrics as returned by ``compute_network_metrics``.
    subject_id: str
        Identifier of the subject (used for the filename).
    output_dir: Path
        Directory where the JSON file will be stored.

    Returns
    -------
    Path
        Path to the written JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{subject_id}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)
    return out_path