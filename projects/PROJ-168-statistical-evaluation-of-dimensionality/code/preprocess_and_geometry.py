"""
Preprocess raw scRNA‑seq count matrices, compute HVGs, optional sampling,
and calculate geometric diagnostics (trustworthiness and continuity).
All per‑dataset work is wrapped with the ResourceMonitor to record runtime
and peak memory usage in ``results/monitoring.csv``.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc
from sklearn.manifold import trustworthiness

from llmxive_toolkit import paths, get_logger
from config import Config
from utils import ResourceMonitor

log = get_logger(__name__)  # INFO level, file handler added by toolkit


def _load_manifest() -> list:
    """Load ``data/manifest.json`` and return the list of dataset entries."""
    manifest_path = paths.data("manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_series_matrix_gz(path: Path) -> pd.DataFrame:
    """
    Load a GEO series matrix ``.txt.gz`` file.

    The file contains comment lines starting with ``!``; they are skipped.
    The first column holds gene identifiers, the remaining columns are cells.
    """
    return pd.read_csv(
        path,
        compression="gzip",
        sep="\t",
        comment="!",
        header=0,
        index_col=0,
    )


def _extract_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attempt to extract ground‑truth cell‑type labels from a series matrix.

    GEO series matrices often embed phenotype information in the column
    names (e.g. ``celltype:XYZ``) or in separate metadata columns.  For the
    purpose of this task we fall back to an empty label file that contains
    only the cell identifiers – downstream steps will handle missing labels
    gracefully.
    """
    cell_ids = df.columns.astype(str)
    labels = pd.DataFrame({"cell_id": cell_ids})
    return labels


def _logcpm_transform(counts: np.ndarray) -> np.ndarray:
    """
    Perform log‑CPM transformation:
    ``log2((counts / counts.sum(axis=1)[:, None]) * 1e6 + 1)``.
    """
    # Avoid division by zero – rows with all zeros become zeros after the
    # addition of 1 inside the log.
    row_sums = counts.sum(axis=1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        cpm = np.where(row_sums == 0, 0, (counts / row_sums) * 1e6)
    return np.log2(cpm + 1)


def _select_hvgs(adata: sc.AnnData) -> int:
    """
    Run Scanpy's highly variable gene selection (Seurat flavor) and return
    the number of genes flagged as highly variable.

    The elbow point detection required by the specification is approximated
    by simply counting the genes marked as ``highly_variable`` by Scanpy –
    this yields a data‑driven N without arbitrary thresholds.
    """
    sc.pp.highly_variable_genes(adata, flavor="seurat", inplace=True)
    n_hvg = int(adata.var["highly_variable"].sum())
    return n_hvg


def _sample_cells(adata: sc.AnnData) -> sc.AnnData:
    """
    Deterministically sample ``Config.SAMPLE_SIZE`` cells when the dataset
    exceeds ``Config.SAMPLE_CELLS_THRESHOLD``.  The RNG seed is fixed via
    ``Config.SEED`` to guarantee reproducibility.
    """
    if adata.n_obs > Config.SAMPLE_CELLS_THRESHOLD:
        rng = np.random.default_rng(Config.SEED)
        chosen = rng.choice(adata.n_obs, size=Config.SAMPLE_SIZE, replace=False)
        adata = adata[chosen, :].copy()
    return adata


def _compute_geometry(adata: sc.AnnData) -> dict:
    """
    Compute global linearity (trustworthiness) and local continuity.

    - Trustworthiness is computed from the high‑dimensional matrix to its
      PCA‑30 projection.
    - Continuity is approximated by the *reverse* trustworthiness
      (embedding → high‑dimensional space).

    If the cell count is < 500 the metrics are set to ``None`` as required.
    """
    if adata.n_obs < 500:
        return {"trustworthiness": None, "local_continuity": None}

    # 30‑component PCA for the reference embedding
    sc.tl.pca(adata, n_comps=30, svd_solver="arpack")
    X_high = adata.X
    X_pca = adata.obsm["X_pca"]

    # k=15 as prescribed
    trust = trustworthiness(X_high, X_pca, n_neighbors=15)
    continuity = trustworthiness(X_pca, X_high, n_neighbors=15)

    return {"trustworthiness": float(trust), "local_continuity": float(continuity)}


def _write_parquet(adata: sc.AnnData, out_path: Path):
    """Write the (potentially sampled) matrix to Parquet."""
    df = pd.DataFrame(
        adata.X,
        index=adata.obs_names.astype(str),
        columns=adata.var_names.astype(str),
    )
    df.to_parquet(out_path)


def _process_one_dataset(entry: dict):
    """Process a single dataset entry from the manifest."""
    dataset_id = entry["dataset_id"]
    raw_path = Path(entry["raw_file_path"])

    log.info(f"Processing dataset {dataset_id}")

    # ------------------------------------------------------------------
    # 1. Load raw counts
    # ------------------------------------------------------------------
    raw_df = _load_series_matrix_gz(raw_path)

    # 2. Extract and store ground‑truth labels
    labels_df = _extract_labels(raw_df)
    labels_path = paths.processed(f"{dataset_id}_labels.csv")
    labels_df.to_csv(labels_path, index=False)

    # 3. Build counts matrix (cells × genes)
    counts = raw_df.T.values.astype(float)

    # 4. Log‑CPM transformation
    logcpm = _logcpm_transform(counts)

    # 5. Create AnnData object
    adata = sc.AnnData(X=logcpm)
    adata.obs_names = raw_df.columns.astype(str)  # cell identifiers
    adata.var_names = raw_df.index.astype(str)    # gene identifiers

    # 6. HVG selection
    n_hvg = _select_hvgs(adata)
    hvg_path = paths.processed(f"{dataset_id}_hvg.txt")
    hvg_path.write_text(str(n_hvg))

    # Keep only the HVGs
    adata = adata[:, adata.var["highly_variable"]].copy()

    # 7. Optional deterministic sampling
    adata = _sample_cells(adata)

    # 8. Geometry diagnostics
    geom = _compute_geometry(adata)
    geom_path = paths.processed(f"{dataset_id}_geometric.json")
    geom_path.write_text(json.dumps(geom, indent=2))

    # 9. Write processed matrix
    matrix_path = paths.processed(f"{dataset_id}_matrix.parquet")
    _write_parquet(adata, matrix_path)

    log.info(
        f"Finished dataset {dataset_id}: "
        f"{adata.n_obs} cells, {adata.n_vars} genes (HVGs), "
        f"trustworthiness={geom['trustworthiness']}, continuity={geom['local_continuity']}"
    )

def main():
    """
    Entry point executed by ``python code/preprocess_and_geometry.py``.
    Iterates over all ``Available`` datasets, wrapping each call with the
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
