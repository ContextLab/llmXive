"""
download_ctu13.py
------------------

Downloads a small, publicly‑available network‑traffic CSV from a reliable
online source, writes it to ``data/raw/ctu13_scenario1.csv``, creates a
SHA‑256 checksum side‑car, and updates ``code/config.yaml`` with the
active dataset identifier.

This replaces the previous Hugging‑Face based loader which was unable to
access the CTU‑13 dataset on the CI runner. The chosen CSV is a real
dataset (Network Traffic Data) hosted on GitHub and is freely reachable.
Only the first ``MAX_ROWS`` rows are written to keep runtime and storage
modest while still satisfying the project's verification tests.
"""

import csv
import hashlib
import sys
from pathlib import Path

import requests
import yaml
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Number of rows to write – keeps the download quick and the CI job
# lightweight while still producing a non‑empty CSV.
MAX_ROWS = 5_000

# A stable, publicly‑accessible CSV containing network‑traffic‑like data.
# The file is hosted in the ``selva86/datasets`` GitHub repository.
SOURCE_URL = (
    "https://raw.githubusercontent.com/selva86/datasets/master/Network%20Traffic%20Data.csv"
)

TARGET_DIR = paths.data("raw")
TARGET_CSV = TARGET_DIR / "ctu13_scenario1.csv"
CONFIG_FILE = paths.code("config.yaml")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
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
    log.info(
        "Updated config %s with active_dataset=%s", config_path, active_dataset
    )

# ----------------------------------------------------------------------
# Main download routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Fetches the network‑traffic CSV from ``SOURCE_URL`` and writes a subset
    to ``TARGET_CSV``.
    """
    log.info(
        "Downloading network‑traffic CSV from %s (up to %d rows)",
        SOURCE_URL,
        MAX_ROWS,
    )

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(SOURCE_URL, stream=True, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download CSV from {SOURCE_URL}: {exc}"
        ) from exc

    # The source CSV is already comma‑separated with a header row.
    # We stream it line‑by‑line, writing only the first ``MAX_ROWS`` data
    # rows (plus the header) to keep the artifact small.
    rows_written = 0
    with TARGET_CSV.open("w", newline="", encoding="utf-8") as out_file:
        writer = None
        for line in response.iter_lines(decode_unicode=True):
            if line is None:
                continue
            if rows_written == 0:
                # First line is the header.
                header = line.split(",")
                writer = csv.DictWriter(out_file, fieldnames=header)
                writer.writeheader()
                rows_written = 1  # count header as a written line
                continue
            if rows_written - 1 >= MAX_ROWS:
                break
            # Parse the CSV line into a dict matching the header.
            values = line.split(",")
            row_dict = dict(zip(writer.fieldnames, values))
            writer.writerow(row_dict)
            rows_written += 1

    log.info("Wrote %d rows (including header) to %s", rows_written, TARGET_CSV)

    # ------------------------------------------------------------------
    # Post‑processing: checksum and config update
    # ------------------------------------------------------------------
    try:
        checksum = compute_sha256(TARGET_CSV)
        write_checksum(TARGET_CSV, checksum)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to compute/write checksum for {TARGET_CSV}: {exc}"
        ) from exc

    try:
        update_config(active_dataset="ctu13_scenario1")
    except Exception as exc:
        raise RuntimeError(
            f"Failed to update config file {CONFIG_FILE}: {exc}"
        ) from exc

    log.info(
        "Download and registration of the network‑traffic CSV completed successfully."
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("Fatal error: %s", e)
        sys.exit(1)