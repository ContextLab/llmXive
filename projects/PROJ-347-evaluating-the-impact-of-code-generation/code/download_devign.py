"""
download_devign.py

This script streams the Python subset of the Devign dataset from HuggingFace,
writes the raw records to `data/raw/devign/devign_train.jsonl`, and records a
SHA‑256 checksum for the output file in `data/checksums.json`.

The script is intended to be invoked via the pipeline orchestrator:
    from code.download_devign import main as download_devign_main
    download_devign_main()
"""
import json
import hashlib
from pathlib import Path
from typing import Dict

import pandas as pd
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum should be calculated.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_checksums(path: Path) -> Dict[str, str]:
    """
    Load a JSON checksum mapping; return an empty dict if the file does not exist.

    Parameters
    ----------
    path: Path
        Path to the JSON file containing checksum mappings.

    Returns
    -------
    dict
        Mapping from filename (str) to SHA‑256 checksum (str).
    """
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Failed to load checksums from {path}: {e}")
        return {}


def save_checksums(path: Path, data: Dict[str, str]) -> None:
    """
    Write checksum mapping to a JSON file (pretty‑printed).

    Parameters
    ----------
    path: Path
        Destination path for the JSON file.
    data: dict
        Mapping from filename to checksum.
    """
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        log.info(f"Checksums saved to {path}")
    except Exception as e:
        log.error(f"Failed to write checksums to {path}: {e}")
        raise


# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Fetch the Devign dataset (Python subset) and store it as a JSONL file.
    A SHA‑256 checksum for the generated file is recorded in `data/checksums.json`.
    """
    # Destination directory and file
    raw_dir: Path = paths.data("raw", "devign")
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path: Path = raw_dir / "devign_train.jsonl"

    log.info("Starting download of the Devign dataset (Python subset).")
    # Load the dataset in streaming mode to avoid large memory consumption.
    # The HuggingFace identifier for the Devign dataset is "devign".
    # We request the 'train' split because it contains the labelled vulnerable code.
    try:
        dataset = load_dataset(
            "devign",
            split="train",
            streaming=True,
        )
    except Exception as e:
        log.error(f"Failed to load Devign dataset via `datasets`: {e}")
        raise

    # Write each record as a JSON line.
    records_written = 0
    with out_path.open("w", encoding="utf-8") as outfile:
        for record in dataset:
            # Expect fields like `code`, `vulnerability_label`, `language`, etc.
            # Keep only Python records.
            language = record.get("language") or record.get("lang") or ""
            if language.lower() != "python":
                continue
            json_line = json.dumps(record, ensure_ascii=False)
            outfile.write(json_line + "\n")
            records_written += 1

    if records_written == 0:
        log.error(
            "No Python records were found in the Devign dataset. "
            "Check that the dataset identifier and language field are correct."
        )
        raise RuntimeError("Empty Devign Python subset.")

    log.info(f"Wrote {records_written} Python records to {out_path}")

    # Compute checksum for the generated file.
    checksum = compute_sha256(out_path)
    log.info(f"SHA‑256 checksum for {out_path.name}: {checksum}")

    # Load existing checksums, update, and save.
    checksums_path: Path = paths.data("checksums.json")
    checksums = load_checksums(checksums_path)
    checksums[out_path.name] = checksum
    save_checksums(checksums_path, checksums)

    log.info("download_devign completed successfully.")


if __name__ == "__main__":
    # Allow the script to be run directly for debugging.
    main()
