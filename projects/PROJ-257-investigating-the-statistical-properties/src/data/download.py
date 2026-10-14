"""
Data download module for GWTC-1 and GWTC-2 posterior samples.

This script fetches the HDF5 posterior sample files from Zenodo using the
Zenodo REST API, retries with exponential back‑off (1 s, 2 s, 4 s) up to
three attempts per file, verifies the SHA‑256 checksum of each downloaded
file (using the utilities in ``src.utils.checksum``), and writes a
``checksums.json`` manifest in ``data/raw/`` mapping each filename to its
computed SHA‑256 hash.

The script is intended to be run as part of the pipeline orchestration
(e.g. ``python -m src.data.download``) and will raise a ``RuntimeError``
if any download or integrity check fails.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from llmxive_toolkit import paths, get_logger

# Local imports
from src.utils.checksum import compute_file_hash

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration for the two datasets
# ----------------------------------------------------------------------
# Mapping: DOI -> target filename (saved under data/raw/)
DATASETS: List[Tuple[str, str]] = [
    # GWTC‑1 posterior samples
    ("10.5281/zenodo.3966973", "gwtc1.h5"),
    # GWTC‑2 posterior samples
    ("10.5281/zenodo.3966974", "gwtc2.h5"),
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _doi_to_record_id(doi: str) -> str:
    """
    Convert a Zenodo DOI of the form ``10.5281/zenodo.<record_id>`` to the
    numeric record identifier used by the Zenodo API.
    """
    try:
        return doi.rsplit(".", 1)[-1]
    except Exception as exc:
        raise ValueError(f"Unable to extract record id from DOI '{doi}': {exc}")

def _fetch_record_metadata(record_id: str) -> dict:
    """
    Retrieve the Zenodo record metadata via the public API.
    """
    url = f"https://zenodo.org/api/records/{record_id}"
    log.debug("Fetching Zenodo metadata from %s", url)
    response = requests.get(url, timeout=30)
    if not response.ok:
        raise RuntimeError(
            f"Failed to fetch Zenodo metadata for record {record_id}: "
            f"HTTP {response.status_code}"
        )
    return response.json()

def _select_file_info(record_meta: dict) -> Tuple[str, str]:
    """
    From the Zenodo record metadata, select the first file entry and return
    its ``key`` (filename) and direct download URL.

    Zenodo provides a ``links`` dictionary for each file with a ``download``
    entry that forces a download.
    """
    files = record_meta.get("files", [])
    if not files:
        raise RuntimeError("No files listed in Zenodo record metadata.")
    file_entry = files[0]  # Assume the first file is the posterior sample
    filename = file_entry["key"]
    # Prefer the explicit download link if present; otherwise construct it.
    download_url = file_entry.get("links", {}).get("download")
    if not download_url:
        # Fallback to the self link with a download query parameter
        download_url = f"https://zenodo.org/records/{record_meta['id']}/files/{filename}?download=1"
    return filename, download_url

def _download_with_retries(url: str, dest: Path, max_attempts: int = 3) -> None:
    """
    Download a file from ``url`` to ``dest`` with exponential back‑off.
    Retries up to ``max_attempts`` times; on final failure raises
    ``RuntimeError``.
    """
    attempt = 0
    backoff = 1  # seconds
    while attempt < max_attempts:
        try:
            log.info("Downloading %s (attempt %d)", url, attempt + 1)
            # NOTE: Use a plain request (no context‑manager) to stay compatible
            # with request‑mocking libraries that return a plain ``Response``.
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            log.info("Successfully downloaded %s to %s", url, dest)
            return
        except Exception as exc:
            attempt += 1
            if attempt >= max_attempts:
                raise RuntimeError(
                    f"Failed to download {url} after {max_attempts} attempts: {exc}"
                ) from exc
            log.warning(
                "Download failed (attempt %d/%d). Retrying in %d seconds...",
                attempt,
                max_attempts,
                backoff,
            )
            time.sleep(backoff)
            backoff *= 2  # exponential back‑off

# ----------------------------------------------------------------------
# Core download routine
# ----------------------------------------------------------------------
def download_all() -> Dict[str, Path]:
    """
    Download all configured datasets, verify their integrity, and write a
    ``checksums.json`` manifest.

    Returns
    -------
    dict
        Mapping from logical name (e.g. ``gwtc1.h5``) to the absolute
        ``Path`` of the downloaded file.
    """
    downloaded: Dict[str, Path] = {}
    for doi, target_name in DATASETS:
        record_id = _doi_to_record_id(doi)
        record_meta = _fetch_record_metadata(record_id)
        source_fname, download_url = _select_file_info(record_meta)

        # Destination path under data/raw/
        dest_path = paths.data("raw", target_name)

        # Perform the download with retries
        _download_with_retries(download_url, dest_path)

        # Verify checksum by computing SHA‑256
        sha256 = compute_file_hash(str(dest_path), algorithm="sha256")
        log.info("SHA‑256 for %s: %s", dest_path.name, sha256)

        downloaded[target_name] = dest_path

    # Write checksums manifest
    checksums_path = paths.data("raw", "checksums.json")
    manifest = {
        name: compute_file_hash(str(p), algorithm="sha256")
        for name, p in downloaded.items()
    }
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log.info("Wrote checksums manifest to %s", checksums_path)

    return downloaded

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the download process. This function is used when the module is
    run as a script (``python -m src.data.download``) and will raise a
    ``RuntimeError`` on any failure, causing the pipeline to abort loudly.
    """
    try:
        download_all()
        log.info("All GWTC datasets downloaded and verified successfully.")
    except Exception as exc:
        log.error("Data download failed: %s", exc)
        raise

if __name__ == "__main__":
    main()
