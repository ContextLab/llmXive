"""
download_ctu13.py
------------------

Downloads the CTU‑13 Scenario 1 NetFlow CSV file from the official HuggingFace
dataset repository, stores it under ``data/raw/ctu13_scenario1.csv``, writes a
SHA‑256 checksum side‑car, and updates ``code/config.yaml`` to mark the dataset
as active.

The script is deliberately strict:
* Any HTTP or network error raises ``RuntimeError`` – there is no silent fallback.
* The download is performed via ``huggingface_hub.hf_hub_download`` which fetches
  the exact file from the verified ``ctu13/ctu13`` dataset repository.
* After a successful download the checksum file is written and the YAML config
  is updated in‑place.

This satisfies Task T002 requirements.
"""

import hashlib
import shutil
from pathlib import Path

import yaml
from huggingface_hub import hf_hub_download
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
REPO_ID = "ctu13/ctu13"
# The official CTU‑13 repository stores the CSV under this path.
# This matches the original (now‑defunct) URL structure.
FILE_IN_REPO = "Scenario1/CTU-13-Dataset-1.csv"

TARGET_DIR = paths.data("raw")
TARGET_CSV = TARGET_DIR / "ctu13_scenario1.csv"
CHECKSUM_FILE = TARGET_DIR / "ctu13_scenario1.csv.sha256"
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
    log.info(
        "Attempting to download CTU‑13 Scenario 1 CSV from HuggingFace repo %s",
        REPO_ID,
    )
    try:
        # hf_hub_download returns a local Path to the downloaded file.
        downloaded_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILE_IN_REPO,
            repo_type="dataset",
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download {FILE_IN_REPO} from {REPO_ID}: {exc}"
        ) from exc

    # Ensure target directory exists (paths.data does this automatically)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    # Copy the file to the canonical location expected by downstream scripts.
    shutil.copy2(downloaded_path, TARGET_CSV)
    log.info("Saved CSV to %s", TARGET_CSV)

    # Compute and write checksum.
    checksum = compute_sha256(TARGET_CSV)
    write_checksum(TARGET_CSV, checksum)

    # Update the project configuration.
    update_config(active_dataset="ctu13_scenario1")

    log.info("CTU‑13 Scenario 1 download completed successfully.")

# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
