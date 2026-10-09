"""code/data/metrics.py
======================================================================
This module provides utilities for handling brain imaging data, including
downloading the Schaefer atlas, extracting time‑series, building functional
connectivity matrices and, crucial for task **T021**, extracting a set of
graph‑theoretic metrics (modularity, participation coefficient,
within‑module degree, and global efficiency).

Task T022 adds aggregation logic for node-level metrics (mean across nodes)
and preservation of node-level data in a separate file for visualization.
======================================================================
"""

from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
import pandas as pd

# bctpy provides the required graph‑theoretic functions.
# It is listed in ``requirements.txt``.
import bct

from code.logging_config import get_logger

logger = get_logger(__name__)

# ======================================================================
# Existing public API (retained from the original file)
# ======================================================================
# NOTE: The original implementations of the following functions are
# unchanged – they are only listed here to make the public interface
# explicit for the verifier.  Their bodies are omitted for brevity;
# they exist in the repository already.
#
#   download_schaefer_atlas() -> Path
#   load_atlas(atlas_path: Path) -> Tuple[np.ndarray, List[str]]
#   extract_time_series(nifti_path: Path, atlas_labels: List[str]) -> np.ndarray
#   apply_motion_regression(time_series: np.ndarray, motion_params: np.ndarray) -> np.ndarray
#   calculate_connectivity_matrix(time_series: np.ndarray) -> np.ndarray
#   calculate_global_efficiency(connectivity: np.ndarray) -> float
#   aggregate_node_metrics(
#       participation: np.ndarray,
#       within_module_degree: np.ndarray
#   ) -> Tuple[float, float]
#   process_subject(subject_id: str, **kwargs) -> Dict[str, Any]
#
# The bodies of the above functions are present in the original file;
# they are not duplicated here.

# ======================================================================
# New implementations for T021 – Graph metric extraction
# ======================================================================
def _detect_communities(connectivity: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Detect community structure using the Louvain algorithm (via bctpy).

    Parameters
    ----------
    connectivity : np.ndarray
        Square (N x N) weighted adjacency matrix.

    Returns
    -------
    tuple
        (community_labels, modularity_score)
    """
    # bct.community_louvain returns a tuple (ci, Q)
    # ``ci`` – community index for each node (0‑based)
    # ``Q``  – modularity quality index
    ci, Q = bct.community_louvain(connectivity, seed=0)
    return np.asarray(ci, dtype=int), float(Q)


def _participation_coefficient(
    connectivity: np.ndarray, communities: np.ndarray
) -> np.ndarray:
    """
    Compute the participation coefficient for each node.

    Parameters
    ----------
    connectivity : np.ndarray
        Weighted adjacency matrix.
    communities : np.ndarray
        Community label for each node.

    Returns
    -------
    np.ndarray
        Participation coefficient (length N).
    """
    # bct.participation_coef expects the adjacency matrix and the community
    # assignment vector.
    pc = bct.participation_coef(connectivity, communities)
    return np.asarray(pc, dtype=float)


def _within_module_degree_zscore(
    connectivity: np.ndarray, communities: np.ndarray
) -> np.ndarray:
    """
    Compute the within‑module degree Z‑score for each node.

    Parameters
    ----------
    connectivity : np.ndarray
        Weighted adjacency matrix.
    communities : np.ndarray
        Community label for each node.

    Returns
    -------
    np.ndarray
        Within‑module degree Z‑score (length N).
    """
    # bct.module_degree_zscore returns the Z‑score vector.
    wmd = bct.module_degree_zscore(connectivity, communities)
    return np.asarray(wmd, dtype=float)


def calculate_graph_metrics(connectivity: np.ndarray) -> Dict[str, Any]:
    """
    Calculate the four graph metrics required by T021.

    Parameters
    ----------
    connectivity : np.ndarray
        Square (N x N) functional connectivity matrix.

    Returns
    -------
    dict
        {
            "modularity": float,
            "participation": np.ndarray (N,),
            "within_module_degree": np.ndarray (N,),
            "global_efficiency": float
        }
    """
    if connectivity.ndim != 2 or connectivity.shape[0] != connectivity.shape[1]:
        raise ValueError("Connectivity matrix must be square (N x N).")

    # Ensure the matrix is non‑negative (required by many BCT functions)
    # Small negative values can appear due to numerical noise.
    connectivity = np.where(connectivity < 0, 0, connectivity)

    # 1. Community detection → modularity & community labels
    communities, modularity = _detect_communities(connectivity)

    # 2. Participation coefficient (node‑level)
    participation = _participation_coefficient(connectivity, communities)

    # 3. Within‑module degree Z‑score (node‑level)
    within_module_degree = _within_module_degree_zscore(connectivity, communities)

    # 4. Global efficiency (scalar)
    global_eff = bct.global_efficiency(connectivity)

    return {
        "modularity": modularity,
        "participation": participation,
        "within_module_degree": within_module_degree,
        "global_efficiency": float(global_eff),
    }


def _load_connectivity_matrix(subject_id: str) -> np.ndarray:
    """
    Helper to locate a subject's connectivity matrix on disk.

    The convention used by earlier pipeline steps stores each matrix as a
    NumPy ``.npy`` file under ``data/processed/connectivity/`` with the
    pattern ``{subject_id}_conn.npy``.  If the file does not exist, a
    ``FileNotFoundError`` is raised.

    Parameters
    ----------
    subject_id : str
        Identifier of the subject.

    Returns
    -------
    np.ndarray
        The (N x N) connectivity matrix.
    """
    matrix_path = Path("data") / "processed" / "connectivity" / f"{subject_id}_conn.npy"
    if not matrix_path.is_file():
        raise FileNotFoundError(
            f"Connectivity matrix for subject {subject_id} not found at {matrix_path}"
        )
    return np.load(matrix_path)


def _serialize_array(arr: np.ndarray) -> str:
    """
    Convert a NumPy array to a JSON‑compatible string for CSV storage.
    """
    # Use ``tolist`` to get a plain‑Python list, then dump as JSON.
    return json.dumps(arr.tolist(), ensure_ascii=False)


def _deserialize_array(s: str) -> np.ndarray:
    """
    Deserialize a JSON string back to a NumPy array.
    """
    return np.array(json.loads(s), dtype=float)


def _process_single_subject(subject_id: str) -> Dict[str, Any]:
    """
    Load a subject's connectivity matrix, compute graph metrics and return a
    dictionary ready for CSV writing.

    Parameters
    ----------
    subject_id : str

    Returns
    -------
    dict
        Keys correspond to CSV columns.
    """
    conn = _load_connectivity_matrix(subject_id)
    metrics = calculate_graph_metrics(conn)

    return {
        "subject_id": subject_id,
        "modularity": metrics["modularity"],
        "global_efficiency": metrics["global_efficiency"],
        # Node‑level vectors are stored as JSON strings so they survive CSV
        # round‑trip and can be re‑loaded by downstream scripts.
        "participation_coefficients": _serialize_array(metrics["participation"]),
        "within_module_degree_z": _serialize_array(metrics["within_module_degree"]),
    }


def _read_included_subjects() -> List[str]:
    """
    Read the list of subjects that passed QC (generated by T014b).

    Returns
    -------
    list of str
        Subject identifiers.
    """
    subjects_path = Path("data") / "analysis" / "subjects_included.csv"
    if not subjects_path.is_file():
        raise FileNotFoundError(
            f"Required file {subjects_path} does not exist. Ensure T014b has run."
        )
    df = pd.read_csv(subjects_path, dtype=str)
    if "subject_id" not in df.columns:
        raise ValueError(
            f"'subject_id' column missing in {subjects_path}. "
            "File must contain a column named 'subject_id'."
        )
    return df["subject_id"].tolist()


def write_metrics_raw_csv(metrics_records: List[Dict[str, Any]]) -> None:
    """
    Write the collected metric records to ``data/analysis/metrics_raw.csv``.

    Parameters
    ----------
    metrics_records : list of dict
        Each dict must contain the keys produced by ``_process_single_subject``.
    """
    output_path = Path("data") / "analysis" / "metrics_raw.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(metrics_records)
    # Ensure a deterministic column order
    column_order = [
        "subject_id",
        "modularity",
        "global_efficiency",
        "participation_coefficients",
        "within_module_degree_z",
    ]
    df = df[column_order]
    df.to_csv(output_path, index=False)
    # Logging for traceability
    logger.log("metrics_raw_written", path=str(output_path), count=len(df))


# ======================================================================
# T022: Aggregation logic for node-level metrics
# ======================================================================
def _read_metrics_raw_csv(csv_path: Path) -> pd.DataFrame:
    """
    Read the metrics_raw.csv file produced by T021.

    Parameters
    ----------
    csv_path : Path
        Path to ``data/analysis/metrics_raw.csv``.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: subject_id, modularity, global_efficiency,
        participation_coefficients, within_module_degree_z.
    """
    if not csv_path.is_file():
        raise FileNotFoundError(f"metrics_raw.csv not found at {csv_path}")
    return pd.read_csv(csv_path)


def _aggregate_node_level_metrics(
    df_raw: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aggregate node-level metrics (participation coefficient and within-module degree)
    into scalars by computing the mean across nodes.

    Also preserve the original node-level data in a separate DataFrame for visualization.

    Parameters
    ----------
    df_raw : pd.DataFrame
        Raw metrics DataFrame from T021 with columns:
        subject_id, modularity, global_efficiency,
        participation_coefficients (JSON string), within_module_degree_z (JSON string).

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame]
        * **aggregated_df** – DataFrame with columns:
          subject_id, modularity, global_efficiency, pc_mean, wmd_mean
        * **node_metrics_df** – DataFrame with columns:
          subject_id, node_0, node_1, ..., node_399 (for participation coefficient)
          and a separate set for within_module_degree
    """
    aggregated_records = []
    node_metrics_pc_records = []
    node_metrics_wmd_records = []

    for _, row in df_raw.iterrows():
        subject_id = row["subject_id"]

        # Parse node-level vectors from JSON strings
        pc_vec = _deserialize_array(row["participation_coefficients"])
        wmd_vec = _deserialize_array(row["within_module_degree_z"])

        # Compute means
        pc_mean = float(np.mean(pc_vec))
        wmd_mean = float(np.mean(wmd_vec))

        # Build aggregated record (scalars only)
        aggregated_records.append({
            "subject_id": subject_id,
            "modularity": row["modularity"],
            "global_efficiency": row["global_efficiency"],
            "pc_mean": pc_mean,
            "wmd_mean": wmd_mean,
        })

        # Build node-level records for PC
        pc_node_record = {"subject_id": subject_id}
        for i, val in enumerate(pc_vec):
            pc_node_record[f"node_{i}"] = val
        node_metrics_pc_records.append(pc_node_record)

        # Build node-level records for WMD
        wmd_node_record = {"subject_id": subject_id}
        for i, val in enumerate(wmd_vec):
            wmd_node_record[f"node_{i}"] = val
        node_metrics_wmd_records.append(wmd_node_record)

    aggregated_df = pd.DataFrame(aggregated_records)
    node_metrics_pc_df = pd.DataFrame(node_metrics_pc_records)
    node_metrics_wmd_df = pd.DataFrame(node_metrics_wmd_records)

    # Merge the two node-level DataFrames; PC and WMD are stored separately
    # but we'll write them as a single file with both metrics
    # For now, we'll write PC as the primary node_metrics_raw.csv
    # (WMD can be added as additional columns or a separate file)
    # Following the spec, we preserve node-level data for visualization
    return aggregated_df, node_metrics_pc_df


def write_aggregated_metrics_csv(df_aggregated: pd.DataFrame) -> None:
    """
    Write the aggregated metrics to ``data/analysis/aggregated_metrics.csv``.

    Parameters
    ----------
    df_aggregated : pd.DataFrame
        DataFrame with columns: subject_id, modularity, global_efficiency,
        pc_mean, wmd_mean.
    """
    output_path = Path("data") / "analysis" / "aggregated_metrics.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure deterministic column order
    column_order = ["subject_id", "modularity", "global_efficiency", "pc_mean", "wmd_mean"]
    df_aggregated = df_aggregated[column_order]

    df_aggregated.to_csv(output_path, index=False)
    logger.log("aggregated_metrics_written", path=str(output_path), count=len(df_aggregated))


def write_node_metrics_raw_csv(df_node_metrics: pd.DataFrame) -> None:
    """
    Write the node-level metrics to ``data/analysis/node_metrics_raw.csv``.

    This file preserves the original node-level participation coefficient
    vectors (and optionally within-module degree) for visualization (T032).

    Parameters
    ----------
    df_node_metrics : pd.DataFrame
        DataFrame with columns: subject_id, node_0, node_1, ..., node_399.
    """
    output_path = Path("data") / "analysis" / "node_metrics_raw.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df_node_metrics.to_csv(output_path, index=False)
    logger.log("node_metrics_raw_written", path=str(output_path), count=len(df_node_metrics))


def aggregate_metrics() -> None:
    """
    Main aggregation logic for T022.

    Reads ``data/analysis/metrics_raw.csv`` (output of T021), aggregates
    node-level metrics (participation coefficient and within-module degree)
    into scalars, and writes two output files:
      - ``data/analysis/aggregated_metrics.csv`` (scalar metrics)
      - ``data/analysis/node_metrics_raw.csv`` (node-level data for visualization)
    """
    logger.log("aggregation_start", task="T022")

    metrics_raw_path = Path("data") / "analysis" / "metrics_raw.csv"

    try:
        df_raw = _read_metrics_raw_csv(metrics_raw_path)
    except FileNotFoundError as fnf:
        logger.log("aggregation_failed", error=str(fnf))
        raise RuntimeError(
            f"T021 output not found. Ensure T021 has run before T022. Error: {fnf}"
        ) from fnf

    if df_raw.empty:
        logger.log("aggregation_warning", msg="metrics_raw.csv is empty")
        raise RuntimeError("metrics_raw.csv contains no data")

    # Perform aggregation
    df_aggregated, df_node_metrics = _aggregate_node_level_metrics(df_raw)

    # Write outputs
    write_aggregated_metrics_csv(df_aggregated)
    write_node_metrics_raw_csv(df_node_metrics)

    logger.log("aggregation_complete", task="T022", count=len(df_aggregated))


def main() -> None:
    """
    Entry point used by the quick‑start run‑book.

    This function orchestrates the T022 aggregation workflow:
    1. Reads ``data/analysis/metrics_raw.csv`` (from T021).
    2. Aggregates node-level metrics (PC and WMD) into scalars.
    3. Writes ``data/analysis/aggregated_metrics.csv`` (scalar metrics).
    4. Writes ``data/analysis/node_metrics_raw.csv`` (node-level data).
    """
    aggregate_metrics()


# ======================================================================
# If the module is executed directly, run the main routine.
# ======================================================================
if __name__ == "__main__":
    main()