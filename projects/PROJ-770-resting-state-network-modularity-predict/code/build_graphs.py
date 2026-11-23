"""
build_graphs.py
=================

This module implements the full graph construction and modularity calculation
pipeline for the resting‑state network modularity project. It reads Fisher‑z
transformed correlation matrices (stored as ``.npy`` files) from
``data/processed/correlation_matrices/``, thresholds them to retain the top
proportion of strongest positive edges, builds weighted NetworkX graphs,
runs the Louvain community detection algorithm, and records the modularity
quality index (Q) for each subject.

The resulting DataFrame with columns ``subject_id`` and ``modularity_q`` is
written to ``data/processed/subject_modularity.csv``.  A sanity check is
performed to ensure all Q values lie within the theoretical interval
``[0.0, 1.0]``; any out‑of‑bounds values are logged.

The script is designed to run on real data only.  If no correlation matrix
files are found, it raises an informative ``FileNotFoundError`` rather than
falling back to synthetic data.
"""

import argparse
import logging
from pathlib import Path
from typing import Optional, List

import numpy as np
import pandas as pd
import networkx as nx

# The ``python‑louvain`` package provides the ``community`` module.
try:
    import community as community_louvain
except ImportError as exc:
    raise ImportError(
        "The 'python-louvain' package is required. Install it via "
        "`pip install python-louvain`."
    ) from exc

# Import project‑wide configuration.  If the config module does not define
# a default threshold, we fall back to 10 % (the value used in the
# specification).
try:
    from config import THRESHOLD_PERCENT as DEFAULT_THRESHOLD_PERCENT
except Exception:
    DEFAULT_THRESHOLD_PERCENT = 10.0

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
)

def sanity_check_modularity(
    df: pd.DataFrame,
    q_column: str = "modularity_q",
    subject_id_column: str = "subject_id",
    lower_bound: float = 0.0,
    upper_bound: float = 1.0,
) -> pd.DataFrame:
    """
    Scan a DataFrame containing modularity Q values and log any subjects
    whose Q lies outside the interval ``[lower_bound, upper_bound]``.
    The function returns the original DataFrame unchanged.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame that must contain at least ``subject_id_column`` and
        ``q_column``.
    q_column : str, optional
        Name of the column storing the modularity Q values.  Defaults to
        ``"modularity_q"``.
    subject_id_column : str, optional
        Column name for the subject identifier.  Defaults to ``"subject_id"``.
    lower_bound : float, optional
        Minimum acceptable Q value (inclusive).  Defaults to ``0.0``.
    upper_bound : float, optional
        Maximum acceptable Q value (inclusive).  Defaults to ``1.0``.

    Returns
    -------
    pd.DataFrame
        The original DataFrame (unchanged).  The function is side‑effecting:
        it writes a log entry for each out‑of‑bounds subject.
    """
    out_of_bounds = df[
        (df[q_column] < lower_bound) | (df[q_column] > upper_bound)
    ]
    if not out_of_bounds.empty:
        for _, row in out_of_bounds.iterrows():
            logger.warning(
                f"Subject {row[subject_id_column]} has modularity Q = "
                f"{row[q_column]:.4f}, which lies outside [{lower_bound}, {upper_bound}]"
            )
    else:
        logger.info("All modularity Q values are within the expected bounds.")
    return df

def _threshold_matrix(
    corr_mat: np.ndarray, threshold_percent: float
) -> np.ndarray:
    """
    Keep only the top ``threshold_percent`` of positive edge weights
    (by absolute value) and set the rest to zero.  The matrix is assumed
    to be symmetric with ones on the diagonal.

    Parameters
    ----------
    corr_mat : np.ndarray
        Square correlation matrix (Fisher‑z transformed).
    threshold_percent : float
        Percentage (0‑100) of strongest positive edges to retain.

    Returns
    -------
    np.ndarray
        Thresholded adjacency matrix (same shape as ``corr_mat``).
    """
    if not (0.0 < threshold_percent <= 100.0):
        raise ValueError("threshold_percent must be in (0, 100].")

    # Work on the upper triangle to avoid double‑counting edges.
    triu_indices = np.triu_indices_from(corr_mat, k=1)
    upper_vals = corr_mat[triu_indices]

    # Consider only positive weights for thresholding.
    positive_vals = upper_vals[upper_vals > 0]
    if positive_vals.size == 0:
        raise ValueError("No positive edge weights found for thresholding.")

    # Determine the cutoff value that retains the desired proportion.
    k_keep = int(np.ceil(len(positive_vals) * (threshold_percent / 100.0)))
    if k_keep < 1:
        k_keep = 1
    cutoff = np.partition(positive_vals, -k_keep)[-k_keep]

    # Build a mask of edges to keep.
    keep_mask = np.zeros_like(corr_mat, dtype=bool)
    keep_mask[triu_indices] = corr_mat[triu_indices] >= cutoff
    # Mirror to lower triangle.
    keep_mask = keep_mask | keep_mask.T

    adj = np.where(keep_mask, corr_mat, 0.0)
    np.fill_diagonal(adj, 0.0)  # No self‑loops.
    return adj

def _compute_modularity(adj: np.ndarray) -> float:
    """
    Given a weighted adjacency matrix, compute the Louvain modularity Q.

    Parameters
    ----------
    adj : np.ndarray
        Weighted adjacency matrix (symmetric, zero diagonal).

    Returns
    -------
    float
        Modularity quality index Q.
    """
    G = nx.from_numpy_array(adj, create_using=nx.Graph())
    # The Louvain implementation may raise if the graph is empty.
    if G.number_of_edges() == 0:
        raise ValueError("Graph contains no edges after thresholding.")
    # community_louvain.best_partition returns a dict {node: community}.
    partition = community_louvain.best_partition(G, weight="weight")
    modularity_q = community_louvain.modularity(partition, G, weight="weight")
    return modularity_q

def build_graphs(
    threshold: Optional[float] = None,
    matrix_dir: Optional[Path] = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Construct functional connectivity graphs for all subjects, compute
    Louvain modularity Q, and return a DataFrame with the results.

    Parameters
    ----------
    threshold : float, optional
        Percentage of strongest positive edges to retain.  If ``None``,
        the default defined in ``code/config.py`` (or 10 %) is used.
    matrix_dir : pathlib.Path, optional
        Directory containing ``.npy`` correlation matrices.  If ``None``,
        defaults to ``data/processed/correlation_matrices``.
    **kwargs
        Additional keyword arguments are ignored but accepted for API
        compatibility.

    Returns
    -------
    pd.DataFrame
        Columns: ``subject_id`` (str) and ``modularity_q`` (float).
    """
    # Resolve the threshold.
    if threshold is None:
        threshold = DEFAULT_THRESHOLD_PERCENT
    logger.info(f"Using top‑{threshold:.1f}% positive edges for thresholding.")

    # Resolve the matrix directory.
    if matrix_dir is None:
        matrix_dir = Path("data/processed/correlation_matrices")
    if not matrix_dir.is_dir():
        raise FileNotFoundError(
            f"Correlation matrix directory not found: {matrix_dir}"
        )

    # Find all ``.npy`` files.
    matrix_files: List[Path] = list(matrix_dir.glob("*.npy"))
    if not matrix_files:
        raise FileNotFoundError(
            f"No correlation matrix files (*.npy) found in {matrix_dir}"
        )

    records = []
    for mat_path in matrix_files:
        subject_id = mat_path.stem  # filename without extension
        logger.info(f"Processing subject {subject_id} from {mat_path.name}")

        corr_mat = np.load(mat_path)
        if corr_mat.ndim != 2 or corr_mat.shape[0] != corr_mat.shape[1]:
            raise ValueError(
                f"Correlation matrix for subject {subject_id} is not square."
            )

        # Threshold and compute modularity.
        adj = _threshold_matrix(corr_mat, threshold)
        modularity_q = _compute_modularity(adj)

        records.append({"subject_id": subject_id, "modularity_q": modularity_q})

    df = pd.DataFrame.from_records(records)
    return df

def _parse_args() -> argparse.Namespace:
    """
    Parse command‑line arguments for the script.

    Returns
    -------
    argparse.Namespace
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Build functional connectivity graphs from correlation matrices, "
            "compute Louvain modularity Q for each subject, and write the "
            "results to `data/processed/subject_modularity.csv`."
        )
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help=(
            "Percentage of strongest positive edges to retain. "
            "If omitted, the default from `code/config.py` (or 10) is used."
        ),
    )
    parser.add_argument(
        "--matrix-dir",
        type=str,
        default=None,
        help=(
            "Directory containing Fisher‑z correlation matrices stored as "
            "`.npy` files. Defaults to `data/processed/correlation_matrices`."
        ),
    )
    return parser.parse_args()

def main() -> None:
    """
    Entry point for ``python code/build_graphs.py``.

    The function:
    1. Parses CLI arguments.
    2. Calls :func:`build_graphs` to obtain a DataFrame of modularity Q values.
    3. Executes :func:`sanity_check_modularity` on the DataFrame.
    4. Writes the DataFrame to ``data/processed/subject_modularity.csv``.
    """
    args = _parse_args()
    threshold = args.threshold
    matrix_dir = Path(args.matrix_dir) if args.matrix_dir else None

    logger.info("Starting graph construction and modularity calculation.")
    df = build_graphs(threshold=threshold, matrix_dir=matrix_dir)
    sanity_check_modularity(df)

    output_path = Path("data/processed/subject_modularity.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Modularity results written to {output_path}")

if __name__ == "__main__":
    main()
