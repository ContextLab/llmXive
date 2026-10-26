"""
Preprocess raw Ego4D data into a parquet table of memory nodes.

This script reads the ``manifest.jsonl`` and ``embeddings.npy`` files
produced by ``src/data/download.py`` and creates a parquet file with
the required schema, adding the ``is_rare`` flag.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


def _load_manifest(raw_dir: Path):
    """Load the manifest JSON lines file."""
    manifest_path = Path(raw_dir) / "manifest.jsonl"
    if not manifest_path.is_file():
        raise RuntimeError(f"Manifest file not found at {manifest_path}")
    records = []
    with manifest_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Invalid JSON line in manifest: {e}") from e
            records.append(rec)
    if not records:
        raise RuntimeError("Manifest is empty.")
    return records


def _load_embeddings(raw_dir: Path):
    """Load the embeddings NumPy array."""
    embeddings_path = Path(raw_dir) / "embeddings.npy"
    if not embeddings_path.is_file():
        raise RuntimeError(f"Embeddings file not found at {embeddings_path}")
    try:
        arr = np.load(embeddings_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load embeddings.npy: {e}") from e
    if arr.ndim != 2 or arr.shape[1] != 768:
        raise RuntimeError(
            f"Embeddings array must have shape (N, 768); got {arr.shape}"
        )
    return arr


def _join_and_flag(manifest, embeddings):
    """Join manifest records with embeddings and compute ``is_rare``."""
    if len(manifest) != embeddings.shape[0]:
        raise RuntimeError(
            f"Number of manifest records ({len(manifest)}) does not match number of embeddings ({embeddings.shape[0]})."
        )

    # Count event_label frequencies
    label_counts = Counter(rec["event_label"] for rec in manifest)

    rows = []
    for rec, embedding in zip(manifest, embeddings):
        is_rare = label_counts[rec["event_label"]] <= 5
        rows.append(
            {
                "node_id": rec["node_id"],
                "timestamp": rec["timestamp"],
                "event_label": rec["event_label"],
                "embedding": embedding.tobytes(),
                "is_rare": is_rare,
            }
        )
    df = pd.DataFrame(rows)
    df = df[["node_id", "timestamp", "event_label", "embedding", "is_rare"]]
    return df


def build_memory_nodes_parquet(raw_dir: Path, output_path: Path) -> None:
    """Create the parquet file from raw data."""
    manifest = _load_manifest(raw_dir)
    embeddings = _load_embeddings(raw_dir)
    df = _join_and_flag(manifest, embeddings)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, engine="pyarrow", index=False)


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Preprocess Ego4D raw data into a parquet table of memory nodes."
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        required=True,
        help="Directory containing the raw manifest and embeddings.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to write the resulting parquet file.",
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    try:
        build_memory_nodes_parquet(Path(args.raw_dir), Path(args.output))
    except Exception as e:
        raise RuntimeError(f"Preprocessing failed: {e}") from e


if __name__ == "__main__":
    main()
