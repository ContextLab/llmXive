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
    in ``preprocess.structural``.  The function returns a dictionary that also
    includes the ``subject_id`` field.  If the underlying calculation fails
    (e.g. the graph is too sparse), a ``ValueError`` is raised.

compute_subject_metrics(subject_id: str, data_dir: str,
                        density_threshold: float = 0.15) -> dict
    Convenience helper that loads the adjacency matrix for ``subject_id``,
    runs the metric calculation and returns a flat dictionary that also
    includes the ``subject_id`` field.

run_density_sensitivity(data_dir: str,
                        output_path: Optional[str] = None) -> pandas.DataFrame
    Iterate over all subjects found in ``data_dir`` (files matching
    ``*_matrix.npy``) and compute graph metrics for each density
    threshold defined in the configuration (baseline ± 0.05).  The
    results are written to ``data/derived/structural_density_sensitivity.csv``
    (or to ``output_path`` if provided) and the resulting DataFrame is
    returned.

Example
-------
>>> from structural import compute_subject_metrics, run_density_sensitivity
>>> metrics = compute_subject_metrics('sub-001', 'data/processed')
>>> metrics['global_efficiency']
0.42
>>> df = run_density_sensitivity('data/processed')
>>> df.head()
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger
from preprocess.structural import calculate_graph_metrics as _core_calc
from config import get_config_dict

log = get_logger(__name__)


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
        raise FileNotFoundError(
            f"Adjacency matrix not found for subject '{subject_id}' at '{matrix_path}'."
        )
    return np.load(matrix_path)


def calculate_graph_metrics(
    adjacency_matrix: np.ndarray, density_threshold: float = 0.15
) -> Dict[str, float]:
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
        raise ValueError(
            "Graph metric calculation failed (e.g., graph too sparse or disconnected)."
        )
    # Standardise key names expected by downstream code.
    return {
        "global_efficiency": result.get("global_efficiency", np.nan),
        "clustering": result.get("clustering", np.nan),
        "modularity": result.get("modularity", np.nan),
    }


def compute_subject_metrics(
    subject_id: str,
    data_dir: str,
    density_threshold: float = 0.15,
) -> Dict[str, float]:
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
    metrics["density_threshold"] = density_threshold
    return metrics


def _gather_subject_ids(data_dir: str) -> List[str]:
    """
    Return a list of subject identifiers for which ``*_matrix.npy`` files exist.
    """
    p = Path(data_dir)
    ids = []
    for fp in p.glob("*_matrix.npy"):
        ids.append(fp.stem.replace("_matrix", ""))
    return ids


def run_density_sensitivity(
    data_dir: str,
    output_path: Optional[str] = None,
) -> pd.DataFrame:
    """
    Perform the mandatory graph‑density sensitivity analysis.

    For every subject found in ``data_dir`` and for each density
    threshold defined in the configuration (baseline ± 0.05), compute
    the three graph metrics and save the aggregated results.

    Parameters
    ----------
    data_dir : str
        Directory containing subject adjacency matrices (``*_matrix.npy``).
    output_path : str, optional
        Destination CSV file.  If omitted, the file is written to
        ``data/derived/structural_density_sensitivity.csv`` using the
        llmxive path helper.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns:
        ``subject_id, density_threshold, global_efficiency, clustering, modularity``.
    """
    config = get_config_dict()

    # Resolve density thresholds
    baseline = config.get("BASELINE_DENSITY")
    variations = config.get("DENSITY_THRESHOLD_VARIATIONS")

    if variations is None:
        if baseline is None:
            raise RuntimeError(
                "Configuration must define either 'BASELINE_DENSITY' or "
                "'DENSITY_THRESHOLD_VARIATIONS' for the sensitivity analysis."
            )
        # Default to ±0.05 (i.e., 5% absolute offset)
        variations = [
            round(baseline - 0.05, 5),
            round(baseline, 5),
            round(baseline + 0.05, 5),
        ]

    # Ensure variations are positive and <= 1.0
    variations = [float(v) for v in variations if 0.0 < v <= 1.0]
    if not variations:
        raise ValueError("No valid density thresholds derived from configuration.")

    subject_ids = _gather_subject_ids(data_dir)
    if not subject_ids:
        log.warning(f"No adjacency matrix files found in '{data_dir}'.")
        return pd.DataFrame()  # Empty result

    rows = []
    for subj in subject_ids:
        for thr in variations:
            try:
                row = compute_subject_metrics(subj, data_dir, density_threshold=thr)
                rows.append(row)
            except Exception as exc:
                log.error(
                    f"Failed to compute metrics for subject '{subj}' at density {thr}: {exc}"
                )
                # Record exclusion in the global exclusion log
                exclusion_entry = {
                    "subject_id": subj,
                    "density_threshold": thr,
                    "reason": str(exc),
                }
                # Append to the exclusion log file (creates if missing)
                exclusion_log_path = paths.data("logs", "exclusion_log.json")
                try:
                    if exclusion_log_path.is_file():
                        with open(exclusion_log_path, "r") as f:
                            excl = json.load(f)
                    else:
                        excl = []
                    excl.append(exclusion_entry)
                    with open(exclusion_log_path, "w") as f:
                        json.dump(excl, f, indent=2)
                except Exception as log_exc:
                    log.error(f"Could not write to exclusion log: {log_exc}")

    df = pd.DataFrame(rows)
    # Define output location
    if output_path is None:
        out_path = paths.data("derived", "structural_density_sensitivity.csv")
    else:
        out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    log.info(f"Structural density sensitivity results saved to {out_path}")
    return df


if __name__ == "__main__":
    """
    Minimal command‑line interface.

    Usage
    -----
    python code/structural.py <subject_id> <data_dir> [density]
    python code/structural.py sensitivity <data_dir> [output_csv]

    The first form computes metrics for a single subject.
    The second form runs the full density‑sensitivity analysis.
    """
    import json
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python structural.py <subject_id> <data_dir> [density]\n"
            "   or: python structural.py sensitivity <data_dir> [output_csv]"
        )
        sys.exit(1)

    if sys.argv[1] == "sensitivity":
        if len(sys.argv) < 3:
            print("Please provide the directory containing adjacency matrices.")
            sys.exit(1)
        data_directory = sys.argv[2]
        out_csv = sys.argv[3] if len(sys.argv) > 3 else None
        try:
            run_density_sensitivity(data_directory, out_csv)
        except Exception as e:
            print(f"Error during sensitivity analysis: {e}")
            sys.exit(1)
    else:
        # Single‑subject mode (legacy)
        subj = sys.argv[1]
        dir_path = sys.argv[2]
        dens = float(sys.argv[3]) if len(sys.argv) > 3 else 0.15
        try:
            res = compute_subject_metrics(subj, dir_path, dens)
            print(json.dumps(res, indent=2))
        except Exception as exc:
            print(f"Error: {exc}")
            sys.exit(1)