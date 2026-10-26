"""
Preprocess raw Ego4D data into a parquet table of memory nodes.

The script expects two main artefacts in ``raw_dir``:
    * A JSON file (any name ending with ``.json``) that contains a list of
      dictionaries, each with the keys ``node_id``, ``timestamp`` (ISO‑8601
      string), and ``event_label``.
    * A tar‑gz archive (any name ending with ``.tar.gz`` or ``.tgz``) that
      contains one ``.npy`` file per memory node.  The filename (without the
      extension) must match a ``node_id`` from the JSON manifest and hold a
      768‑dimensional ``float32`` embedding.

The script:
    1. Loads the manifest JSON.
    2. Extracts all ``.npy`` embeddings from the archive.
    3. Joins the two sources on ``node_id``.
    4. Counts occurrences of each ``event_label`` and sets the boolean
       ``is_rare`` flag (``True`` when the count ≤ 5, per FR‑012).
    5. Writes a parquet file matching the schema defined in ``data-model.md``.
    6. Raises a descriptive ``RuntimeError`` if any required field is missing
       or an embedding cannot be parsed.

The implementation streams the tar‑gz file so that even large archives are
handled without exhausting memory.
"""

import argparse
import json
import tarfile
from collections import Counter
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_manifest(raw_dir: Path) -> List[Dict]:
    """Load the first JSON file found in ``raw_dir`` as a list of dicts."""
    json_files = list(raw_dir.glob("*.json"))
    if not json_files:
        raise RuntimeError(f"No JSON manifest found in {raw_dir}")
    manifest_path = json_files[0]
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to read manifest JSON '{manifest_path}': {e}") from e

    if not isinstance(data, list):
        raise RuntimeError(
            f"Manifest JSON must be a list of records, got {type(data)}"
        )
    required_keys = {"node_id", "timestamp", "event_label"}
    for i, rec in enumerate(data):
        if not isinstance(rec, dict):
            raise RuntimeError(f"Record {i} in manifest is not a dict")
        missing = required_keys - rec.keys()
        if missing:
            raise RuntimeError(
                f"Record {i} missing required fields: {', '.join(missing)}"
            )
    return data


def _extract_embeddings(raw_dir: Path) -> Dict[str, np.ndarray]:
    """
    Extract ``.npy`` embeddings from the first tar.gz/tgz archive in ``raw_dir``.
    Returns a mapping ``node_id -> embedding``.
    """
    archive_paths = list(raw_dir.glob("*.tar.gz")) + list(raw_dir.glob("*.tgz"))
    if not archive_paths:
        raise RuntimeError(f"No tar.gz archive with embeddings found in {raw_dir}")
    archive_path = archive_paths[0]

    embeddings: Dict[str, np.ndarray] = {}
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                if member.name.lower().endswith(".npy"):
                    # Derive node_id from filename (strip directories & extension)
                    node_id = Path(member.name).stem
                    f = tar.extractfile(member)
                    if f is None:
                        raise RuntimeError(f"Failed to extract {member.name}")
                    # Load the numpy array from the file‑like object
                    try:
                        arr = np.load(f)
                    except Exception as e:
                        raise RuntimeError(
                            f"Failed to load embedding for node_id '{node_id}': {e}"
                        ) from e
                    if arr.dtype != np.float32:
                        arr = arr.astype(np.float32)
                    if arr.shape != (768,):
                        raise RuntimeError(
                            f"Embedding for node_id '{node_id}' has shape {arr.shape}, expected (768,)"
                        )
                    embeddings[node_id] = arr
    except tarfile.TarError as e:
        raise RuntimeError(f"Error reading tar archive '{archive_path}': {e}") from e

    if not embeddings:
        raise RuntimeError(f"No embeddings were extracted from {archive_path}")
    return embeddings


def _join_and_flag(
    manifest: List[Dict], embeddings: Dict[str, np.ndarray]
) -> pd.DataFrame:
    """
    Join manifest records with embeddings on ``node_id`` and compute the
    ``is_rare`` flag.
    Returns a pandas DataFrame ready for parquet export.
    """
    # Verify that every manifest entry has a corresponding embedding
    missing_embeddings = [
        rec["node_id"] for rec in manifest if rec["node_id"] not in embeddings
    ]
    if missing_embeddings:
        raise RuntimeError(
            f"The following node_id(s) have no embedding in the archive: {missing_embeddings}"
        )

    # Count event_label frequencies
    label_counts = Counter(rec["event_label"] for rec in manifest)

    rows = []
    for rec in manifest:
        node_id = rec["node_id"]
        embedding = embeddings[node_id]
        is_rare = label_counts[rec["event_label"]] <= 5
        rows.append(
            {
                "node_id": node_id,
                "timestamp": rec["timestamp"],
                "event_label": rec["event_label"],
                # Store the raw bytes of the float32 array (compatible with schema)
                "embedding": embedding.tobytes(),
                "is_rare": is_rare,
            }
        )
    df = pd.DataFrame(rows)
    # Ensure column order matches the schema
    df = df[["node_id", "timestamp", "event_label", "embedding", "is_rare"]]
    return df


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def build_memory_nodes_parquet(raw_dir: Path, output_path: Path) -> None:
    """
    Build ``memory_nodes.parquet`` from raw Ego4D files.

    Parameters
    ----------
    raw_dir : Path
        Directory containing the raw JSON manifest and the embeddings archive.
    output_path : Path
        Destination parquet file (e.g., ``data/processed/memory_nodes.parquet``).
    """
    raw_dir = Path(raw_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = _load_manifest(raw_dir)
    embeddings = _extract_embeddings(raw_dir)
    df = _join_and_flag(manifest, embeddings)

    # Write parquet using pyarrow (pandas will pick the appropriate engine)
    try:
        df.to_parquet(output_path, engine="pyarrow", index=False)
    except Exception as e:
        raise RuntimeError(f"Failed to write parquet to '{output_path}': {e}") from e


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess Ego4D raw data into a parquet table of memory nodes."
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        required=True,
        help="Directory containing the raw JSON manifest and embeddings archive.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to write the resulting parquet file.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    try:
        build_memory_nodes_parquet(Path(args.raw_dir), Path(args.output))
    except Exception as e:
        # Propagate a clear error message; the CI runner will surface this.
        raise RuntimeError(f"Preprocessing failed: {e}") from e


if __name__ == "__main__":
    main()
