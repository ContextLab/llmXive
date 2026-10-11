"""
Structural utilities module.

This module provides a thin wrapper around the core graph‑metric
implementation that lives in ``code/preprocess/structural.py``.
It is intentionally lightweight: the heavy lifting (density
thresholding, metric calculation, handling of disconnected graphs)
is performed by :func:`preprocess.structural.calculate_graph_metrics`.

The public API mirrors the expectations of the unit tests for
``tests/unit/test_structural.py`` and other parts of the pipeline
that import ``code.structural`` directly.

Functions
----------
load_adjacency_matrix(subject_id: str, data_dir: str) -> np.ndarray
    Load a subject‑specific structural connectivity matrix saved as a
    NumPy ``.npy`` file.  The file is expected to be located at
    ``{data_dir}/{subject_id}_matrix.npy``.  An informative ``FileNotFoundError``
    is raised if the file does not exist.

calculate_graph_metrics(adjacency_matrix: np.ndarray,
                        density_threshold: float = 0.15) -> dict
    Compute the three required graph metrics (global efficiency,
    average clustering coefficient, modularity) using the implementation
    in ``preprocess.structural``.  The function returns a dictionary
    with keys ``'global_efficiency'``, ``'clustering'`` and ``'modularity'``.
    If the underlying calculation fails (e.g. the graph is too sparse),
    a ``ValueError`` is raised.

compute_subject_metrics(subject_id: str, data_dir: str,
                        density_threshold: float = 0.15) -> dict
    Convenience helper that loads the adjacency matrix for ``subject_id``,
    runs the metric calculation and returns a dictionary that also
    includes the ``subject_id`` field.  This is the function used by the
    higher‑level pipeline (e.g. ``code/main.py``) when aggregating results.

Example
-------
>>> from structural import compute_subject_metrics
>>> metrics = compute_subject_metrics('sub-001', 'data/processed')
>>> metrics['global_efficiency']
0.42
"""

import os
from pathlib import Path
from typing import Dict

import numpy as np

# Import the core implementation from the preprocessing package.
# This keeps the heavy logic in a single place and avoids code duplication.
from preprocess.structural import calculate_graph_metrics as _core_calc


def load_adjacency_matrix(subject_id: str, data_dir: str) -> np.ndarray:
    """
    Load a subject's structural connectivity matrix.

    Parameters
    ----------
    subject_id : str
        Identifier of the subject (e.g., ``'sub-001'``).
    data_dir : str
        Directory that contains the ``{subject_id}_matrix.npy`` files.

    Returns
    -------
    np.ndarray
        The adjacency matrix (shape ``N x N``).

    Raises
    ------
    FileNotFoundError
        If the expected ``.npy`` file does not exist.
    """
    matrix_path = Path(data_dir) / f"{subject_id}_matrix.npy"
    if not matrix_path.is_file():
        raise FileNotFoundError(f"Adjacency matrix not found for subject "
                                f"'{subject_id}' at '{matrix_path}'.")
    return np.load(matrix_path)


def calculate_graph_metrics(adjacency_matrix: np.ndarray,
                           density_threshold: float = 0.15) -> Dict[str, float]:
    """
    Wrapper around the core metric calculation.

    Parameters
    ----------
    adjacency_matrix : np.ndarray
        Weighted adjacency matrix of the structural connectome.
    density_threshold : float, optional
        Proportional density to retain (default 0.15).

    Returns
    -------
    dict
        Dictionary with keys ``'global_efficiency'``, ``'clustering'``,
        and ``'modularity'``.

    Raises
    ------
    ValueError
        If the underlying metric calculation returns ``None``.
    """
    result = _core_calc(adjacency_matrix, density_threshold)
    if result is None:
        raise ValueError("Graph metric calculation failed (e.g., graph "
                         "too sparse or disconnected).")
    # Standardise key names expected by downstream code.
    return {
        "global_efficiency": result.get("global_efficiency", np.nan),
        "clustering": result.get("clustering", np.nan),
        "modularity": result.get("modularity", np.nan),
    }


def compute_subject_metrics(subject_id: str,
                           data_dir: str,
                           density_threshold: float = 0.15) -> Dict[str, float]:
    """
    Compute structural metrics for a single subject.

    This helper loads the adjacency matrix, runs the metric calculation
    and returns a flat dictionary that includes the ``subject_id`` field.

    Parameters
    ----------
    subject_id : str
        Subject identifier.
    data_dir : str
        Directory containing ``{subject_id}_matrix.npy``.
    density_threshold : float, optional
        Density threshold for the graph (default 0.15).

    Returns
    -------
    dict
        ``{'subject_id': ..., 'global_efficiency': ..., 'clustering': ...,
        'modularity': ...}``
    """
    adj = load_adjacency_matrix(subject_id, data_dir)
    metrics = calculate_graph_metrics(adj, density_threshold)
    metrics["subject_id"] = subject_id
    return metrics


if __name__ == "__main__":
    """
    Minimal command‑line interface.

    Usage
    -----
    python code/structural.py <subject_id> <data_dir> [density]

    The script prints the computed metrics as a JSON‑like string.
    It is primarily intended for quick manual checks and is not
    part of the automated pipeline.
    """
    import json
    import sys

    if len(sys.argv) < 3:
        print("Usage: python structural.py <subject_id> <data_dir> [density]")
        sys.exit(1)

    subj = sys.argv[1]
    dir_path = sys.argv[2]
    dens = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15

    try:
        res = compute_subject_metrics(subj, dir_path, dens)
        print(json.dumps(res, indent=2))
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)