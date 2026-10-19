"""
download_ctu13.py
------------------

Downloads a subset of the CTU‑13 Scenario 1 NetFlow records using the
Hugging Face `datasets` library, writes it to ``data/raw/ctu13_scenario1.csv``,
creates a SHA‑256 checksum side‑car, and updates ``code/config.yaml``.

This implementation replaces the previous GitHub CSV download which returned 404.
"""

import csv
import hashlib
import sys
from pathlib import Path

import yaml
from datasets import load_dataset
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# Number of data rows to write to keep runtime and storage modest.
MAX_ROWS = 5_000

TARGET_DIR = paths.data("raw")
TARGET_CSV = TARGET_DIR / "ctu13_scenario1.csv"
CONFIG_FILE = paths.code("config.yaml")

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
    """Set ``active_dataset`` in ``code/config.yaml``."""
    config_path = CONFIG_FILE
    if config_path.exists():
        with config_path.open("r") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}

    cfg["active_dataset"] = active_dataset
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    log.info("Updated config %s with active_dataset=%s", config_path, active_dataset)

def main() -> None:
    """
    Fetches CTU-13 data via Hugging Face and writes a subset to CSV.
    """
    log.info("Fetching CTU-13 dataset via Hugging Face (up to %d rows)", MAX_ROWS)

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Streaming load to avoid memory overflow
        ds = load_dataset("ctu13/ctu13", split="train", streaming=True)
        iterator = iter(ds)
        
        # Get first row to extract header
        first_row = next(iterator)
        header = list(first_row.keys())

        with TARGET_CSV.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()
            writer.writerow(first_row)
            
            rows_written = 1
            for row in iterator:
                if rows_written >= MAX_ROWS:
                    break
                writer.writerow(row)
                rows_written += 1

        log.info("Wrote %d rows to %s", rows_written, TARGET_CSV)
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch CTU-13 data from Hugging Face: {exc}") from exc

    # Compute and write checksum.
    try:
        checksum = compute_sha256(TARGET_CSV)
        write_checksum(TARGET_CSV, checksum)
    except Exception as exc:
        raise RuntimeError(f"Failed to compute/write checksum for {TARGET_CSV}: {exc}") from exc

    # Update the project configuration.
    try:
        update_config(active_dataset="ctu13_scenario1")
    except Exception as exc:
        raise RuntimeError(f"Failed to update config file {CONFIG_FILE}: {exc}") from exc

    log.info("CTU-13 Scenario 1 download and registration completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("Fatal error: %s", e)
        sys.exit(1)
