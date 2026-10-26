"""
Build a deterministic FAISS HNSW index from memory node embeddings.

The script reads a parquet file containing memory nodes with an
``embedding`` column (stored as raw bytes) and creates:
  * A CPU‑only HNSW index saved to the provided ``--output`` path.
  * A JSON mapping file ``faiss_index_mapping.json`` that maps each
    FAISS row index to the corresponding ``node_id``.
The index parameters are deterministic:
  * seed = 42
  * M = 16
  * ef_construction = 200
  * ef_search = 50
"""

import argparse
import json
from pathlib import Path
import sys

import faiss
import numpy as np
import pandas as pd

def _load_embeddings(parquet_path: Path) -> np.ndarray:
    """Load embeddings from the parquet file as a (N, 768) float32 array."""
    df = pd.read_parquet(parquet_path, engine="pyarrow")
    # ``embedding`` column stores raw bytes; convert each to a numpy array.
    embeddings = np.stack(
        [
            np.frombuffer(b, dtype=np.float32)
            for b in df["embedding"]
        ],
        axis=0,
    )
    if embeddings.shape[1] != 768:
        raise RuntimeError(
            f"Expected embedding dimension 768, got {embeddings.shape[1]}"
        )
    return embeddings

def _load_node_ids(parquet_path: Path) -> list[str]:
    """Return the ordered list of node_id strings from the parquet file."""
    df = pd.read_parquet(parquet_path, engine="pyarrow")
    return df["node_id"].tolist()

def build_faiss_index(parquet_path: Path, output_path: Path) -> None:
    """
    Build and save a deterministic FAISS HNSW index.

    Parameters
    ----------
    parquet_path : Path
        Path to the memory_nodes.parquet file.
    output_path : Path
        Destination file for the FAISS index (e.g., ``faiss_hnsw_ego4d.index``).
    """
    parquet_path = Path(parquet_path)
    output_path = Path(output_path)

    if not parquet_path.is_file():
        raise RuntimeError(f"Parquet file not found at {parquet_path}")

    # Load data
    embeddings = _load_embeddings(parquet_path)
    node_ids = _load_node_ids(parquet_path)

    # Ensure deterministic behaviour
    faiss.rand_seed(42)

    d = embeddings.shape[1]
    M = 16
    index = faiss.IndexHNSWFlat(d, M, faiss.METRIC_L2)
    # Configure construction and search parameters
    index.hnsw.efConstruction = 200
    index.hnsw.efSearch = 50

    # Add vectors
    index.add(embeddings)

    # Write index
    output_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(output_path))

    # Write mapping JSON (row index -> node_id)
    mapping = {str(i): node_id for i, node_id in enumerate(node_ids)}
    mapping_path = output_path.parent / "faiss_index_mapping.json"
    with mapping_path.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a deterministic FAISS HNSW index from memory node embeddings."
    )
    parser.add_argument(
        "--memory-nodes",
        type=str,
        required=True,
        help="Path to the memory_nodes.parquet file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path where the FAISS index will be written.",
    )
    return parser.parse_args()

def main() -> None:
    args = _parse_args()
    try:
        build_faiss_index(
            Path(args.memory_nodes),
            Path(args.output),
        )
    except Exception as e:
        sys.stderr.write(f"{e}\\n")
        raise

if __name__ == "__main__":
    main()
