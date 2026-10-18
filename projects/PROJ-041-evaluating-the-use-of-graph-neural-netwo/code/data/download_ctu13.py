"""
download_ctu13.py
------------------

Downloads a subset of the CTU‑13 Scenario 1 NetFlow records from the
official GitHub repository, writes it to ``data/raw/ctu13_scenario1.csv``,
creates a SHA‑256 checksum side‑car, and updates ``code/config.yaml`` with
the active dataset name.

The script streams the CSV directly from GitHub to avoid loading the entire
file into memory and writes only the first ``MAX_ROWS`` data rows (the
header is always written) to keep runtime and storage modest while still
using real data.
"""

import csv
import hashlib
import sys
from pathlib import Path

import requests
import yaml
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
# Direct URL to the raw CSV for Scenario 1 in the CTU‑13 dataset.
CSV_URL = (
    "https://raw.githubusercontent.com/CTU-AI-Lab/CTU-13-Dataset/master/"
    "Scenario1/CTU-13-Dataset-1.csv"
)
# Number of data rows (excluding the header) to write – enough for a
# non‑empty file while staying fast.
MAX_ROWS = 5_000

TARGET_DIR = paths.data("raw")
TARGET_CSV = TARGET_DIR / "ctu13_scenario1.csv"
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
    Streams the CTU‑13 Scenario 1 CSV from GitHub and writes the first
    ``MAX_ROWS`` data rows to ``data/raw/ctu13_scenario1.csv``.
    """
    log.info(
        "Downloading CTU‑13 Scenario 1 CSV from %s (up to %d rows)",
        CSV_URL,
        MAX_ROWS,
    )

    # Ensure the target directory exists.
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # Stream the CSV file.
    try:
        response = requests.get(CSV_URL, stream=True, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"Failed to download CTU‑13 CSV: {exc}") from exc

    line_iterator = response.iter_lines(decode_unicode=True)

    try:
        header_line = next(line_iterator)
    except StopIteration:
        raise RuntimeError("Downloaded CSV is empty.") from None

    header = next(csv.reader([header_line]))

    rows_written = 0
    with TARGET_CSV.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)  # always write the header

        for line in line_iterator:
            if rows_written >= MAX_ROWS:
                break
            # ``line`` is a raw CSV line; parse it safely with ``csv.reader``.
            row = next(csv.reader([line]))
            writer.writerow(row)
            rows_written += 1

    log.info("Wrote %d data rows to %s", rows_written, TARGET_CSV)

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
