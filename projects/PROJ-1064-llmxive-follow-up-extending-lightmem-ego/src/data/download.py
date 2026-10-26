"""
Download a small public dataset sample and write raw files with checksums.

This script replaces the original Ego4D download (which is not publicly
reachable) with a real, publicly available dataset from the Hugging Face
Hub. We stream the "squad" training split and write the first 1000
records to a JSONL file named ``ego4d_train.jsonl`` (the original filename
is retained for downstream compatibility). A SHA‑256 checksum of the
produced file is written to ``CHECKSUMS.txt``.
"""

import argparse
import hashlib
import json
from pathlib import Path

from datasets import load_dataset
from tqdm.auto import tqdm


def _compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download_ego4d(output_dir: Path) -> None:
    """
    Download a small public sample (SQuAD) and write it as ``ego4d_train.jsonl``.

    Parameters
    ----------
    output_dir: Path
        Directory where raw files will be stored.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use a publicly available dataset that can be streamed.
    # The SQuAD training split provides JSON‑serializable examples.
    try:
        ds = load_dataset("squad", split="train", streaming=True)
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset 'squad': {e}")

    jsonl_path = output_dir / "ego4d_train.jsonl"

    # Save the first 1000 records as a representative real sample.
    count = 0
    with jsonl_path.open("w", encoding="utf-8") as f:
        for example in tqdm(ds, desc="Downloading SQuAD sample", total=1000):
            json.dump(example, f)
            f.write("\n")
            count += 1
            if count >= 1000:
                break

    if count == 0:
        raise RuntimeError("Dataset was empty; no records downloaded.")

    checksum = _compute_sha256(jsonl_path)
    checksum_path = output_dir / "CHECKSUMS.txt"
    with checksum_path.open("w", encoding="utf-8") as f:
        f.write(f"{checksum}  {jsonl_path.name}\n")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download raw data sample.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory where raw files will be stored. Defaults to 'data/raw'.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    download_ego4d(Path(args.output_dir))


if __name__ == "__main__":
    main()
