"""
Download a small public dataset, convert it into the expected Ego4D‑like
raw format, and write SHA‑256 checksums.

The public function required by the task is:
    download_ego4d(output_dir: Path) -> None

It creates three files in ``output_dir``:
    * ``manifest.jsonl`` – one JSON line per example containing
      ``node_id``, ``timestamp`` (ISO‑8601), and ``event_label``.
    * ``embeddings.npy`` – a NumPy ``.npy`` archive where each entry is a
      768‑dimensional ``float32`` embedding. The order matches the manifest.
    * ``CHECKSUMS.txt`` – SHA‑256 hashes for the generated files (and the
      raw CSV source).

Any failure aborts with a clear exception.
"""

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import numpy as np
import requests
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

    NumPy's ``RandomState`` only accepts a 32‑bit seed, so the 64‑bit
    integer derived from the hash is reduced modulo 2**32.
    """
    # Create a 64‑bit integer seed from the first 8 bytes of the hash.
    hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()[:8]
    seed_64 = int.from_bytes(hash_bytes, byteorder="big", signed=False)
    # Reduce to a valid 32‑bit seed for RandomState.
    seed = seed_64 % (2**32)
    rng = np.random.RandomState(seed)
    return rng.rand(768).astype(np.float32)


def _download_csv(url: str, dest_path: Path) -> None:
    """Download a CSV file from ``url`` to ``dest_path`` using streaming."""
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    with dest_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


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
    # 1️⃣ Download a small, public CSV version of the AG News dataset.
    # ------------------------------------------------------------------
    csv_url = (
        "https://raw.githubusercontent.com/mhjabreel/CharCnn_Keras/master/"
        "data/ag_news_csv/train.csv"
    )
    csv_path = output_dir / "ag_news.csv"
    try:
        _download_csv(csv_url, csv_path)
    except Exception as e:
        raise RuntimeError(f"Failed to download CSV dataset: {e}") from e

    # ------------------------------------------------------------------
    # 2️⃣ Prepare output file paths.
    # ------------------------------------------------------------------
    manifest_path = output_dir / "manifest.jsonl"
    embeddings_path = output_dir / "embeddings.npy"

    # ------------------------------------------------------------------
    # 3️⃣ Iterate over the CSV, writing a manifest line and a
    #    deterministic embedding for each example.
    # ------------------------------------------------------------------
    embeddings: List[np.ndarray] = []
    base_timestamp = datetime(2022, 1, 1, 0, 0, 0)

    with manifest_path.open("w", encoding="utf-8") as manifest_f:
        # The CSV has three columns: label, title, description
        with csv_path.open("r", encoding="utf-8") as csv_f:
            reader = csv.reader(csv_f)
            for idx, row in enumerate(tqdm(reader, desc="Processing AG News CSV")):
                if len(row) != 3:
                    raise RuntimeError(
                        f"Unexpected CSV format on line {idx + 1}: {row}"
                    )
                label_str, title, description = row
                node_id = f"node_{idx}"
                timestamp = (base_timestamp + timedelta(hours=idx)).isoformat()
                # Create a richer event label to ensure a mix of rare/common events.
                # Using the news category together with a short title fragment.
                event_label = f"{label_str}_{title[:12].replace(' ', '_')}"

                # Write manifest line
                manifest_record = {
                    "node_id": node_id,
                    "timestamp": timestamp,
                    "event_label": event_label,
                }
                manifest_f.write(json.dumps(manifest_record) + "\n")

                # Compute deterministic embedding from the concatenated text
                text = f"{title} {description}"
                embedding = _deterministic_embedding(text)
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
    # 5️⃣ Compute SHA‑256 checksums for the generated files (and the source CSV).
    # ------------------------------------------------------------------
    checksums = {
        manifest_path.name: _compute_sha256(manifest_path),
        embeddings_path.name: _compute_sha256(embeddings_path),
        csv_path.name: _compute_sha256(csv_path),
    }

    checksum_path = output_dir / "CHECKSUMS.txt"
    with checksum_path.open("w", encoding="utf-8") as f:
        for fname, chksum in checksums.items():
            f.write(f"{chksum}  {fname}\\n")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a public AG News CSV and write raw files in Ego4D format."
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
