"""
download_ctu13.py
------------------

Downloads the CTU‑13 Scenario 1 NetFlow CSV from a verified public URL,
writes it to ``data/raw/ctu13_scenario1.csv``, creates a SHA‑256 checksum
side‑car, and updates ``code/config.yaml`` with the active dataset name.
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
# Verified public URL for the CTU‑13 Scenario 1 CSV.
# The repository uses the default ``main`` branch; using ``master`` results in 404.
CSV_URL = (
    "https://raw.githubusercontent.com/CTU-AI-Lab/CTU-13-Dataset/main/"
    "Scenario1/CTU-13-Dataset-1.csv"
)

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
    Downloads the CTU‑13 Scenario 1 CSV from the public GitHub URL
    and writes it to ``data/raw/ctu13_scenario1.csv``.
    """
    log.info("Attempting to download CTU‑13 Scenario 1 CSV from %s", CSV_URL)

    # Ensure target directory exists.
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with requests.get(CSV_URL, stream=True, timeout=60) as r:
            r.raise_for_status()
            # Stream directly to file to avoid loading whole CSV into memory.
            with TARGET_CSV.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive chunks
                        f.write(chunk)
    except Exception as exc:
        raise RuntimeError(f"Failed to download CSV from {CSV_URL}: {exc}") from exc

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
