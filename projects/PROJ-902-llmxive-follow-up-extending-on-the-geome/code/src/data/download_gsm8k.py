"""
Download GSM8K dataset splits (train and test) in streaming mode,
write them as JSONL files, and generate a SHA‑256 checksum file.

This script is intended to be run directly:
    python -m src.data.download_gsm8k
It creates the following files under the project root:
  data/gsm8k/raw/gsm8k_train.jsonl
  data/gsm8k/raw/gsm8k_test.jsonl
  data/gsm8k/checksums.json
"""

import json
import hashlib
from pathlib import Path
from typing import Dict

from datasets import load_dataset


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of a file and return the hexadecimal digest.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def save_checksums(checksum_path: Path, checksums: Dict[str, str]) -> None:
    """
    Write a JSON file mapping filenames to their SHA‑256 checksums.
    """
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)


def load_checksums(checksum_path: Path) -> Dict[str, str]:
    """
    Load a checksum JSON file produced by ``save_checksums``.
    """
    with checksum_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_jsonl(dataset, output_path: Path) -> None:
    """
    Write a streaming ``datasets`` split to a JSON‑Lines file.
    Each example is dumped as a single JSON object per line.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for example in dataset:
            # ``json.dumps`` ensures proper escaping; ``ensure_ascii=False`` keeps Unicode.
            f.write(json.dumps(example, ensure_ascii=False) + "\n")


def main() -> None:
    """
    Main entry point: download the GSM8K train and test splits,
    write them to ``data/gsm8k/raw`` as JSONL files, and generate
    a checksum manifest at ``data/gsm8k/checksums.json``.
    """
    # Resolve the project root (four levels up from this file):
    #   code/src/data/download_gsm8k.py -> code/src/data -> code/src -> code -> <project_root>
    project_root = Path(__file__).resolve().parents[3]

    data_dir = project_root / "data" / "gsm8k"
    raw_dir = data_dir / "raw"
    checksum_file = data_dir / "checksums.json"

    # Load the GSM8K dataset in streaming mode to avoid loading everything into memory.
    # The Hugging Face hub hosts the dataset under the identifier ``gsm8k``.
    train_ds = load_dataset("gsm8k", split="train", streaming=True)
    test_ds = load_dataset("gsm8k", split="test", streaming=True)

    # Destination file paths
    train_path = raw_dir / "gsm8k_train.jsonl"
    test_path = raw_dir / "gsm8k_test.jsonl"

    # Write the splits to disk.
    _write_jsonl(train_ds, train_path)
    _write_jsonl(test_ds, test_path)

    # Compute SHA‑256 checksums for the generated files.
    checksums = {
        "gsm8k_train.jsonl": compute_sha256(train_path),
        "gsm8k_test.jsonl": compute_sha256(test_path),
    }

    # Persist the checksum manifest.
    save_checksums(checksum_file, checksums)


if __name__ == "__main__":
    main()
