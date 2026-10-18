"""
download_ctu13.py
------------------

Downloads a subset of the CTU‑13 Scenario 1 NetFlow records using the
HuggingFace ``datasets`` library, writes it to ``data/raw/ctu13_scenario1.csv``,
creates a SHA‑256 checksum side‑car, and updates ``code/config.yaml`` with the
active dataset name.

The script streams the dataset to avoid loading the entire collection into
memory and writes only the first ``MAX_ROWS`` records (a configurable limit)
to keep runtime and storage modest while still using real data.
"""

import csv
import hashlib
import sys
from pathlib import Path

import yaml
from datasets import load_dataset
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
# HuggingFace dataset identifier for the CTU‑13 NetFlow records.
HF_DATASET = "ctu13/ctu13"
# Number of rows to write – enough for a non‑empty file while staying fast.
MAX_ROWS = 5_000

TARGET_DIR = paths.data("raw")
TARGET_CSV = TARGET_DIR / "ctu13_scenario1.csv"
CHECKSUM_FILE = TARGET_CSV.with_suffix(TARGET_CSV.suffix + ".sha256")
CONFIG_FILE = paths.code("config.yaml")

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def write_checksum(file_path: Path, checksum: str) -> None:
    """Write *checksum* to a ``.sha256`` side‑car next to *file_path*."""
    checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")
    checksum_path.write_text(f"{checksum}  {file_path.name}\n")
    log.info("Wrote checksum to %s", checksum_path)

def update_config(active_dataset: str) -> None:
    """Set ``active_dataset`` in ``code/config.yaml`` (creates file if missing)."""
    config_path = CONFIG_FILE
    if config_path.exists():
        with config_path.open("r") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}

    cfg["active_dataset"] = active_dataset

    # Ensure the parent directory exists (paths.code does this)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    log.info(
        "Updated config %s with active_dataset=%s", config_path, active_dataset
    )

# --------------------------------------------------------------------------- #
# Main download routine
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Streams the CTU‑13 NetFlow dataset from HuggingFace and writes the first
    ``MAX_ROWS`` records to ``data/raw/ctu13_scenario1.csv``.
    """
    log.info(
        "Streaming CTU‑13 dataset from HuggingFace (%s) – will write up to %d rows",
        HF_DATASET,
        MAX_ROWS,
    )

    # Ensure target directory exists.
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # Load the dataset in streaming mode to avoid full download.
    try:
        ds = load_dataset(HF_DATASET, split="train", streaming=True)
    except Exception as exc:
        raise RuntimeError(f"Failed to load HuggingFace dataset {HF_DATASET}: {exc}") from exc

    # Determine column order from the first example.
    try:
        first_example = next(iter(ds))
    except StopIteration:
        raise RuntimeError(f"The dataset {HF_DATASET} is empty.") from None
    fieldnames = list(first_example.keys())

    # Write CSV header and rows.
    rows_written = 0
    with TARGET_CSV.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        # Write the first example we already fetched.
        writer.writerow(first_example)
        rows_written += 1

        for example in ds:
            if rows_written >= MAX_ROWS:
                break
            writer.writerow(example)
            rows_written += 1

    log.info("Wrote %d rows to %s", rows_written, TARGET_CSV)

    # Compute and write checksum.
    try:
        checksum = compute_sha256(TARGET_CSV)
        write_checksum(TARGET_CSV, checksum)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to compute/write checksum for {TARGET_CSV}: {exc}"
        ) from exc

    # Update the project configuration.
    try:
        update_config(active_dataset="ctu13_scenario1")
    except Exception as exc:
        raise RuntimeError(
            f"Failed to update config file {CONFIG_FILE}: {exc}"
        ) from exc

    log.info(
        "CTU‑13 Scenario 1 download and registration completed successfully."
    )

# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("Fatal error: %s", e)
        sys.exit(1)
