"""
generate_embeddings.py

Generates PCA, t-SNE, and UMAP embeddings for processed scRNA-seq datasets.

Inputs:
  - data/manifest.json: To identify available datasets.
  - data/processed/<dataset_id>_matrix.parquet: Preprocessed gene expression matrix.

Outputs:
  - data/embeddings/<dataset_id>_PCA.csv (cell_id, PC1...PC30)
  - data/embeddings/<dataset_id>_tSNE.csv (cell_id, Dim1, Dim2)
  - data/embeddings/<dataset_id>_UMAP.csv (cell_id, Dim1, Dim2)
  - results/monitoring.csv: Appends runtime and peak RAM usage.
"""

import json
import time
import psutil
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
import scanpy as sc
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import umap

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_manifest() -> List[Dict[str, Any]]:
    """Load the manifest JSON."""
    manifest_path = paths.data("manifest.json")
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _generate_processed_matrix(entry: Dict[str, Any]) -> pd.DataFrame:
    """
    Fallback generator for processed matrix if parquet is missing.
    Implements T008 preprocessing: Log-CPM, HVG (Seurat), Deterministic Subsampling.
    """
    dataset_id = entry["dataset_id"]
    raw_path = Path(entry["raw_file_path"])
    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw file not found for {dataset_id} at {raw_path}")

    log.info(f"Generating processed matrix for {dataset_id} from raw file {raw_path}")
    adata = sc.read_h5ad(raw_path)

    # Dense conversion for calculation
    X = adata.X.toarray() if sc.sparse.issparse(adata.X) else np.asarray(adata.X)

    # Log-CPM
    counts_per_cell = X.sum(axis=1, keepdims=True)
    counts_per_cell[counts_per_cell == 0] = 1
    log_cpm = np.log1p((X / counts_per_cell) * 1e6)
    adata.X = log_cpm

    # HVG selection (Seurat flavor, top 2000)
    sc.pp.highly_variable_genes(adata, flavor="seurat", n_top_genes=2000, subset=False)
    adata = adata[:, adata.var["highly_variable"]]

    # Deterministic subsampling (seed=42, size=5000 if > 10000)
    if adata.n_obs > 10000:
        rng = np.random.default_rng(42)
        idx = rng.choice(adata.n_obs, size=5000, replace=False)
        adata = adata[idx, :]

    cell_ids = adata.obs_names if adata.obs_names is not None else [f"cell_{i}" for i in range(adata.n_obs)]
    df = pd.DataFrame(adata.X, index=cell_ids, columns=adata.var_names)
    df.reset_index(inplace=True)
    df.rename(columns={"index": "cell_id"}, inplace=True)

    processed_path = paths.data("processed", f"{dataset_id}_matrix.parquet")
    df.to_parquet(processed_path, index=False)
    return df

def _load_processed_matrix(dataset_id: str) -> pd.DataFrame:
    """Load processed matrix from parquet or generate it."""
    matrix_path = paths.data("processed", f"{dataset_id}_matrix.parquet")
    if matrix_path.is_file():
        return pd.read_parquet(matrix_path)

    log.warning(f"Processed matrix for {dataset_id} missing. Generating...")
    manifest = _load_manifest()
    entry = next((e for e in manifest if e["dataset_id"] == dataset_id), None)
    if entry is None:
        raise KeyError(f"No manifest entry for {dataset_id}")
    return _generate_processed_matrix(entry)

def _update_monitoring(step_name: str, start_time: float, peak_rss: int) -> None:
    """Append resource usage to results/monitoring.csv."""
    monitoring_path = paths.results("monitoring.csv")
    wall_time = time.time() - start_time
    if not monitoring_path.is_file():
        monitoring_path.write_text("step,wall_time_s,peak_ram_bytes\n")
    with open(monitoring_path, "a", encoding="utf-8") as f:
        f.write(f"{step_name},{wall_time:.6f},{peak_rss}\n")

def _write_embedding(cell_ids: pd.Series, embedding: np.ndarray, output_path: Path, prefix: str) -> None:
    """Write embedding matrix to CSV with cell_id."""
    if np.isnan(embedding).any():
        raise ValueError(f"NaNs detected in embedding for {output_path}")
    
    cols = [f"{prefix}{i+1}" for i in range(embedding.shape[1])]
    df = pd.DataFrame(embedding, columns=cols)
    df.insert(0, "cell_id", cell_ids.values)
    df.to_csv(output_path, index=False)

def _process_dataset(entry: Dict[str, Any]) -> None:
    dataset_id = entry["dataset_id"]
    log.info(f"Processing embeddings for {dataset_id}")
    
    df = _load_processed_matrix(dataset_id)
    cell_ids = df["cell_id"]
    data_matrix = df.drop(columns=["cell_id"]).to_numpy()
    
    # PCA
    step_pca = f"embed_PCA_{dataset_id}"
    start = time.time()
    pca_res = PCA(n_components=30, random_state=42).fit_transform(data_matrix)
    _write_embedding(cell_ids, pca_res, paths.data("embeddings", f"{dataset_id}_PCA.csv"), "PC")
    _update_monitoring(step_pca, start, psutil.Process().memory_info().rss)

    # t-SNE
    step_tsne = f"embed_tSNE_{dataset_id}"
    start = time.time()
    tsne_res = TSNE(n_components=2, perplexity=30, n_iter=1000, random_state=42).fit_transform(data_matrix)
    _write_embedding(cell_ids, tsne_res, paths.data("embeddings", f"{dataset_id}_tSNE.csv"), "Dim")
    _update_monitoring(step_tsne, start, psutil.Process().memory_info().rss)

    # UMAP
    step_umap = f"embed_UMAP_{dataset_id}"
    start = time.time()
    umap_res = umap.UMAP(n_components=2, n_neighbors=15, min_dist=0.1, random_state=42).fit_transform(data_matrix)
    _write_embedding(cell_ids, umap_res, paths.data("embeddings", f"{dataset_id}_UMAP.csv"), "Dim")
    _update_monitoring(step_umap, start, psutil.Process().memory_info().rss)

def main() -> int:
    try:
        manifest = _load_manifest()
        available = [e for e in manifest if e.get("status") == "Available"]
        if not available:
            log.error("No available datasets in manifest.")
            return 1
        for entry in available:
            _process_dataset(entry)
        log.info("All embeddings generated successfully.")
        return 0
    except Exception as e:
        log.error(f"Embedding generation failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
