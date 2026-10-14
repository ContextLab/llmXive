"""
download_moral_machine.py
-------------------------

Downloads the public Moral Machine dataset from the official GitHub repository
and stores it under ``data/raw/moral_machine.csv`` (uncompressed CSV).

The script is deliberately lightweight and uses only the standard library
plus ``requests`` (which is already available in the execution environment).

It creates any missing parent directories, writes the file, and logs a short
message to stdout.  No checksum verification is performed here – that is
handled later by ``validate_sources.py``.
"""
import sys
import os
import logging
from pathlib import Path

import requests

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Official Moral Machine dataset (processed shared responses) – a stable URL.
MORAL_MACHINE_URL = (
    "https://raw.githubusercontent.com/ethical-ai/moral-machine-data/"
    "master/processed/shared_responses.csv"
)
OUTPUT_REL_PATH = Path("data/raw/moral_machine.csv")

# ----------------------------------------------------------------------
# Logging helpers
# ----------------------------------------------------------------------
def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("download_moral_machine")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# ----------------------------------------------------------------------
# Main download routine
# ----------------------------------------------------------------------
def download_moral_machine(output_path: Path, url: str = MORAL_MACHINE_URL) -> None:
    """
    Download the Moral Machine CSV and write it to ``output_path``.

    Parameters
    ----------
    output_path: Path
        Destination file (parents are created automatically).
    url: str
        URL of the CSV file.  Defaults to the official public dataset.
    """
    logger = _setup_logger()
    logger.info(f"Starting download of Moral Machine dataset from {url}")

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        logger.error(f"Failed to download Moral Machine data: {exc}")
        raise

    # Write in chunks to avoid loading the whole file into memory
    try:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    except Exception as exc:
        logger.error(f"Error writing file {output_path}: {exc}")
        raise

    logger.info(f"Successfully saved Moral Machine data to {output_path}")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    CLI wrapper – returns exit code 0 on success, 1 on failure.
    """
    try:
        download_moral_machine(OUTPUT_REL_PATH)
        return 0
    except Exception:
        return 1

if __name__ == "__main__":
    sys.exit(main())
