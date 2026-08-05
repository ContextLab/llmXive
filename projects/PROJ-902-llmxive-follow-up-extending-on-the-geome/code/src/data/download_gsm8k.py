"""
download_gsm8k.py
-----------------

This script streams the GSM8K dataset from the HuggingFace Hub and caches each
split locally as line‑delimited JSON files under ``data/gsm8k/``.  After the
download it computes a SHA‑256 checksum for every generated file and stores the
results in ``data/gsm8k/checksums.json``.  The public API mirrors the
expectations of the task list:

* ``compute_sha256(path: Path) -> str``
* ``save_checksums(checksums: Dict[str, str], path: Path) -> None``
* ``load_checksums(path: Path) -> Dict[str, str]``
* ``main()`` – entry point used by the integration test.

The implementation streams the dataset (``streaming=True``) so memory usage
stays bounded regardless of dataset size.  Each example is written as a single
JSON object on its own line (JSON‑Lines format), which is convenient for later
processing and checksum validation.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict

from datasets import load_dataset


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path`` and return the hex digest.

    The function reads the file in 4 MiB chunks to avoid loading the whole file
    into memory.
    """
    hash_sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def save_checksums(checksums: Dict[str, str], path: Path) -> None:
    """
    Persist a mapping ``{filename: sha256}`` as JSON.

    The JSON file is written with ``indent=2`` for readability.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(checksums, fp, indent=2, sort_keys=True)


def load_checksums(path: Path) -> Dict[str, str]:
    """
    Load a checksum mapping written by :func:`save_checksums`.

    Raises ``FileNotFoundError`` if the file does not exist.
    """
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _stream_and_write(split: str, out_path: Path) -> None:
    """
    Stream the given ``split`` of the GSM8K dataset and write each example as a
    JSON line to ``out_path``.
    """
    dataset = load_dataset("gsm8k", split=split, streaming=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write one JSON object per line.
    with out_path.open("w", encoding="utf-8") as fp:
        for example in dataset:
            json.dump(example, fp, ensure_ascii=False)
            fp.write("\n")


def main() -> None:
    """
    Download all GSM8K splits, cache them locally, and write checksum metadata.

    The function is deliberately side‑effectful – it creates the directory
    ``data/gsm8k/`` relative to the repository root (the directory that contains
    the ``code/`` folder) and writes ``train.jsonl`` and ``test.jsonl`` files.
    After the files are written, a ``checksums.json`` file containing SHA‑256
    digests for each cached file is created.
    """
    # Resolve the project root (``.../code`` -> repository root)
    repo_root = Path(__file__).resolve().parents[2]  # code/src/data -> repo root
    data_dir = repo_root / "data" / "gsm8k"
    data_dir.mkdir(parents=True, exist_ok=True)

    splits = ["train", "test"]
    for split in splits:
        out_file = data_dir / f"{split}.jsonl"
        print(f"Downloading GSM8K '{split}' split → {out_file}")
        _stream_and_write(split, out_file)

    # Compute checksums for all generated files.
    checksums: Dict[str, str] = {}
    for jsonl_path in data_dir.glob("*.jsonl"):
        checksum = compute_sha256(jsonl_path)
        checksums[jsonl_path.name] = checksum

    checksum_path = data_dir / "checksums.json"
    save_checksums(checksums, checksum_path)
    print(f"Checksums written to {checksum_path}")


if __name__ == "__main__":
    # When executed as a script ``python -m src.data.download_gsm8k`` or
    # ``python code/src/data/download_gsm8k.py`` the ``main`` function is run.
    main()
