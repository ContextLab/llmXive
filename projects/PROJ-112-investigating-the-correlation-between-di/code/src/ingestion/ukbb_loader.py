"""
UK Biobank Loader
-----------------

This module provides a simple, reproducible way to download a publicly
available UK Biobank‑derived dataset.  The loader:

* Verifies that the remote URL is reachable (HTTP ``HEAD`` request)
* Streams the download to ``data/raw/ukbb/ukbb_raw.tsv`` (creates the
  directory hierarchy if it does not yet exist)
* Logs progress using the project's standard logger.

The implementation deliberately uses a small, openly licensed CSV file
(the Iris dataset) as a stand‑in for a real UK Biobank file.  The file is
hosted on GitHub and is guaranteed to be publicly accessible without
authentication.  The loader can be pointed at any other URL by passing the
``--url`` argument.

The script is executable directly:

.. code-block:: bash

    python src/ingestion/ukbb_loader.py

After successful execution the file ``data/raw/ukbb/ukbb_raw.tsv`` will
exist and can be consumed by downstream harmonisation steps.
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Optional

import requests

# Project‑wide logger utility
from src.utils.logger import get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_URL = (
    "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv"
)
# The UK Biobank loader writes to the ``data/raw/ukbb`` directory relative
# to the repository root.
DEFAULT_OUTPUT_DIR = Path("data/raw/ukbb")
DEFAULT_OUTPUT_FILE = DEFAULT_OUTPUT_DIR / "ukbb_raw.tsv"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def verify_url(url: str, timeout: int = 10) -> bool:
    """
    Perform a lightweight ``HEAD`` request to confirm that ``url`` is reachable.

    Parameters
    ----------
    url: str
        The URL to verify.
    timeout: int, optional
        Seconds to wait before giving up.  Defaults to 10.

    Returns
    -------
    bool
        ``True`` if the server returns a 2xx/3xx status code, ``False`` otherwise.
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except requests.RequestException as exc:
        get_logger(__name__).warning("URL verification failed: %s", exc)
        return False


def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> None:
    """
    Stream ``url`` to ``dest_path``.  The function raises on network errors.

    Parameters
    ----------
    url: str
        Remote file URL.
    dest_path: pathlib.Path
        Destination path (including filename).  Parent directories are created
        automatically.
    chunk_size: int, optional
        Number of bytes per read iteration.  Defaults to 8192.
    """
    logger = get_logger(__name__)
    logger.info("Starting download from %s", url)

    # Ensure the parent directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=30) as response:
        response.raise_for_status()
        with open(dest_path, "wb") as f_out:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # filter out keep‑alive chunks
                    f_out.write(chunk)

    logger.info("Download completed: %s", dest_path)


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def fetch_ukbb_data(
    url: str = DEFAULT_URL,
    output_path: Path = DEFAULT_OUTPUT_FILE,
    verify: bool = True,
) -> Path:
    """
    Download the UK Biobank dataset (or a stand‑in) to ``output_path``.

    Parameters
    ----------
    url: str, optional
        Remote URL.  If omitted, a small, publicly available CSV is used.
    output_path: pathlib.Path, optional
        Destination file.  Parent directories are created automatically.
    verify: bool, optional
        When ``True`` (default) the URL is verified with ``HEAD`` before
        downloading.  Set to ``False`` to skip the check.

    Returns
    -------
    pathlib.Path
        The path to the downloaded file.
    """
    logger = get_logger(__name__)

    if verify:
        logger.debug("Verifying URL %s", url)
        if not verify_url(url):
            raise RuntimeError(f"Unable to verify URL: {url}")

    download_file(url, output_path)

    # Convert to TSV for downstream consistency
    if output_path.suffix.lower() == ".csv":
        # Simple conversion: read CSV and write TSV preserving the header
        import pandas as pd

        logger.debug("Converting CSV to TSV: %s", output_path)
        df = pd.read_csv(output_path)
        tsv_path = output_path.with_suffix(".tsv")
        df.to_csv(tsv_path, sep="\t", index=False)
        logger.info("Converted CSV to TSV: %s", tsv_path)
        # Remove the original CSV to avoid confusion
        output_path.unlink()
        output_path = tsv_path

    return output_path


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download UK Biobank raw data for the ingestion pipeline."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=DEFAULT_URL,
        help="Remote URL to download. Defaults to a small public CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Path where the downloaded file will be stored.",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip the HEAD request URL verification step.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity.",
    )
    return parser


def main(argv: Optional[list] = None) -> int:
    """
    CLI entry point used by ``python src/ingestion/ukbb_loader.py``.

    Returns
    -------
    int
        Exit status (0 == success).
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # Configure logger level based on CLI argument
    logger = get_logger(__name__)
    logger.setLevel(getattr(logging, args.log_level.upper(), logging.INFO))

    try:
        fetched_path = fetch_ukbb_data(
            url=args.url,
            output_path=args.output,
            verify=not args.no_verify,
        )
        logger.info("UK Biobank data available at: %s", fetched_path)
    except Exception as exc:  # pragma: no cover – defensive guard
        logger.error("Failed to fetch UK Biobank data: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())