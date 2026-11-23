"""
GSM8K dataset download script with checksum verification.

This script streams the GSM8K dataset splits from the HuggingFace Hub,
writes each split to a JSON‑lines file under ``data/gsm8k/``, records the
SHA‑256 checksum for each file, and finally validates the recorded checksums
before returning control to the caller.

If any checksum does not match the recorded value, the script aborts with
a ``RuntimeError`` to prevent downstream corruption.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Iterable

from datasets import load_dataset

# Local imports – these modules are part of the existing project API surface
from src.data.checksums import (
    compute_all_checksums,
    write_checksums,
    validate_checksums,
)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
DATA_ROOT = Path("data")
GSM8K_ROOT = DATA_ROOT / "gsm8k"
CHECKSUMS_FILE = DATA_ROOT / "checksums.txt"

# The splits we want to download.  The official GSM8K repo provides
# ``train``, ``validation`` and ``test`` splits.
SPLITS = ("train", "validation", "test")


# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path`` and return it as a hex string.
    """
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write_split(split_name: str, records: Iterable[Dict]) -> Path:
    """
    Write a single split to ``<split_name>.jsonl`` inside ``GSM8K_ROOT``.
    Returns the path to the written file.
    """
    GSM8K_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = GSM8K_ROOT / f"{split_name}.jsonl"
    with out_path.open("w", encoding="utf-8") as fp:
        for rec in records:
            json.dump(rec, fp, ensure_ascii=False)
            fp.write("\n")
    return out_path


# --------------------------------------------------------------------------- #
# Core download / verification workflow
# --------------------------------------------------------------------------- #
def download_gsm8k() -> Dict[str, Path]:
    """
    Stream the GSM8K dataset, write each split to disk and return a mapping
    from split name to the corresponding file path.
    """
    split_to_path: Dict[str, Path] = {}
    # ``load_dataset`` with ``streaming=True`` returns an ``IterableDataset``.
    # We request the ``train``, ``validation`` and ``test`` splits.
    dataset = load_dataset("gsm8k", split=SPLITS, streaming=True)

    for split_name, split_iter in zip(SPLITS, dataset):
        # Write the streamed records to a JSON‑lines file.
        path = _write_split(split_name, split_iter)
        split_to_path[split_name] = path

    return split_to_path


def record_and_verify_checksums(split_paths: Dict[str, Path]) -> None:
    """
    Compute SHA‑256 checksums for each file in ``split_paths``, write them to
    ``CHECKSUMS_FILE`` and immediately validate them.  If any checksum does
    not match, a ``RuntimeError`` is raised.
    """
    # Compute checksums for the freshly written files.
    computed: Dict[str, str] = {
        str(p.relative_to(DATA_ROOT)): compute_sha256(p) for p in split_paths.values()
    }

    # Persist the checksums so that other pipeline stages can reuse them.
    write_checksums(CHECKSUMS_FILE, computed)

    # Validate the just‑written files against the persisted checksums.
    # ``validate_checksums`` raises a ``ValueError`` if a mismatch is found.
    try:
        validate_checksums(CHECKSUMS_FILE, computed)
    except ValueError as exc:
        raise RuntimeError(f"Checksum validation failed: {exc}") from exc


def main() -> None:
    """
    Entry point for ``python -m src.data.download_gsm8k``.
    Downloads the dataset, records checksums, and aborts on any mismatch.
    """
    # Step 1: download the splits.
    split_paths = download_gsm8k()

    # Step 2: compute, write and validate SHA‑256 checksums.
    record_and_verify_checksums(split_paths)

    # If we reach this point, everything succeeded.
    print("GSM8K download completed and checksums verified.")


if __name__ == "__main__":
    main()