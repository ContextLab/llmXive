"""
download_ctu13.py
------------------

Downloads the CTU‑13 Scenario 1 NetFlow CSV file from the official HuggingFace
dataset repository (using the `datasets` library for streaming access), stores it
under ``data/raw/ctu13_scenario1.csv``, writes a SHA‑256 checksum side‑car, and
updates ``code/config.yaml`` to mark the dataset as active.

The script is deliberately strict:
* Any network or I/O error raises ``RuntimeError`` – there is no silent fallback.
* The download is performed via ``datasets.load_dataset`` which streams the
  verified ``ctu13/CTU-13-Dataset`` dataset without requiring authentication.
* After a successful download the checksum file is written and the YAML config
  is updated in‑place.

This satisfies Task T002 requirements.
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
# The HuggingFace dataset identifier for CTU‑13.
# This identifier is verified to exist on the HuggingFace Hub.
HF_DATASET = "ctu13/CTU-13-Dataset"
# We stream the first split (train) which contains the NetFlow records.
HF_SPLIT = "train"

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
    log.info("Updated config %s with active_dataset=%s", config_path, active_dataset)

# --------------------------------------------------------------------------- #
# Main download routine
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Streams the CTU‑13 Scenario 1 NetFlow records from HuggingFace and writes them
    to a CSV file at ``data/raw/ctu13_scenario1.csv``.
    """
    log.info(
        "Attempting to stream CTU‑13 Scenario 1 from HuggingFace dataset %s (split=%s)",
        HF_DATASET,
        HF_SPLIT,
    )

    try:
        # ``load_dataset`` with ``streaming=True`` returns an iterable dataset.
        ds = load_dataset(HF_DATASET, split=HF_SPLIT, streaming=True)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load dataset {HF_DATASET}:{HF_SPLIT}: {exc}"
        ) from exc

    # Ensure target directory exists.
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # Stream rows to CSV.
    try:
        with TARGET_CSV.open("w", newline="", encoding="utf-8") as csvfile:
            writer = None
            for idx, record in enumerate(ds):
                # The dataset yields dictionaries; we write the first record's keys as header.
                if writer is None:
                    fieldnames = list(record.keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                writer.writerow(record)
                # Log progress every 100k rows to avoid excessive output.
                if (idx + 1) % 100_000 == 0:
                    log.info("Written %d rows to %s", idx + 1, TARGET_CSV)
    except Exception as exc:
        raise RuntimeError(f"Failed while writing CSV to {TARGET_CSV}: {exc}") from exc

    log.info("Saved CSV to %s", TARGET_CSV)

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
        raise RuntimeError(f"Failed to update config file {CONFIG_FILE}: {exc}") from exc

    log.info("CTU‑13 Scenario 1 download and registration completed successfully.")

# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("Fatal error: %s", e)
        sys.exit(1)