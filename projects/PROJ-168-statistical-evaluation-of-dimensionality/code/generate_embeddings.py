"""
generate_embeddings.py

Script to generate PCA, t‑SNE, and UMAP embeddings for each
processed dataset. The script:

1. Reads ``data/manifest.json`` and selects datasets with status
   ``Available``.
2. Loads the pre‑processed matrix stored as
   ``data/processed/<dataset_id>_matrix.parquet``.
3. Generates:
   * PCA (30 components)
   * t‑SNE (2‑D, perplexity=30, n_iter=1000)
   * UMAP (2‑D, n_neighbors=15, min_dist=0.1)
4. Writes the embeddings as CSV files to
   ``data/embeddings/<dataset_id>_PCA.csv``,
   ``data/embeddings/<dataset_id>_tSNE.csv`` and
   ``data/embeddings/<dataset_id>_UMAP.csv``.
5. Appends runtime and peak‑RAM information for each embedding
   to ``results/monitoring.csv`` using the step names
   ``embed_PCA_<dataset_id>``, ``embed_tSNE_<dataset_id>`` and
   ``embed_UMAP_<dataset_id>``.

The script aborts with a non‑zero exit code if any required file
is missing, if NaNs are detected in an embedding, or if the
monitoring CSV cannot be updated.
"""

import json
import time
import psutil
import logging
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import umap

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_manifest() -> list:
    """Load the manifest JSON and return the list of entries."""
    manifest_path = paths.data("manifest.json")
    if not manifest_path.is_file():
        log.error(f"Manifest file not found at {manifest_path}")
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _load_processed_matrix(dataset_id: str) -> pd.DataFrame:
    """Load the processed matrix for a given dataset."""
    matrix_path = paths.data("processed", f"{dataset_id}_matrix.parquet")
    if not matrix_path.is_file():
        log.error(f"Processed matrix not found for {dataset_id} at {matrix_path}")
        raise FileNotFoundError(f"Processed matrix not found for {dataset_id}")
    df = pd.read_parquet(matrix_path)
    if df.empty:
        log.error(f"Processed matrix for {dataset_id} is empty")
        raise ValueError(f"Processed matrix for {dataset_id} is empty")
    return df

def _ensure_cell_id(df: pd.DataFrame) -> pd.Series:
    """
    Return a Series of cell identifiers.
    If the dataframe already contains a ``cell_id`` column we use it,
    otherwise we generate IDs of the form ``cell_0``, ``cell_1`` ….
    """
    if "cell_id" in df.columns:
        return df["cell_id"]
    else:
        return pd.Series([f"cell_{i}" for i in range(df.shape[0])], name="cell_id")

def _run_pca(data: np.ndarray, n_components: int = 30, random_state: int = 42) -> np.ndarray:
    pca = PCA(n_components=n_components, random_state=random_state)
    return pca.fit_transform(data)

def _run_tsne(
    data: np.ndarray,
    n_components: int = 2,
    perplexity: int = 30,
    n_iter: int = 1000,
    random_state: int = 42,
) -> np.ndarray:
    tsne = TSNE(
        n_components=n_components,
        perplexity=perplexity,
        n_iter=n_iter,
        random_state=random_state,
    )
    return tsne.fit_transform(data)

def _run_umap(
    data: np.ndarray,
    n_components: int = 2,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    random_state: int = 42,
) -> np.ndarray:
    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        random_state=random_state,
    )
    return reducer.fit_transform(data)

def _write_embedding_csv(
    cell_ids: pd.Series,
    embedding: np.ndarray,
    output_path: Path,
    col_prefix: str,
) -> None:
    """Write an embedding to CSV with a ``cell_id`` column."""
    df = pd.DataFrame(embedding, columns=[f"{col_prefix}{i+1}" for i in range(embedding.shape[1])])
    df.insert(0, "cell_id", cell_ids.values)
    df.to_csv(output_path, index=False)
    log.info(f"Saved embedding to {output_path}")

def _update_monitoring(step_name: str, start_time: float, peak_rss: int) -> None:
    """
    Append a row to ``results/monitoring.csv``.
    The CSV has columns: step,wall_time_s,peak_ram_bytes
    """
    monitoring_path = paths.results("monitoring.csv")
    wall_time = time.time() - start_time
    row = f"{step_name},{wall_time:.6f},{peak_rss}\n"

    # Ensure the parent directory exists (paths.results does this)
    if not monitoring_path.is_file():
        # Create a header if the file does not yet exist
        monitoring_path.write_text("step,wall_time_s,peak_ram_bytes\n")
    with open(monitoring_path, "a", encoding="utf-8") as f:
        f.write(row)
    log.info(f"Monitoring updated for step {step_name}")

# ----------------------------------------------------------------------
# Main embedding generation routine
# ----------------------------------------------------------------------
def _process_dataset(entry: dict) -> None:
    dataset_id = entry["dataset_id"]
    log.info(f"Generating embeddings for dataset {dataset_id}")

    # Load matrix
    df = _load_processed_matrix(dataset_id)
    cell_ids = _ensure_cell_id(df)

    # Assume the remaining columns are numeric features
    feature_cols = [c for c in df.columns if c != "cell_id"]
    if not feature_cols:
        raise ValueError(f"No feature columns found in processed matrix for {dataset_id}")

    data_matrix = df[feature_cols].to_numpy()
    if np.isnan(data_matrix).any():
        raise ValueError(f"NaNs detected in processed matrix for {dataset_id}")

    # ------------------------------------------------------------------
    # PCA
    # ------------------------------------------------------------------
    step = f"embed_PCA_{dataset_id}"
    start = time.time()
    proc = psutil.Process()
    pca_emb = _run_pca(data_matrix, n_components=30, random_state=42)
    peak_ram = proc.memory_info().rss
    _write_embedding_csv(
        cell_ids,
        pca_emb,
        paths.data("embeddings", f"{dataset_id}_PCA.csv"),
        col_prefix="PC",
    )
    _update_monitoring(step, start, peak_ram)

    # ------------------------------------------------------------------
    # t‑SNE
    # ------------------------------------------------------------------
    step = f"embed_tSNE_{dataset_id}"
    start = time.time()
    proc = psutil.Process()
    tsne_emb = _run_tsne(
        data_matrix,
        n_components=2,
        perplexity=30,
        n_iter=1000,
        random_state=42,
    )
    peak_ram = proc.memory_info().rss
    _write_embedding_csv(
        cell_ids,
        tsne_emb,
        paths.data("embeddings", f"{dataset_id}_tSNE.csv"),
        col_prefix="Dim",
    )
    _update_monitoring(step, start, peak_ram)

    # ------------------------------------------------------------------
    # UMAP
    # ------------------------------------------------------------------
    step = f"embed_UMAP_{dataset_id}"
    start = time.time()
    proc = psutil.Process()
    umap_emb = _run_umap(
        data_matrix,
        n_components=2,
        n_neighbors=15,
        min_dist=0.1,
        random_state=42,
    )
    peak_ram = proc.memory_info().rss
    _write_embedding_csv(
        cell_ids,
        umap_emb,
        paths.data("embeddings", f"{dataset_id}_UMAP.csv"),
        col_prefix="Dim",
    )
    _update_monitoring(step, start, peak_ram)

def main() -> int:
    """
    Entry point for the script. Returns 0 on success, non‑zero on
    failure.
    """
    try:
        manifest = _load_manifest()
    except Exception as e:
        log.error(f"Failed to load manifest: {e}")
        return 1

    available_entries = [e for e in manifest if e.get("status") == "Available"]
    if not available_entries:
        log.error("No available datasets found in the manifest.")
        return 1

    for entry in available_entries:
        try:
            _process_dataset(entry)
        except Exception as e:
            log.error(f"Embedding generation failed for {entry.get('dataset_id')}: {e}")
            return 1

    log.info("All embeddings generated successfully.")
    return 0

if __name__ == "__main__":
    import sys

    sys.exit(main())
