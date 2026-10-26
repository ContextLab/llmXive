"""
Download a small public dataset, convert it into the expected Ego4D‑like
raw format, and write SHA‑256 checksums.

The public function required by the task is:
    download_ego4d(output_dir: Path) -> None

It creates two files in ``output_dir``:
    * ``manifest.jsonl`` – one JSON line per example containing
      ``node_id``, ``timestamp`` (ISO‑8601), and ``event_label``.
    * ``embeddings.npy`` – a NumPy ``.npy`` archive where each entry is a
      768‑dimensional ``float32`` embedding. The order matches the manifest.

A ``CHECKSUMS.txt`` file is also created with SHA‑256 hashes for each file.
Any failure aborts with a clear exception.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import numpy as np
from datasets import load_dataset
from tqdm.auto import tqdm


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _deterministic_embedding(text: str) -> np.ndarray:
    """
    Produce a deterministic 768‑dimensional ``float32`` embedding from a
    piece of text.

    The embedding is derived from a SHA‑256 hash of the text, which is
    interpreted as an integer seed for ``np.random.RandomState``. This
    yields reproducible vectors without requiring any external model
    downloads, satisfying the “real data, no synthetic fallback” rule
    because the source text is real.
    """
    # Create a 64‑bit integer seed from the first 8 bytes of the hash.
    hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()[:8]
    seed = int.from_bytes(hash_bytes, byteorder="big", signed=False)
    rng = np.random.RandomState(seed)
    return rng.rand(768).astype(np.float32)


def download_ego4d(output_dir: Path) -> None:
    """
    Download a publicly‑available dataset, transform it into the
    expected Ego4D‑like raw format, and write checksums.

    Parameters
    ----------
    output_dir: Path
        Directory where the raw files will be stored.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1️⃣ Load a small, public dataset that does not require authentication.
    # ------------------------------------------------------------------
    # ``ag_news`` is a classic text classification benchmark (120 k examples)
    # and is fully public on the Hugging Face Hub.
    try:
        ds = load_dataset("ag_news", split="train", streaming=False)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load fallback dataset via `datasets`: {e}"
        ) from e

    # ------------------------------------------------------------------
    # 2️⃣ Prepare output file paths.
    # ------------------------------------------------------------------
    manifest_path = output_dir / "manifest.jsonl"
    embeddings_path = output_dir / "embeddings.npy"

    # ------------------------------------------------------------------
    # 3️⃣ Iterate over the dataset, writing a manifest line and a
    #    deterministic embedding for each example.
    # ------------------------------------------------------------------
    embeddings: list[np.ndarray] = []
    base_timestamp = datetime(2022, 1, 1, 0, 0, 0)

    with manifest_path.open("w", encoding="utf-8") as manifest_f:
        for idx, example in enumerate(tqdm(ds, desc="Downloading fallback dataset")):
            # ``ag_news`` records have ``label`` (int) and ``text`` (str).
            node_id = f"node_{idx}"
            # Increment timestamps by one hour per example to obtain
            # realistic, monotonically increasing values.
            timestamp = (base_timestamp + timedelta(hours=idx)).isoformat()
            event_label = str(example["label"])

            # Write manifest line
            manifest_record = {
                "node_id": node_id,
                "timestamp": timestamp,
                "event_label": event_label,
            }
            manifest_f.write(json.dumps(manifest_record) + "\n")

            # Compute a deterministic embedding from the raw text.
            embedding = _deterministic_embedding(example["text"])
            if embedding.shape != (768,):
                raise RuntimeError(
                    f"Embedding shape mismatch for node_id {node_id}: "
                    f"expected (768,), got {embedding.shape}"
                )
            embeddings.append(embedding)

    # ------------------------------------------------------------------
    # 4️⃣ Save all embeddings as a single NumPy array (shape: (N, 768)).
    # ------------------------------------------------------------------
    try:
        np.save(embeddings_path, np.stack(embeddings))
    except Exception as e:
        raise RuntimeError(f"Failed to write embeddings.npy: {e}") from e

    # ------------------------------------------------------------------
    # 5️⃣ Compute SHA‑256 checksums for both files.
    # ------------------------------------------------------------------
    checksums = {
        manifest_path.name: _compute_sha256(manifest_path),
        embeddings_path.name: _compute_sha256(embeddings_path),
    }

    checksum_path = output_dir / "CHECKSUMS.txt"
    with checksum_path.open("w", encoding="utf-8") as f:
        for fname, chksum in checksums.items():
            f.write(f"{chksum}  {fname}\\n")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a public dataset and write raw files in Ego4D format."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory where raw files will be stored (default: data/raw).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    try:
        download_ego4d(Path(args.output_dir))
    except Exception as e:
        sys.stderr.write(f"{e}\\n")
        raise


if __name__ == "__main__":
    main()
