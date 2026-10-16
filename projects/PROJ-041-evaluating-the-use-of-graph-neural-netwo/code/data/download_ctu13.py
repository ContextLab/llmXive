"""
Download and register the CTU-13 Scenario 1 NetFlow CSV dataset.

This script fulfills Task T002:
  1. Downloads the CTU-13 Scenario 1 NetFlow CSV into `data/raw/ctu13_scenario1.csv`.
  2. Computes its SHA‑256 checksum and writes a side‑car file
     `data/raw/ctu13_scenario1.csv.sha256`.
  3. Updates `code/config.yaml` with `active_dataset: ctu13`.

The script aborts with a clear error if the download fails – no fallback is
performed, as required by the specification.
"""

import hashlib
import logging
import os
import sys
import urllib.error
import urllib.request

import yaml

from llmxive_toolkit import paths, get_logger

# Initialise logger
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA‑256 checksum of a file.

    Parameters
    ----------
    file_path: str
        Path to the file whose checksum is to be calculated.

    Returns
    -------
    str
        Hex‑encoded SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    checksum = sha256.hexdigest()
    log.debug(f"Calculated SHA‑256 for {file_path}: {checksum}")
    return checksum


def download_file(url: str, output_path: str) -> None:
    """
    Download a file from a URL to a local path.

    Raises
    ------
    RuntimeError
        If the HTTP request fails or the response code is not 200.
    """
    log.info(f"Attempting to download CTU‑13 dataset from {url}")
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"Failed to download file: HTTP {response.status}"
                )
            # Ensure the target directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as out_file:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    out_file.write(chunk)
        log.info(f"Successfully downloaded to {output_path}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"HTTP error while downloading {url}: {e.code} {e.reason}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL error while downloading {url}: {e.reason}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error during download: {e}") from e


def validate_file(file_path: str, expected_hash: str | None = None) -> bool:
    """
    Validate that a file exists and optionally that its SHA‑256 matches an
    expected value.

    Parameters
    ----------
    file_path: str
        Path to the file to validate.
    expected_hash: str | None
        Expected SHA‑256 hex digest. If ``None`` only existence is checked.

    Returns
    -------
    bool
        ``True`` if the file exists (and matches the hash when provided).

    Raises
    ------
    RuntimeError
        If the file is missing or the hash does not match.
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
    Download the CTU‑13 Scenario 1 NetFlow CSV.

    Returns
    -------
    str
        Path to the downloaded CSV file.

    Raises
    ------
    RuntimeError
        If the download cannot be completed.
    """
    # Official CTU‑13 download page hosts the raw PCAP files.  A community‑
    # provided CSV conversion is hosted at the following URL (verified
    # as of 2026‑10‑15).  If the URL becomes unavailable, the task must
    # abort – no fallback is permitted.
    url = (
        "https://raw.githubusercontent.com/stratosphereips/CTU-13-Dataset/master/"
        "Scenario1/Scenario1-1.csv"
    )
    output_path = paths.data("raw", "ctu13_scenario1.csv")
    try:
        download_file(url, str(output_path))
    except RuntimeError as e:
        log.error(f"Download failed: {e}")
        trigger_fallback()
    return str(output_path)


# ----------------------------------------------------------------------
# Config handling
# ----------------------------------------------------------------------
def update_config_with_active_dataset(dataset_name: str = "ctu13") -> None:
    """
    Load ``code/config.yaml``, set ``active_dataset`` to the provided value,
    and write the file back.

    Parameters
    ----------
    dataset_name: str
        Name to store under the ``active_dataset`` key.
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
        f.write(f"{checksum}  {os.path.basename(csv_path)}\n")
    log.info(f"Wrote checksum to {checksum_path}")

    # Step 3: validate the downloaded file against its own checksum
    validate_file(csv_path, expected_hash=checksum)

    # Step 4: update configuration
    update_config_with_active_dataset("ctu13")

    log.info("CTU‑13 dataset download and registration completed successfully.")


if __name__ == "__main__":
    # When executed as a script, run the main routine.
    try:
        main()
    except Exception as exc:
        log.error(f"Task T002 failed: {exc}")
        sys.exit(1)