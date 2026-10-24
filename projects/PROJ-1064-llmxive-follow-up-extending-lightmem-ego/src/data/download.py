"""
Download Ego4D dataset and write raw files with checksums.
"""

import argparse
import hashlib
import json
from pathlib import Path

from datasets import load_dataset
from tqdm.auto import tqdm


def _write_jsonl(dataset, output_path: Path):
    """Write a HuggingFace Dataset to a JSONL file."""
    with output_path.open("w", encoding="utf-8") as f:
        for example in tqdm(dataset, desc=f"Writing {output_path.name}", unit="record"):
            json.dump(example, f)
            f.write("\n")


def _compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download_ego4d(output_dir: Path) -> None:
    """
    Download the Ego4D training split, save as JSONL, and write SHA256 checksum.

    Parameters
    ----------
    output_dir: Path
        Directory where raw files will be stored.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load the dataset (non‑streaming to be able to write locally)
    ds = load_dataset("ego4d/ego4d", split="train", streaming=False)

    jsonl_path = output_dir / "ego4d_train.jsonl"
    _write_jsonl(ds, jsonl_path)

    checksum = _compute_sha256(jsonl_path)
    checksum_path = output_dir / "CHECKSUMS.txt"
    with checksum_path.open("w", encoding="utf-8") as f:
        f.write(f"{checksum}  {jsonl_path.name}\\n")


def _parse_args():
    parser = argparse.ArgumentParser(description="Download Ego4D raw data.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory where raw files will be stored. Defaults to 'data/raw'.",
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    download_ego4d(Path(args.output_dir))


if __name__ == "__main__":
    main()
