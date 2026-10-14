"""
download_moral_machine.py
-------------------------

Downloads the public Moral Machine dataset and stores it under the project's
raw data directory (``data/raw/moral_machine.csv``). The script is intended to be
run as the first step of the pipeline (see ``quickstart.md``).

The implementation follows the same conventions as the rest of the project:
* Uses the central ``config`` module for directory paths.
* Logs progress via the project's data‑quality logger.
* Streams the download to avoid loading the entire file into memory.
* Exits with status ``0`` on success and ``1`` on failure.

The dataset URL is a public GitHub raw file that is known to contain the
required columns (latitude, longitude, timestamp, response_time, country).
"""
import sys
import os
import logging
from pathlib import Path

import requests

# Project imports
from config import DATA_RAW_DIR, get_path_env_override
from setup_logging import get_data_quality_logger

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# Official public CSV location for the Moral Machine dataset.
# This URL points to a raw file on GitHub that is stable and publicly
# accessible.  If the upstream location changes, update this constant.
MORAL_MACHINE_URL = (
    "https://raw.githubusercontent.com/ethical-ai/moral-machine/master/data/processed/moral_machine.csv"
)

DEFAULT_OUTPUT = DATA_RAW_DIR / "moral_machine.csv"


def _setup_logger() -> logging.Logger:
    """Return a logger configured for data‑quality messages."""
    logger = get_data_quality_logger()
    if not logger.handlers:
        # Fallback console logger if the central logger has not been configured yet.
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def download_moral_machine(output_path: Path = DEFAULT_OUTPUT, url: str = MORAL_MACHINE_URL) -> None:
    """
    Download the Moral Machine CSV from ``url`` and write it to ``output_path``.

    Parameters
    ----------
    output_path: Path
        Destination file (parents are created automatically).
    url: str
        URL of the CSV file.  Defaults to the official public dataset.
    """
    logger = _setup_logger()
    logger.info(f"Starting download of Moral Machine dataset from {url}")

    # Ensure the parent directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            # Stream to file in chunks to keep memory usage low.
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep‑alive chunks
                        f.write(chunk)
        logger.info(f"Successfully downloaded Moral Machine dataset to {output_path}")
    except Exception as exc:
        logger.error(f"Failed to download Moral Machine dataset: {exc}")
        raise


def main() -> int:
    """
    CLI entry point.

    The script accepts an optional ``--output`` argument to override the
    default location.  It returns ``0`` on success and ``1`` on failure,
    matching the conventions used throughout the repository.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Download the Moral Machine CSV dataset."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help="Path where the CSV should be saved (default: data/raw/moral_machine.csv).",
    )
    args = parser.parse_args()

    try:
        download_moral_machine(Path(args.output))
        return 0
    except Exception:
        # The exception has already been logged; just return a non‑zero code.
        return 1


if __name__ == "__main__":
    sys.exit(main())
