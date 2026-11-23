"""
Functional connectivity computation for a single subject and group aggregation.

This module provides:

* ``fisher_z_transform`` – Fisher‑r‑to‑z transformation.
* ``compute_pearson_correlation_chunked`` – memory‑efficient Pearson correlation.
* ``process_subject_connectivity`` – end‑to‑end processing for one subject,
  returning a ``ConnectivityMatrix`` dataclass (defined in ``data.models``).
* ``generate_group_connectivity_results`` – compute connectivity for a list
  of synthetic subjects, write the stacked array to ``connectivity_matrices.npy``,
  and return the array for downstream statistics.
* ``main`` – CLI entry point that iterates over all cleaned subjects,
  writes per‑subject connectivity matrices (JSON) and network‑level metrics
  (JSON) to the appropriate ``data/processed`` sub‑directories.

The implementation follows the specifications of task **T004** and is
extended to support the synthetic verification pipeline used by
``code/main.py``.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
import nibabel as nib
import pandas as pd

from utils.logging import get_logger
from utils.memory_monitor import check_memory_limit, MemoryLimitExceeded
from data.models import ConnectivityMatrix
from .atlas import load_atlas, TARGET_NETWORKS
from .network_metrics import compute_network_metrics, save_network_metrics

logger = get_logger(__name__)

def fisher_z_transform(r: np.ndarray) -> np.ndarray:
    """
    Apply Fisher's z‑transformation to correlation coefficients.

    Args:
        r: Correlation coefficients (scalar or array).

    Returns:
        Z‑transformed values.
    """
    r_clipped = np.clip(r, -0.9999, 0.9999)
    return 0.5 * np.log((1 + r_clipped) / (1 - r_clipped))


def compute_pearson_correlation_chunked(
    time_series: np.ndarray,
    chunk_size: int = 50,
    memory_limit_gb: float = 7.0,
) -> np.ndarray:
    """
    Compute Pearson correlation matrix with chunked processing to manage memory.

    Args:
        time_series: Shape (n_timepoints, n_rois).
        chunk_size: Number of ROIs to process at once.
        memory_limit_gb: Maximum memory usage in GB.

    Returns:
        Correlation matrix (n_rois, n_rois).
    """
    n_timepoints, n_rois = time_series.shape

    estimated_memory = (n_rois * n_rois * 8) / (1024**3)  # float64 size
    if estimated_memory > memory_limit_gb:
        raise MemoryLimitExceeded(
            f"Estimated memory ({estimated_memory:.2f}GB) exceeds limit ({memory_limit_gb}GB)"
        )

    # Standardise once
    mean_ts = np.mean(time_series, axis=0, keepdims=True)
    std_ts = np.std(time_series, axis=0, keepdims=True)
    std_ts[std_ts == 0] = 1.0
    standardized_ts = (time_series - mean_ts) / std_ts

    corr_matrix = np.zeros((n_rois, n_rois), dtype=np.float64)

    for i_start in range(0, n_rois, chunk_size):
        i_end = min(i_start + chunk_size, n_rois)
        chunk_ts = standardized_ts[:, i_start:i_end]

        for j_start in range(0, n_rois, chunk_size):
            j_end = min(j_start + chunk_size, n_rois)
            other_chunk_ts = standardized_ts[:, j_start:j_end]

            block_corr = np.dot(chunk_ts.T, other_chunk_ts) / (n_timepoints - 1)
            corr_matrix[i_start:i_end, j_start:j_end] = block_corr

    return corr_matrix


def _extract_time_series_from_nifti(
    nifti_path: Path,
    atlas_df: pd.DataFrame,
) -> np.ndarray:
    """
    Extract a (timepoints x n_rois) matrix from a 4‑D NIfTI image.

    The extraction uses the voxel coordinates (x, y, z) provided in the
    atlas CSV.  For each ROI we take the voxel at the integer‑rounded
    coordinate and use its full time‑course.

    Parameters
    ----------
    nifti_path: Path
        Path to the subject's NIfTI file.
    atlas_df: pd.DataFrame
        Atlas DataFrame with columns ``x``, ``y``, ``z``.

    Returns
    -------
    np.ndarray
        Array of shape (n_timepoints, n_rois).
    """
    img = nib.load(str(nifti_path))
    data = img.get_fdata()  # shape: (X, Y, Z, T)
    if data.ndim != 4:
        raise ValueError(f"NIfTI image at {nifti_path} is not 4‑D.")

    n_timepoints = data.shape[3]
    n_rois = len(atlas_df)
    ts = np.empty((n_timepoints, n_rois), dtype=np.float32)

    for idx, row in atlas_df.iterrows():
        x = int(round(row["x"]))
        y = int(round(row["y"]))
        z = int(round(row["z"]))
        # Guard against out‑of‑bounds coordinates
        if (
            x < 0
            or y < 0
            or z < 0
            or x >= data.shape[0]
            or y >= data.shape[1]
            or z >= data.shape[2]
        ):
            raise IndexError(
                f"Atlas voxel coordinate ({x},{y},{z}) out of bounds for NIfTI shape {data.shape[:3]}"
            )
        ts[:, idx] = data[x, y, z, :]

    return ts


def process_subject_connectivity(
    subject_id: str,
    nifti_path: Path,
    atlas_df: pd.DataFrame,
    chunk_size: int = 50,
) -> ConnectivityMatrix:
    """
    Process a single subject's NIfTI file into a Fisher‑z transformed
    connectivity matrix and write the results to disk.

    Parameters
    ----------
    subject_id: str
        Identifier of the subject (used for output filenames).
    nifti_path: Path
        Path to the subject's NIfTI image.
    atlas_df: pd.DataFrame
        Atlas description DataFrame.
    chunk_size: int, optional
        Chunk size for correlation computation.

    Returns
    -------
    ConnectivityMatrix
        Dataclass instance containing the subject ID, the z‑matrix and the
        path to the atlas used.
    """
    logger.info(f"Loading NIfTI for subject {subject_id} from {nifti_path}")
    time_series = _extract_time_series_from_nifti(nifti_path, atlas_df)

    # Compute Pearson correlation
    corr_matrix = compute_pearson_correlation_chunked(time_series, chunk_size=chunk_size)

    # Fisher‑z
    z_matrix = fisher_z_transform(corr_matrix)

    # Build dataclass
    matrix = ConnectivityMatrix(
        subject_id=subject_id,
        matrix=z_matrix,
        atlas_path=str(atlas_df.attrs.get("source_path", "")),
    )

    return matrix


def _save_connectivity_json(
    conn_matrix: ConnectivityMatrix,
    output_dir: Path,
) -> Path:
    """
    Serialize a ``ConnectivityMatrix`` to JSON.

    The JSON structure matches the contract defined in
    ``connectivity.schema.yaml``:

    {
        "subject_id": "...",
        "atlas_path": "...",
        "n_rois": <int>,
        "z_matrix": [[...], [...], ...]
    }
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{conn_matrix.subject_id}.json"
    payload = {
        "subject_id": conn_matrix.subject_id,
        "atlas_path": conn_matrix.atlas_path,
        "n_rois": conn_matrix.matrix.shape[0],
        "z_matrix": conn_matrix.matrix.tolist(),
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    logger.debug(f"Wrote connectivity JSON for {conn_matrix.subject_id} to {out_path}")
    return out_path


def generate_group_connectivity_results(
    subjects_data: List[Dict[str, Any]],
    atlas_path: Path,
    output_dir: Path,
    chunk_size: int = 50,
) -> Tuple[np.ndarray, List[str]]:
    """
    Compute connectivity matrices for a list of synthetic subjects.

    Parameters
    ----------
    subjects_data: list of dict
        Each dict must contain ``subject_id`` and ``time_series`` keys.
    atlas_path: Path
        Path to the Schaefer atlas CSV.
    output_dir: Path
        Directory where ``connectivity_matrices.npy`` will be saved.
    chunk_size: int
        Chunk size for the chunked correlation routine.

    Returns
    -------
    tuple
        - ``matrices`` – ``np.ndarray`` of shape (N, R, R) containing Fisher‑z matrices.
        - ``subject_ids`` – list of subject identifiers in the same order.
    """
    logger.info(f"Loading atlas from {atlas_path}")
    atlas_df = load_atlas(atlas_path)
    atlas_df.attrs["source_path"] = str(atlas_path)

    matrices = []
    subject_ids = []

    for entry in subjects_data:
        subject_id = entry["subject_id"]
        ts = entry["time_series"]
        # Compute correlation and Fisher‑z
        corr = compute_pearson_correlation_chunked(ts, chunk_size=chunk_size)
        z = fisher_z_transform(corr)
        matrices.append(z)
        subject_ids.append(subject_id)

    matrices_arr = np.stack(matrices)  # (N, R, R)

    # Write the stacked array to disk for downstream steps
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "connectivity_matrices.npy"
    np.save(str(out_path), matrices_arr)
    logger.info(f"Saved stacked connectivity matrices to {out_path}")

    return matrices_arr, subject_ids


def main() -> None:
    """
    CLI entry point for the connectivity stage.

    The script expects the cleaned subjects Parquet file generated by the
    preprocessing step (``data/processed/subjects_cleaned.parquet``).  For
    each subject it:
        1. Loads the subject's NIfTI file (``data/raw/mock_nifti/<id>.nii.gz``).
        2. Extracts ROI time‑courses using the atlas CSV.
        3. Computes a Pearson correlation matrix and applies Fisher‑z.
        4. Saves the matrix as JSON under ``data/processed/connectivity``.
        5. Computes mean intra‑network Fisher‑z values for the three target
           networks and saves them under ``data/processed/network_metrics``.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute per‑subject functional connectivity and network metrics."
    )
    parser.add_argument(
        "--subjects-parquet",
        type=str,
        default="data/processed/subjects_cleaned.parquet",
        help="Path to the cleaned subjects Parquet file.",
    )
    parser.add_argument(
        "--atlas-path",
        type=str,
        default="data/atlas/schaefer_200.csv",
        help="Path to the Schaefer‑200 atlas CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Base output directory for connectivity and network metric JSON files.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50,
        help="Chunk size for correlation computation (memory‑friendly).",
    )
    args = parser.parse_args()

    subjects_path = Path(args.subjects_parquet)
    if not subjects_path.is_file():
        raise FileNotFoundError(f"Cleaned subjects file not found at {subjects_path}")

    atlas_path = Path(args.atlas_path)
    atlas_df = load_atlas(atlas_path)
    # Store source path for provenance in the JSON output
    atlas_df.attrs["source_path"] = str(atlas_path)

    output_base = Path(args.output_dir)
    conn_output_dir = output_base / "connectivity"
    net_output_dir = output_base / "network_metrics"

    subjects_df = pd.read_parquet(str(subjects_path))

    for _, row in subjects_df.iterrows():
        subject_id = row["subject_id"]
        nifti_path = Path("data/raw/mock_nifti") / f"{subject_id}.nii.gz"
        if not nifti_path.is_file():
            logger.warning(f"NIfTI file missing for subject {subject_id}; skipping.")
            continue

        try:
            conn_matrix = process_subject_connectivity(
                subject_id=subject_id,
                nifti_path=nifti_path,
                atlas_df=atlas_df,
                chunk_size=args.chunk_size,
            )

            # Save connectivity JSON
            _save_connectivity_json(conn_matrix, conn_output_dir)

            # Compute and save network‑level metrics
            metrics = compute_network_metrics(
                conn_matrix.matrix,
                atlas_df,
                target_networks=TARGET_NETWORKS,
            )
            save_network_metrics(metrics, subject_id, net_output_dir)

            # Periodically check memory usage
            if (int(subject_id.split("_")[-1]) % 10) == 0:
                check_memory_limit()

        except Exception as exc:
            logger.error(f"Failed processing for subject {subject_id}: {exc}")
            continue

    logger.info("Connectivity and network‑metric computation completed successfully.")


if __name__ == "__main__":
    main()
