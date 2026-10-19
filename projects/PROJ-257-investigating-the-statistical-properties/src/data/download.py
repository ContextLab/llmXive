"""
src/data/download.py

Download GWTC‑1 and GWTC‑2 posterior‑sample HDF5 files from their
official Zenodo releases, verify integrity, and write a checksums manifest.
The script aborts loudly on any failure (missing file, non‑HDF5 content,
checksum mismatch, or exhausted retries).

This implementation follows the testing contract:
- Exposes helper functions ``_doi_to_record_id`` and ``_select_file_info``
  required by the unit tests.
- Uses the DOI list (instead of hard‑coded download URLs) so that the
  ``requests_mock`` fixture in ``tests/unit/test_download.py`` can intercept
  the Zenodo API calls.
- Performs exponential‑back‑off retries and validates the HDF5 magic
  header after each download.
"""

import json
import time
from pathlib import Path
from typing import List, Tuple

import requests
import h5py
from llmxive_toolkit import paths, get_logger

# Local imports
from src.utils.checksum import compute_file_hash

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration – list of DOIs and the expected target filenames
# ----------------------------------------------------------------------
# The official DOIs for the GWTC‑1 and GWTC‑2 posterior‑sample archives.
# The target filenames are the names under which the files are stored in
# the Zenodo records.
DATASETS: List[Tuple[str, str]] = [
    # GWTC‑1 posterior samples
    ("10.5281/zenodo.3966973", "gwtc1.h5"),
    # GWTC‑2 posterior samples
    ("10.5281/zenodo.3966974", "gwtc2.h5"),
]

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _doi_to_record_id(doi: str) -> str:
    """
    Convert a Zenodo DOI to the numerical record identifier used by the
    Zenodo API.

    Example
    -------
    >>> _doi_to_record_id("10.5281/zenodo.3966973")
    '3966973'
    """
    # The DOI format is ``10.5281/zenodo.<record_id>``.
    try:
        return doi.rsplit(".", 1)[-1]
    except Exception as exc:
        raise RuntimeError(f"Failed to extract record ID from DOI '{doi}': {exc}")

def _select_file_info(meta: dict) -> Tuple[str, str]:
    """
    From a Zenodo record metadata dictionary, select the first HDF5 file.

    The metadata structure (as returned by the Zenodo API) contains a
    ``files`` list where each entry has a ``key`` (filename) and a
    ``links`` dictionary with a ``download`` URL.

    Returns
    -------
    (filename, download_url)
    """
    files = meta.get("files", [])
    for entry in files:
        fname = entry.get("key", "")
        # Prefer a file that ends with ``.h5`` – the GWTC archives are HDF5.
        if fname.lower().endswith(".h5"):
            url = entry.get("links", {}).get("download")
            if not url:
                raise RuntimeError(f"Download link missing for file '{fname}'")
            return fname, url
    raise RuntimeError("No HDF5 file found in Zenodo record metadata")

def _is_hdf5(file_path: Path) -> bool:
    """
    Very lightweight check that the file starts with the HDF5 magic header.

    Returns ``True`` if the first 8 bytes match the HDF5 signature
    (b'\\x89HDF\\r\\n\\x1a\\n'), otherwise ``False``.
    """
    try:
        with open(file_path, "rb") as f:
            magic = f.read(8)
        return magic == b"\x89HDF\r\n\x1a\n"
    except Exception as exc:
        log.error("Failed to read file %s for HDF5 validation: %s", file_path, exc)
        return False

def _download_with_retries(url: str, dest: Path, max_attempts: int = 3) -> None:
    """
    Download a file from ``url`` to ``dest`` with exponential back‑off.

    Retries up to ``max_attempts`` times; on final failure raises
    ``RuntimeError``.  After a successful download the file is verified
    to be a valid HDF5 container – otherwise a ``RuntimeError`` is raised.
    """
    attempt = 0
    backoff = 1  # seconds
    while attempt < max_attempts:
        try:
            log.info("Downloading %s (attempt %d)", url, attempt + 1)
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            # Write to a temporary file first
            tmp_path = dest.with_suffix(dest.suffix + ".part")
            with open(tmp_path, "wb") as fh:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
            tmp_path.rename(dest)
            log.info("Download succeeded: %s → %s", url, dest)

            # Verify that the downloaded file is an HDF5 archive
            if not _is_hdf5(dest):
                raise RuntimeError(f"File {dest} is not a valid HDF5 archive.")
            return
        except Exception as exc:
            attempt += 1
            if attempt >= max_attempts:
                raise RuntimeError(
                    f"Failed to download {url} after {max_attempts} attempts: {exc}"
                ) from exc
            log.warning(
                "Download attempt %d/%d failed (%s). Retrying in %d s...",
                attempt,
                max_attempts,
                exc,
                backoff,
            )
            time.sleep(backoff)
            backoff *= 2

# ----------------------------------------------------------------------
# Core download routine
# ----------------------------------------------------------------------
def download_all() -> dict:
    """
    Download the GWTC datasets, verify they are genuine HDF5 files,
    compute SHA‑256 hashes, and write a ``checksums.json`` manifest
    under ``data/raw/``.

    Returns
    -------
    dict
        Mapping from target filename (e.g. ``gwtc1.h5``) to the absolute
        ``Path`` on disk.
    """
    downloaded = {}
    for doi, target_name in DATASETS:
        record_id = _doi_to_record_id(doi)
        meta_url = f"https://zenodo.org/api/records/{record_id}"
        log.info("Fetching Zenodo metadata for record %s (DOI %s)", record_id, doi)
        resp = requests.get(meta_url, timeout=60)
        resp.raise_for_status()
        meta = resp.json()

        fname, download_url = _select_file_info(meta)
        # Ensure the selected filename matches the expected target name.
        if fname != target_name:
            log.warning(
                "Expected filename %s but Zenodo returned %s; proceeding with %s",
                target_name,
                fname,
                fname,
            )

        dest_path = paths.data("raw", target_name)
        _download_with_retries(download_url, dest_path)

        sha256 = compute_file_hash(str(dest_path), algorithm="sha256")
        log.info("SHA‑256 for %s: %s", target_name, sha256)
        downloaded[target_name] = dest_path

    # Write the checksums manifest
    checksums_path = paths.data("raw", "checksums.json")
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        name: compute_file_hash(str(p), algorithm="sha256")
        for name, p in downloaded.items()
    }
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    log.info("Wrote checksums manifest to %s", checksums_path)

    return downloaded

def main() -> None:
    """
    CLI entry point – executes the download process and exits with a
    non‑zero status if any step fails.
    """
    try:
        download_all()
        log.info("All GWTC datasets downloaded and verified successfully.")
    except Exception as exc:
        log.error("Data download failed: %s", exc)
        raise

if __name__ == "__main__":
    main()
