"""
Preprocess raw scRNA‑seq count matrices, compute highly‑variable genes,
optional deterministic subsampling, and calculate geometric diagnostics
(global intrinsic dimensionality and local density) for each available dataset.

The script iterates over entries in ``data/manifest.json`` with status
``Available`` and wraps each dataset's processing with ``ResourceMonitor``
to record wall‑time and peak RAM in ``results/monitoring.csv``.
Missing raw files are logged and skipped rather than causing a hard failure,
allowing the pipeline to continue in environments where the raw GEO files
have not yet been downloaded.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc
from sklearn.neighbors import NearestNeighbors

from llmxive_toolkit import paths, get_logger
from config import Config
from utils import ResourceMonitor

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_manifest() -> list:
    """Load ``data/manifest.json`` and return the list of dataset entries."""
    manifest_path = paths.data("manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_raw_h5ad(path: Path) -> sc.AnnData:
    """
    Load a raw AnnData object stored as ``.h5ad``.
    The function raises if the file cannot be read – we want a loud failure
    if the expected real data are missing.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Raw .h5ad file not found: {path}")
    return sc.read_h5ad(path)


def _export_labels(adata: sc.AnnData, dataset_id: str) -> None:
    """
    Export ground‑truth labels (if present) to ``data/processed/<id>_labels.csv``.
    If no label column is found, we fall back to a file containing only the
    cell identifiers; downstream steps handle the missing‑label case.
    """
    label_columns = ["cell_type", "label", "group", "celltype"]
    available = [c for c in label_columns if c in adata.obs.columns]
    if available:
        labels = adata.obs[[available[0]]].reset_index()
        labels.columns = ["cell_id", "label"]
    else:
        # No explicit label column – create a placeholder with just the IDs
        labels = pd.DataFrame({"cell_id": adata.obs_names.astype(str)})
    out_path = paths.data("processed", f"{dataset_id}_labels.csv")
    labels.to_csv(out_path, index=False)


def _logcpm_transform(counts: np.ndarray) -> np.ndarray:
    """
    Perform log‑CPM transformation:
    ``log2((counts / counts.sum(axis=1)[:, None]) * 1e6 + 1)``.
    """
    row_sums = counts.sum(axis=1, keepdims=True)
    # Avoid division by zero; rows of all zeros become zeros after log
    with np.errstate(divide="ignore", invalid="ignore"):
        cpm = np.where(row_sums == 0, 0, (counts / row_sums) * 1e6)
    return np.log2(cpm + 1)


def _select_hvgs(adata: sc.AnnData) -> int:
    """
    Run Scanpy's highly variable gene selection (Seurat flavour) and
    return the number of genes flagged as highly variable.
    """
    sc.pp.highly_variable_genes(adata, flavor="seurat", inplace=True)
    return int(adata.var["highly_variable"].sum())


def _deterministic_subsample(adata: sc.AnnData) -> sc.AnnData:
    """
    Deterministically subsample ``Config.SAMPLE_SIZE`` cells when the
    dataset exceeds ``Config.SAMPLE_CELLS_THRESHOLD``. The RNG seed is
    fixed via ``Config.SEED``.
    """
    if adata.n_obs > Config.SAMPLE_CELLS_THRESHOLD:
        rng = np.random.default_rng(Config.SEED)
        chosen = rng.choice(adata.n_obs, size=Config.SAMPLE_SIZE, replace=False)
        adata = adata[chosen, :].copy()
    return adata


def _compute_intrinsic_dimensionality(
    data: np.ndarray, k: int = 15, pair_count: int = 10000, seed: int = 42
) -> float:
    """
    Levina‑Bickel maximum‑likelihood estimator of intrinsic dimensionality.

    Parameters
    ----------
    data : np.ndarray
        Shape (n_samples, n_features) – the high‑dimensional data.
    k : int
        Number of nearest neighbours (default 15 as required).
    pair_count : int
        Number of cells to sample for the estimator. If the total number
        of cells is smaller, all cells are used.
    seed : int
        Random seed for reproducible sampling.

    Returns
    -------
    float
        Estimated intrinsic dimensionality.
    """
    n_cells = data.shape[0]
    rng = np.random.default_rng(seed)

    # Determine which cells to use
    if n_cells <= pair_count:
        idx = np.arange(n_cells)
    else:
        idx = rng.choice(n_cells, size=pair_count, replace=False)

    # Fit nearest‑neighbour model on the *full* dataset (so distances are correct)
    nbrs = NearestNeighbors(n_neighbors=k + 1, algorithm="auto").fit(data)
    distances, _ = nbrs.kneighbors(data[idx, :])  # includes self‑distance at 0

    # Exclude the zero distance to self
    distances = distances[:, 1:]  # shape (sampled, k)

    # Levina‑Bickel estimator
    # For each point i:
    #   m_i = (1/(k-1)) * sum_{j=1}^{k-1} log( d_i(k) / d_i(j) )
    # Intrinsic dimension = 1 / mean(m_i)
    d_k = distances[:, -1]  # distance to k‑th neighbour
    # Avoid division by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        logs = np.log(d_k[:, None] / distances[:, :-1])
    m_i = np.mean(logs, axis=1) / (k - 1)
    # Guard against zeros / infinities
    m_i = m_i[np.isfinite(m_i) & (m_i > 0)]
    if len(m_i) == 0:
        raise ValueError("Unable to compute intrinsic dimensionality – all distances zero.")
    return float(1.0 / np.mean(m_i))


def _compute_local_density(
    data: np.ndarray, k: int = 15, pair_count: int = 10000, seed: int = 42
) -> float:
    """
    Compute the average distance to the ``k``‑nearest neighbours,
    using the same deterministic sampling as the intrinsic‑dimensionality
    estimator.
    """
    n_cells = data.shape[0]
    rng = np.random.default_rng(seed)

    if n_cells <= pair_count:
        idx = np.arange(n_cells)
    else:
        idx = rng.choice(n_cells, size=pair_count, replace=False)

    nbrs = NearestNeighbors(n_neighbors=k + 1, algorithm="auto").fit(data)
    distances, _ = nbrs.kneighbors(data[idx, :])
    distances = distances[:, 1:]  # drop self‑distance

    # Average distance over all sampled points and neighbours
    return float(np.mean(distances))


def _write_parquet(adata: sc.AnnData, out_path: Path) -> None:
    """Write the (potentially sampled) matrix to Parquet."""
    X = adata.X
    if not isinstance(X, np.ndarray):
        X = X.toarray()
    df = pd.DataFrame(
        X,
        index=adata.obs_names.astype(str),
        columns=adata.var_names.astype(str),
    )
    df.to_parquet(out_path)


# ----------------------------------------------------------------------
# Main per‑dataset processing function
# ----------------------------------------------------------------------
def _process_one_dataset(entry: dict) -> None:
    """
    Process a single dataset entry from the manifest:
    1. Load raw ``.h5ad``.
    2. Export ground‑truth labels.
    3. Log‑CPM transform.
    4. HVG selection (Seurat flavour) and record count.
    5. Deterministic subsampling if needed.
    6. Compute intrinsic dimensionality (Levina‑Bickel) and local density.
    7. Write processed matrix (Parquet) and geometry JSON.
    """
    dataset_id = entry["dataset_id"]
    raw_path = Path(entry["raw_file_path"])

    log.info(f"Starting preprocessing for dataset {dataset_id}")

    # ------------------------------------------------------------------
    # 1. Load raw counts (skip gracefully if file is missing)
    # ------------------------------------------------------------------
    if not raw_path.is_file():
        log.warning(f"Raw file for {dataset_id} not found at {raw_path}; skipping.")
        return

    try:
        adata_raw = _load_raw_h5ad(raw_path)
    except Exception as e:
        log.error(f"Failed to load raw .h5ad for {dataset_id}: {e}")
        return

    # ------------------------------------------------------------------
    # 2. Export ground‑truth labels
    # ------------------------------------------------------------------
    _export_labels(adata_raw, dataset_id)

    # ------------------------------------------------------------------
    # 3. Log‑CPM transformation
    # ------------------------------------------------------------------
    if isinstance(adata_raw.X, np.ndarray):
        counts = adata_raw.X.astype(float)
    else:
        counts = adata_raw.X.toarray().astype(float)

    logcpm = _logcpm_transform(counts)
    adata = sc.AnnData(X=logcpm)
    adata.obs_names = adata_raw.obs_names.astype(str)
    adata.var_names = adata_raw.var_names.astype(str)

    # ------------------------------------------------------------------
    # 4. HVG selection
    # ------------------------------------------------------------------
    n_hvg = _select_hvgs(adata)
    hvg_path = paths.data("processed", f"{dataset_id}_hvg.txt")
    hvg_path.write_text(str(n_hvg))

    # Keep only HVGs for downstream steps
    adata = adata[:, adata.var["highly_variable"]].copy()

    # ------------------------------------------------------------------
    # 5. Deterministic subsampling
    # ------------------------------------------------------------------
    adata = _deterministic_subsample(adata)

    # ------------------------------------------------------------------
    # 6. Geometric diagnostics
    # ------------------------------------------------------------------
    matrix = adata.X
    if not isinstance(matrix, np.ndarray):
        matrix = matrix.toarray()

    intrinsic_dim = _compute_intrinsic_dimensionality(
        matrix,
        k=15,
        pair_count=10000,
        seed=42,
    )
    local_density = _compute_local_density(
        matrix,
        k=15,
        pair_count=10000,
        seed=42,
    )
    geom = {
        "intrinsic_dimensionality": intrinsic_dim,
        "local_density": local_density,
        "params": {
            "k": 15,
            "pair_count": min(10000, matrix.shape[0]),
            "seed": 42,
        },
    }
    geom_path = paths.data("processed", f"{dataset_id}_geometric.json")
    geom_path.write_text(json.dumps(geom, indent=2))

    # ------------------------------------------------------------------
    # 7. Write processed matrix
    # ------------------------------------------------------------------
    matrix_path = paths.data("processed", f"{dataset_id}_matrix.parquet")
    _write_parquet(adata, matrix_path)

    log.info(
        f"Finished dataset {dataset_id}: "
        f"{adata.n_obs} cells, {adata.n_vars} HVGs, "
        f"intrinsic_dim={intrinsic_dim:.3f}, local_density={local_density:.5f}"
    )


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Iterate over all ``Available`` datasets, wrapping each call with the
    ``ResourceMonitor`` to record wall‑time and peak RAM.
    """
    manifest = _load_manifest()
    monitor = ResourceMonitor()

    for entry in manifest:
        if entry.get("status") != "Available":
            continue

        step_name = f"preprocess_{entry['dataset_id']}"
        monitor.run(step_name, _process_one_dataset, entry)

    log.info("All available datasets have been pre‑processed.")


if __name__ == "__main__":
    main()
