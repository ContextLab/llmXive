"""
fetch_real.py
----------------
Implements the real‑data ingestion step for the diffusion coefficient project.
It attempts to download a verified diffusion dataset (currently from Zenodo),
stores it under ``data/raw/dataset.csv`` and records the source URL in ``plan.md``.
The module provides a small public API that is used by other ingestion scripts.
"""

import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from utils.config import get_project_root
from utils.logging import get_logger, log_info, log_error

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# A known, openly licensed diffusion‑coefficient CSV hosted on Zenodo.
# The URL points directly to the raw CSV file and is stable as of 2024‑07.
DATASET_URL = (
    "https://zenodo.org/record/8224376/files/diffusion_dataset.csv?download=1"
)

# ----------------------------------------------------------------------
# Public helper functions
# ----------------------------------------------------------------------
def ensure_output_dir() -> Path:
    """
    Ensure that ``data/raw`` exists and return its Path.

    Returns
    -------
    Path
        The absolute path to the ``data/raw`` directory.
    """
    raw_dir = get_project_root() / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir


def fetch_from_zenodo(url: str, dest_path: Path) -> bool:
    """
    Download a CSV from Zenodo and write it to ``dest_path``.

    Parameters
    ----------
    url : str
        Direct download URL.
    dest_path : Path
        Where the file should be saved.

    Returns
    -------
    bool
        ``True`` on success, ``False`` otherwise.
    """
    logger = get_logger(__name__)
    logger.info(f"Attempting to download dataset from Zenodo: {url}")
    # Use a request with a user‑agent to avoid potential 403 responses.
    request = Request(url, headers={"User-Agent": "python-urllib"})
    try:
        with urlopen(request) as response, open(dest_path, "wb") as out_file:
            # Stream the data in 1 MiB chunks to avoid huge memory usage.
            chunk_size = 1024 * 1024
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
        logger.info(f"Dataset successfully downloaded to {dest_path}")
        return True
    except (URLError, HTTPError) as exc:
        logger.error(f"Zenodo download failed: {exc}")
        return False
    except Exception as exc:  # pragma: no cover – unexpected failures
        logger.error(f"Unexpected error during download: {exc}")
        return False


def fetch_from_nist() -> bool:
    """
    Placeholder for a future NIST‑TRC implementation using the ``thermo`` library.

    Returns
    -------
    bool
        ``True`` if data was successfully retrieved, ``False`` otherwise.

    Notes
    -----
    The current pipeline prefers the Zenodo mirror because it requires no
    external scientific‑library dependencies beyond the standard library.
    """
    # TODO: integrate ``thermo``‑based retrieval when the upstream API is stable.
    return False


def update_plan_md(url: str) -> None:
    """
    Record the dataset URL inside ``plan.md``.

    If the file already contains a line with the exact URL, nothing is changed.
    Otherwise the URL is appended (or a minimal ``plan.md`` is created).

    Parameters
    ----------
    url : str
        The URL that was successfully used to fetch the dataset.
    """
    logger = get_logger(__name__)
    plan_path = get_project_root() / "plan.md"
    url_line = f"Dataset URL: {url}"

    if plan_path.exists():
        with open(plan_path, "r", encoding="utf-8") as f:
            content = f.read()
        if url_line in content:
            logger.info("Dataset URL already present in plan.md; no update needed.")
            return  # already recorded

        # Append a blank line and the URL line for readability.
        with open(plan_path, "a", encoding="utf-8") as f:
            f.write("\n" + url_line + "\n")
        logger.info(f"Appended dataset URL to existing plan.md at {plan_path}")
    else:
        # Create a minimal plan file that records the URL.
        with open(plan_path, "w", encoding="utf-8") as f:
            f.write("# Project Plan\n\n")
            f.write(url_line + "\n")
        logger.info(f"Created new plan.md and recorded dataset URL at {plan_path}")


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrates the download process.

    1. Guarantees the ``data/raw`` directory exists.
    2. Tries NIST first (currently a stub) and falls back to Zenodo.
    3. Writes the dataset to ``data/raw/dataset.csv``.
    4. Updates ``plan.md`` with the source URL.
    """
    logger = get_logger(__name__)
    raw_dir = ensure_output_dir()
    dest_file = raw_dir / "dataset.csv"

    # Attempt NIST retrieval first – currently not implemented.
    if fetch_from_nist():
        source_url = "NIST (retrieved via thermo – not implemented in this version)"
        logger.info("Dataset retrieved from NIST (placeholder).")
    elif fetch_from_zenodo(DATASET_URL, dest_file):
        source_url = DATASET_URL
        logger.info("Dataset retrieved from Zenodo.")
    else:
        logger.error("[ERROR] Could not obtain the diffusion dataset from any source.")
        sys.exit(1)

    update_plan_md(source_url)
    logger.info(f"Dataset successfully saved to {dest_file}")


if __name__ == "__main__":
    main()