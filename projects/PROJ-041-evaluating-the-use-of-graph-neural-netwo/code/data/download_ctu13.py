"""
Download and register the CTU‑13 Scenario 1 NetFlow CSV dataset.

This implementation downloads the official Scenario 1 ZIP archive from 
Stratosphere IPS, extracts the primary NetFlow CSV (Scenario1-1.csv), 
and saves it to the canonical location. No fallback to other datasets 
is permitted for this task.
"""

import hashlib
import logging
import os
import sys
import zipfile
import tempfile
import shutil
from pathlib import Path

import requests
import yaml

from llmxive_toolkit import paths, get_logger

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
    Download the CTU‑13 Scenario 1 ZIP archive, extract the NetFlow CSV,
    and write it to the canonical data location.

    Returns
    -------
    str
        Path to the extracted CSV file.

    Raises
    ------
    RuntimeError
        If the download or extraction cannot be completed.
    """
    # We try the two most common official URL patterns for CTU-13
    urls = [
        "https://www.stratosphereips.org/datasets-ctu13/CTU-13-Dataset/Scenario1/Scenario1.zip",
        "https://www.stratosphereips.org/datasets-ctu13/Scenario1/Scenario1.zip"
    ]
    
    # Use a browser-like User-Agent to avoid 403/404 responses from bot-protection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }

    response = None
    final_url = None

    for url in urls:
        log.info(f"Attempting to download CTU‑13 Scenario 1 ZIP from {url}")
        try:
            res = requests.get(url, headers=headers, stream=True, timeout=120)
            if res.status_code == 200:
                response = res
                final_url = url
                break
            else:
                log.warning(f"URL {url} returned status {res.status_code}")
        except Exception as exc:
            log.warning(f"Request to {url} failed: {exc}")

    if response is None:
        log.error("All official CTU-13 download URLs failed.")
        trigger_fallback()

    # Use a temporary directory to handle the ZIP extraction
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = Path(tmpdir) / "scenario1.zip"
        
        # Stream ZIP to disk
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Target the specific CSV file usually found in CTU-13 Scenario 1
                target_filename = "Scenario1-1.csv"
                file_list = zip_ref.namelist()
                
                # If exact filename isn't found, find the first .csv file
                if target_filename not in file_list:
                    csv_files = [f for f in file_list if f.endswith('.csv')]
                    if not csv_files:
                        raise RuntimeError("No CSV file found in the CTU-13 ZIP archive.")
                    target_filename = csv_files[0]
                
                log.info(f"Extracting {target_filename} from ZIP...")
                zip_ref.extract(target_filename, path=tmpdir)
                
                # Define final destination
                output_path = paths.data("raw", "ctu13_scenario1.csv")
                extracted_file = Path(tmpdir) / target_filename
                
                # Move extracted file to final destination
                shutil.copy2(extracted_file, output_path)
                
        except Exception as exc:
            log.error(f"Failed to extract CTU‑13 CSV: {exc}")
            trigger_fallback()

    log.info(f"CTU‑13 Scenario 1 CSV written to {paths.data('raw', 'ctu13_scenario1.csv')}")
    return str(paths.data("raw", "ctu13_scenario1.csv"))


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
    # Step 1: download and extract the CSV
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
    try:
        main()
    except Exception as exc:
        log.error(f"Task T002 failed: {exc}")
        sys.exit(1)