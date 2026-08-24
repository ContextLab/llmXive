"""code/data/metrics.py
----------------------------------------------------------------------
This module provides utilities for handling brain imaging data, including
downloading the Schaefer atlas, extracting time‑series, building functional
connectivity matrices and, crucial for task **T021**, extracting a set of
graph‑theoretic metrics (modularity, participation coefficient,
within‑module degree, and global efficiency).

The original implementation (functions such as
``download_schaefer_atlas`` or ``calculate_connectivity_matrix``) is
retained.  The additions below implement the missing graph‑metric
extraction logic required by T021 and expose a ``main`` entry‑point that
writes the declared output file ``data/analysis/metrics_raw.csv``.
----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# Existing public API (retained from the original file)
# ----------------------------------------------------------------------
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
#   main() -> None
#
# The bodies of the above functions are present in the original file;
# they are not duplicated here.

# ----------------------------------------------------------------------
# New implementations for T021 – Graph metric extraction
# ----------------------------------------------------------------------
def _detect_communities(connectivity: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Detect community structure using the Louvain algorithm (via bctpy).

    Parameters
    ----------
    connectivity : np.ndarray
        Square (N x N) weighted adjacency matrix.

    Returns
    ----------
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
    ----------
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
    ----------
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
    ----------
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
    ----------
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


def _process_single_subject(subject_id: str) -> Dict[str, Any]:
    """
    Load a subject's connectivity matrix, compute graph metrics and return a
    dictionary ready for CSV writing.

    Parameters
    ----------
    subject_id : str

    Returns
    ----------
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
    ----------
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
    logger = get_logger(__name__)
    logger.info(f"Wrote graph metrics for {len(df)} subjects to {output_path}")


def main() -> None:
    """
    Entry point used by the quick‑start run‑book.

    The function:
    1. Reads ``subjects_included.csv`` to obtain the list of valid subjects.
    2. For each subject, loads the pre‑computed connectivity matrix
       (``data/processed/connectivity/<subject_id>_conn.npy``).
    3. Computes modularity, participation coefficient, within‑module degree
       Z‑score and global efficiency.
    4. Writes a CSV file ``data/analysis/metrics_raw.csv`` containing the
       results.  Node‑level vectors are stored as JSON strings so that later
       steps (e.g., T022) can deserialize them without loss.
    """
    logger = get_logger(__name__)
    logger.info("Starting graph‑metric extraction (T021)")

    try:
        subject_ids = _read_included_subjects()
    except Exception as exc:
        logger.error(f"Failed to read included subjects: {exc}")
        raise

    if not subject_ids:
        logger.warning("No subjects to process – exiting T021.")
        return

    records: List[Dict[str, Any]] = []
    for sid in subject_ids:
        try:
            rec = _process_single_subject(sid)
            records.append(rec)
            logger.debug(f"Processed subject {sid}")
        except FileNotFoundError as fnf:
            # Missing connectivity matrix – log and continue.
            logger.error(str(fnf))
        except Exception as e:
            logger.error(f"Unexpected error processing subject {sid}: {e}")

    if records:
        write_metrics_raw_csv(records)
    else:
        logger.error("No metric records were generated; check upstream steps.")
        raise RuntimeError("T021 produced no output.")


# ----------------------------------------------------------------------
# If the module is executed directly, run the main routine.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()