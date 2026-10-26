"""
src/data/download.py

Implements the GWTC‑1 and GWTC‑2 posterior sample download workflow used by
the T001 task. The implementation follows the specification:

* Retrieve the Zenodo record for each DOI.
* Select the HDF5 payload (or a ZIP containing it).
* Download with exponential back‑off (1 s, 2 s, 4 s) and up to three attempts.
* Verify the file is a valid HDF5 container.
* Compute the SHA‑256 checksum and compare it to the checksum reported in
  the Zenodo metadata.
* Write the downloaded files to ``data/raw/`` and emit a ``checksums.json``
  manifest mapping ``filename → checksum``.
* Return a ``dict`` mapping the base filename to the absolute ``Path`` of
  the downloaded file.

The module is deliberately self‑contained and does **not** rely on any
external helper modules that may be missing or broken. It uses only the
standard library and the project's guaranteed dependencies (``requests``,
``tqdm``, ``h5py``).
"""

import hashlib
import json
import logging
import time
import zipfile
from pathlib import Path
from typing import Dict, Tuple

import requests
from tqdm import tqdm

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# DOIs for GWTC‑1 and GWTC‑2 posterior sample archives.
GWTC_DOIS = [
    "10.5281/zenodo.3966973",  # GWTC‑1
    "10.5281/zenodo.3966974",  # GWTC‑2
]

# Maximum number of download attempts per file.
MAX_RETRIES = 3
# Back‑off delays (seconds) between attempts.
RETRY_DELAYS = [1, 2, 4]

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _doi_to_record_id(doi: str) -> str:
    """
    Convert a Zenodo DOI to the numeric record identifier used by the API.

    Example:
        >>> _doi_to_record_id("10.5281/zenodo.3966973")
        '3966973'
    """
    if not doi.startswith("10.5281/zenodo."):
        raise ValueError(f"Unexpected DOI format: {doi}")
    return doi.split(".")[-1]


def _fetch_record_metadata(record_id: str) -> dict:
    """
    Retrieve the JSON metadata for a Zenodo record via the public API.

    Parameters
    ----------
    record_id:
        The numeric identifier extracted from the DOI.

    Returns
    -------
    dict
        Parsed JSON metadata.
    """
    url = f"https://zenodo.org/api/records/{record_id}"
    log.debug("Fetching Zenodo metadata from %s", url)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _select_file_info(meta: dict) -> Tuple[str, str]:
    """
    From a Zenodo record metadata dictionary, select the file to download.

    Preference order:
    1. A file ending with ``.h5`` or ``.hdf5``.
    2. If no HDF5 file is present, the first listed file (often a ZIP).

    Returns
    -------
    (filename, download_url)
    """
    files = meta.get("files", [])
    if not files:
        raise RuntimeError("No files listed in Zenodo record metadata.")

    # Prefer direct HDF5 files.
    for entry in files:
        name = entry.get("key", "")
        if name.lower().endswith((".h5", ".hdf5")):
            return name, entry["links"]["self"]

    # Fallback to first file.
    first = files[0]
    return first["key"], first["links"]["self"]


def _download_with_retries(url: str, dest: Path) -> None:
    """
    Download ``url`` to ``dest`` with exponential back‑off.

    Raises
    ------
    RuntimeError
        If all attempts fail.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info("Downloading (attempt %d/%d): %s", attempt, MAX_RETRIES, url)
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                tmp_path = dest.with_suffix(dest.suffix + ".part")
                with open(tmp_path, "wb") as f, tqdm(
                    total=total,
                    unit="B",
                    unit_scale=True,
                    desc=dest.name,
                    leave=False,
                ) as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
                tmp_path.rename(dest)
            return
        except Exception as exc:
            log.warning("Download attempt %d failed: %s", attempt, exc)
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                log.info("Retrying after %s seconds...", delay)
                time.sleep(delay)
            else:
                raise RuntimeError(f"Failed to download {url} after {MAX_RETRIES} attempts.") from exc


def _is_hdf5(file_path: Path) -> bool:
    """
    Very lightweight check that the file starts with the HDF5 magic header.

    Returns ``True`` if the first 8 bytes match the HDF5 signature.
    """
    try:
        with file_path.open("rb") as f:
            header = f.read(8)
        return header == b"\x89HDF\r\n\x1a\n"
    except Exception:
        return False


def _extract_hdf5_from_zip(zip_path: Path, target_path: Path) -> None:
    """
    Extract the first ``.h5`` or ``.hdf5`` file from ``zip_path`` into
    ``target_path``. Raises ``RuntimeError`` if no such file is found.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        candidates = [n for n in zf.namelist() if n.lower().endswith((".h5", ".hdf5"))]
        if not candidates:
            raise RuntimeError(f"No HDF5 file found inside ZIP archive {zip_path}")
        # Extract the first candidate.
        member = candidates[0]
        log.info("Extracting %s from %s to %s", member, zip_path, target_path)
        with zf.open(member) as src, open(target_path, "wb") as dst:
            while True:
                chunk = src.read(8192)
                if not chunk:
                    break
                dst.write(chunk)


def _compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path`` and return the hex digest.
    """
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def download_all() -> Dict[str, Path]:
    """
    Download the GWTC‑1 and GWTC‑2 posterior sample archives, verify their
    integrity, and write a ``checksums.json`` manifest.

    Returns
    -------
    dict
        Mapping ``filename → Path`` for the downloaded HDF5 files.
    """
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    checksums: Dict[str, str] = {}
    downloaded: Dict[str, Path] = {}

    for doi in GWTC_DOIS:
        record_id = _doi_to_record_id(doi)
        meta = _fetch_record_metadata(record_id)
        filename, download_url = _select_file_info(meta)

        # Destination path inside ``data/raw``.
        dest_path = raw_dir / filename

        # Download (with retries).
        _download_with_retries(download_url, dest_path)

        # If the downloaded file is a ZIP, extract the HDF5 inside it.
        if dest_path.suffix.lower() == ".zip":
            # Determine final HDF5 name (same base, .h5 extension).
            h5_name = dest_path.stem + ".h5"
            h5_path = raw_dir / h5_name
            _extract_hdf5_from_zip(dest_path, h5_path)
            # Remove the ZIP after extraction.
            try:
                dest_path.unlink()
            except Exception:
                pass
            dest_path = h5_path

        # Verify HDF5 signature.
        if not _is_hdf5(dest_path):
            raise RuntimeError(f"Downloaded file {dest_path} is not a valid HDF5 archive.")

        # Compute checksum and compare with Zenodo metadata (if available).
        computed_hash = _compute_sha256(dest_path)

        # Zenodo may provide a checksum string like "sha256:abcdef..."
        expected_hash = None
        for file_entry in meta.get("files", []):
            if file_entry.get("key") == filename:
                checksum_str = file_entry.get("checksum", "")
                if checksum_str.startswith("sha256:"):
                    expected_hash = checksum_str.split(":", 1)[1]
                break

        if expected_hash and computed_hash.lower() != expected_hash.lower():
            raise RuntimeError(
                f"Checksum mismatch for {dest_path}: expected {expected_hash}, got {computed_hash}"
            )

        checksums[dest_path.name] = computed_hash
        downloaded[dest_path.name] = dest_path
        log.info("Successfully downloaded and verified %s", dest_path)

    # Write the manifest.
    manifest_path = raw_dir / "checksums.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(checksums, fh, indent=2, sort_keys=True)
    log.info("Checksum manifest written to %s", manifest_path)

    return downloaded
