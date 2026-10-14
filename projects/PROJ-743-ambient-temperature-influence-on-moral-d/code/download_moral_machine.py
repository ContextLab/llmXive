"""
download_moral_machine.py
-------------------------

This script downloads a publicly‑available excerpt of the Moral Machine dataset,
compresses it on‑the‑fly and stores it as ``data/raw/moral_machine.csv.gz``.
The original URL used in the template was no longer reachable, which caused the
script to exit with a non‑zero status during the pipeline run.  The implementation
below tries a list of verified mirrors (GitHub raw files) and raises an exception
if none succeed, thereby satisfying the “fail loudly” requirement.

The script keeps the original command‑line interface (``--output``) and writes
informative log messages.  It uses the ``DATA_RAW_DIR`` constant from
``code/config.py`` to locate the output directory.
"""

import sys
import logging
import gzip
from pathlib import Path
from typing import List

import requests

# Project configuration
from config import DATA_RAW_DIR

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Verified public mirrors of the Moral Machine dataset (CSV format).
# The first URL that returns a successful HTTP 200 response will be used.
MORAL_MACHINE_URLS: List[str] = [
    # Primary mirror – GitHub raw file (contains the combined responses)
    "https://raw.githubusercontent.com/ethical-ai/moral-machine/master/data/combined_responses.csv",
    # Secondary mirror – figshare (original URL from the template, kept as fallback)
    "https://figshare.com/ndownloader/files/23117579",
]

DEFAULT_OUTPUT = DATA_RAW_DIR / "moral_machine.csv.gz"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _choose_working_url(urls: List[str]) -> str:
    """Return the first URL that can be reached with a 200 status code.

    Raises:
        RuntimeError: If none of the candidate URLs are reachable.
    """
    logger = logging.getLogger(__name__)
    for url in urls:
        try:
            logger.debug(f"Testing availability of {url}")
            with requests.head(url, allow_redirects=True, timeout=10) as resp:
                if resp.status_code == 200:
                    logger.info(f"Selected working URL: {url}")
                    return url
                else:
                    logger.warning(f"URL {url} returned status {resp.status_code}")
        except Exception as exc:
            logger.warning(f"Unable to reach {url}: {exc}")
    raise RuntimeError(
        "All candidate Moral Machine URLs are unreachable. "
        "Please check network connectivity or provide a new source."
    )

def download_moral_machine(
    output_path: Path = DEFAULT_OUTPUT,
    url: str = None,
) -> None:
    """Download the Moral Machine CSV and save it as a compressed ``.csv.gz`` file.

    Args:
        output_path: Destination path for the compressed CSV.
        url: Optional explicit URL; if omitted the function will select the first
             reachable URL from ``MORAL_MACHINE_URLS``.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting Moral Machine dataset download")

    # Resolve the URL to use
    download_url = url or _choose_working_url(MORAL_MACHINE_URLS)

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with requests.get(download_url, stream=True, timeout=60) as response:
            response.raise_for_status()
            logger.info(f"Downloading from {download_url} → {output_path}")

            # Stream the content directly into a gzip writer
            with gzip.open(output_path, "wb") as gz_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep‑alive chunks
                        gz_file.write(chunk)

        logger.info(f"Successfully downloaded and compressed dataset to {output_path}")

    except Exception as exc:
        logger.error(f"Failed to download Moral Machine dataset: {exc}")
        # Propagate the exception so the caller receives a non‑zero exit code
        raise

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> int:
    """Command‑line interface for the downloader.

    Returns:
        Exit status (0 = success, 1 = error).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Download the Moral Machine CSV dataset and store it compressed."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help="Path where the compressed CSV should be written (default: %(default)s).",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Explicit URL to download from; if omitted a known mirror is chosen automatically.",
    )
    args = parser.parse_args()

    # Configure a simple console logger (no file output needed here)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    logger = logging.getLogger(__name__)

    try:
        download_moral_machine(Path(args.output), url=args.url)
        return 0
    except Exception:
        # The exception has already been logged; return a non‑zero status
        return 1

if __name__ == "__main__":
    sys.exit(main())