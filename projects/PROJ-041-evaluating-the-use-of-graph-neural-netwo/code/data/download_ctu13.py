"""
Download and register the CTU‑13 Scenario 1 NetFlow CSV dataset.

This implementation uses the HuggingFace ``datasets`` library as the
authoritative source for the CSV conversion of the CTU‑13 traffic
records.  The dataset identifier ``ctu13`` (and configuration
``scenario1``) is known to exist as of 2026‑10‑15.  If the download ever
fails, the script aborts – no fallback is permitted, matching the
specification for Task T002.
"""

import hashlib
import logging
import os
import sys
import yaml

from llmxive_toolkit import paths, get_logger
from datasets import load_dataset

log = get_logger(__name__)


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def calculate_sha256(file_path: str) -> str:
    """Calculate the SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    checksum = sha256.hexdigest()
    log.debug(f"Calculated SHA‑256 for {file_path}: {checksum}")
    return checksum


def validate_file(file_path: str, expected_hash: str | None = None) -> bool:
    """
    Validate that a file exists and optionally that its SHA‑256 matches an
    expected value.
    """
    if not os.path.isfile(file_path):
        raise RuntimeError(f"Expected file does not exist: {file_path}")

    if expected_hash is not None:
        actual_hash = calculate_sha256(file_path)
        if actual_hash.lower() != expected_hash.lower():
            raise RuntimeError(
                f"Checksum mismatch for {file_path}: expected {expected_hash}, got {actual_hash}"
            )
        log.debug(f"Checksum verified for {file_path}")
    else:
        log.debug(f"File existence verified (no checksum) for {file_path}")
    return True


def trigger_fallback():
    """
    No fallback is allowed for this task. Invoking this function always
    raises an error, halting the pipeline.
    """
    raise RuntimeError(
        "CTU‑13 download failed and no fallback is permitted for Task T002."
    )


# ----------------------------------------------------------------------
# Core download logic
# ----------------------------------------------------------------------
def download_ctu13_dataset() -> str:
    """
    Download the CTU‑13 Scenario 1 NetFlow CSV using the HuggingFace
    ``datasets`` library and write it to the canonical data location.

    Returns
    -------
    str
        Path to the downloaded CSV file.

    Raises
    ------
    RuntimeError
        If the download cannot be completed.
    """
    # The HuggingFace dataset provides the CSV directly.
    try:
        ds = load_dataset("ctu13", "scenario1", split="train")
    except Exception as e:
        log.error(f"Failed to load CTU‑13 from HuggingFace: {e}")
        trigger_fallback()

    output_path = paths.data("raw", "ctu13_scenario1.csv")
    # Ensure target directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write the dataset to CSV (preserve column order)
    df = ds.to_pandas()
    df.to_csv(output_path, index=False)
    log.info(f"CTU‑13 Scenario 1 CSV written to {output_path}")
    return str(output_path)


# ----------------------------------------------------------------------
# Config handling
# ----------------------------------------------------------------------
def update_config_with_active_dataset(dataset_name: str = "ctu13") -> None:
    """
    Load ``code/config.yaml``, set ``active_dataset`` to the provided value,
    and write the file back.
    """
    config_path = paths.code("config.yaml")
    if not config_path.is_file():
        raise RuntimeError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f) or {}

    config_data["active_dataset"] = dataset_name

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_data, f, sort_keys=False)

    log.info(f"Updated config.yaml with active_dataset: {dataset_name}")


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the full download‑register workflow for CTU‑13 Scenario 1.
    """
    # Step 1: download the CSV
    csv_path = download_ctu13_dataset()

    # Step 2: compute checksum and write side‑car
    checksum = calculate_sha256(csv_path)
    checksum_path = f"{csv_path}.sha256"
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {os.path.basename(csv_path)}\\n")
    log.info(f"Wrote checksum to {checksum_path}")

    # Step 3: validate the downloaded file against its own checksum
    validate_file(csv_path, expected_hash=checksum)

    # Step 4: update configuration
    update_config_with_active_dataset("ctu13")

    log.info("CTU‑13 dataset download and registration completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(f"Task T002 failed: {exc}")
        sys.exit(1)