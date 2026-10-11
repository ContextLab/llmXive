"""
Download QM9 dataset subset and record its checksum.

This script implements Task T004: it streams the QM9 dataset (via the
HuggingFace `datasets` library) to a Parquet file located at
`data/raw/qm9_subset.parquet`. After the file is written, the script
computes its SHA‑256 hash and records an entry in
`data/raw/checksums.json` following the project's checksum schema.

Usage
-----
python code/data/download.py --dataset qm9 --output data/raw

The script is CPU‑only and makes no attempt to fabricate data; any failure
in downloading the real dataset raises an exception so that the pipeline
fails loudly as required.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd
from datasets import load_dataset

# llmxive toolkit provides convenient path helpers that also ensure
# directories exist.
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def update_checksums_json(parquet_path: Path, checksum: str) -> None:
    """
    Record the checksum of the QM9 subset in ``data/raw/checksums.json``.

    The project's checksum schema (see ``data/raw/checksums_schema.yaml``)
    expects a mapping from a logical name to an object containing at least
    the hash, file name and path.  We use the logical name ``qm9_subset``.
    """
    checksums_path = Path(__file__).resolve().parents[3] / "data" / "raw" / "checksums.json"
    # Ensure the parent directory exists (it should, but be defensive)
    checksums_path.parent.mkdir(parents=True, exist_ok=True)

    if checksums_path.is_file():
        try:
            with checksums_path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
        except json.JSONDecodeError:
            log.warning("Existing checksums.json is malformed – starting fresh.")
            manifest = {}
    else:
        manifest = {}

    # Populate entry – follow the structure used elsewhere in the repo
    entry = {
        "hash": checksum,
        "file": parquet_path.name,
        "path": str(parquet_path)
    }
    manifest["qm9_subset"] = entry

    with checksums_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    log.info(f"Checksum entry written to {checksums_path}")

def download_qm9_subset(output_dir: Path, subset_size: int = 100_000) -> Path:
    """
    Stream the QM9 dataset, select ``subset_size`` molecules, and write
    a Parquet file.

    Parameters
    ----------
    output_dir: Path
        Directory where ``qm9_subset.parquet`` will be saved.
    subset_size: int
        Number of molecules to retain. The full QM9 set contains ~130k;
        100k provides the requested “≈100 k” subset.

    Returns
    -------
    Path to the created Parquet file.
    """
    log.info("Loading QM9 dataset from HuggingFace...")
    # The HuggingFace QM9 dataset mirrors the original data and includes a
    # ``smiles`` column needed downstream.
    dataset = load_dataset("qm9", split="train", streaming=False)

    # Verify the expected column exists
    if "smiles" not in dataset.column_names:
        raise RuntimeError("QM9 dataset does not contain a 'smiles' column.")

    # Convert to pandas, selecting only the required number of rows.
    # The dataset comfortably fits into memory on the CI runner.
    df = pd.DataFrame(dataset[:subset_size])

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / "qm9_subset.parquet"
    log.info(f"Writing {len(df)} records to {parquet_path}")
    df.to_parquet(parquet_path, index=False)

    return parquet_path

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download QM9 subset and record its SHA‑256 checksum."
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Name of the dataset to download (currently only 'qm9' is supported).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Directory where the raw files will be stored (e.g., data/raw).",
    )
    args = parser.parse_args()

    if args.dataset.lower() != "qm9":
        log.error("Only the 'qm9' dataset is supported by this script.")
        sys.exit(1)

    # Resolve the output directory using pathlib for safety.
    raw_dir = Path(args.output).resolve()
    if not raw_dir.is_dir():
        log.info(f"Creating output directory: {raw_dir}")
        raw_dir.mkdir(parents=True, exist_ok=True)

    try:
        parquet_path = download_qm9_subset(raw_dir)
    except Exception as exc:
        log.exception(f"Failed to download or write QM9 subset: {exc}")
        sys.exit(1)

    try:
        checksum = calculate_sha256(parquet_path)
        log.info(f"SHA‑256 for {parquet_path.name}: {checksum}")
    except Exception as exc:
        log.exception(f"Failed to compute checksum: {exc}")
        sys.exit(1)

    try:
        update_checksums_json(parquet_path, checksum)
    except Exception as exc:
        log.exception(f"Failed to update checksums.json: {exc}")
        sys.exit(1)

    log.info("QM9 subset download and checksum recording completed successfully.")
    # Exit with status 0 so the run‑book sees success.
    sys.exit(0)

if __name__ == "__main__":
    main()