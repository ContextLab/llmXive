"""
src/data/download.py

Download GWTC‑1 and GWTC‑2 posterior sample archives from Zenodo,
extract the HDF5 payloads, compute SHA‑256 checksums, and write a
``checksums.json`` manifest under ``data/raw/``.
The public DOIs are:

* GWTC‑1: 10.5281/zenodo.3966973
* GWTC‑2: 10.5281/zenodo.3966974

The implementation follows the specification for task **T001**:
- Retrieve the Zenodo record metadata via the public API.
- Select the file ending with ``.h5``/``.hdf5`` if present,
  otherwise fall back to the first listed file.
- Download the file with up to three retries using exponential back‑off
  (1 s, 2 s, 4 s).
- If the downloaded file is a ZIP archive, extract the first HDF5 file
  inside and delete the archive.
- Verify that the resulting file is a valid HDF5 container.
- Compute its SHA‑256 hash and write a ``checksums.json`` manifest that
  maps the **filename** (e.g. ``gwtc1.h5``) to the hex digest.
- Return a mapping ``{filename: Path}`` for convenience.

The function raises on any unrecoverable error so that the calling
wrapper scripts (``code/src/data/download_gwtc.py`` and the test suite)
exit with a non‑zero status, satisfying the “fail loudly” requirement.
"""

import hashlib
import json
import time
import zipfile
from pathlib import Path
from typing import Dict, Tuple

import requests
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Zenodo DOIs for the two GWTC releases.
GWTC_DOIS = {
    "gwtc1.h5": "10.5281/zenodo.3966973",
    "gwtc2.h5": "10.5281/zenodo.3966974",
}

# Maximum number of download attempts per file.
MAX_RETRIES = 3
# Back‑off delays in seconds (len = MAX_RETRIES‑1).
BACKOFF_DELAYS = [1, 2, 4]

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _doi_to_record_id(doi: str) -> str:
    """
    Convert a Zenodo DOI to the numeric record identifier used by the API.
    Example: ``10.5281/zenodo.3966973`` → ``3966973``.
    """
    try:
        return doi.rsplit(".", 1)[-1]
    except Exception as exc:
        raise ValueError(f"Unable to extract record id from DOI '{doi}': {exc}") from exc


def _fetch_record_metadata(record_id: str) -> dict:
    """
    Retrieve the JSON metadata for a Zenodo record via the public API.
    """
    url = f"https://zenodo.org/api/records/{record_id}"
    log.debug("Fetching Zenodo metadata from %s", url)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def _select_file_info(meta: dict) -> Tuple[str, str]:
    """
    From a Zenodo record metadata dictionary, select the file to download.

    Returns a tuple ``(filename, download_url)``.
    Preference is given to files ending with ``.h5`` or ``.hdf5``.
    If none match, the first listed file is used.
    """
    files = meta.get("files", [])
    if not files:
        raise RuntimeError("No files listed in Zenodo record metadata.")

    # Prefer HDF5 files.
    for entry in files:
        name = entry.get("key", "")
        if name.lower().endswith((".h5", ".hdf5")):
            return name, entry["links"]["self"]

    # Fallback: first file.
    first = files[0]
    return first["key"], first["links"]["self"]


def _download_with_retries(url: str, dest: Path) -> None:
    """
    Download ``url`` to ``dest`` with exponential back‑off.
    Raises after ``MAX_RETRIES`` unsuccessful attempts.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info("Downloading (%d/%d): %s → %s", attempt, MAX_RETRIES, url, dest)
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        if chunk:
                            fh.write(chunk)
                tmp.rename(dest)
            log.debug("Download succeeded: %s", dest)
            return
        except Exception as exc:
            log.warning("Attempt %d failed for %s: %s", attempt, url, exc)
            if attempt < MAX_RETRIES:
                delay = BACKOFF_DELAYS[attempt - 1] if attempt - 1 < len(BACKOFF_DELAYS) else BACKOFF_DELAYS[-1]
                log.debug("Waiting %s seconds before retry...", delay)
                time.sleep(delay)
            else:
                raise RuntimeError(f"Failed to download {url} after {MAX_RETRIES} attempts.") from exc


def _is_hdf5(file_path: Path) -> bool:
    """
    Very lightweight check that the file starts with the HDF5 magic header.
    """
    try:
        with open(file_path, "rb") as fh:
            header = fh.read(8)
        return header == b"\x89HDF\r\n\x1a\n"
    except Exception:
        return False


def _extract_hdf5_from_zip(zip_path: Path, target_path: Path) -> None:
    """
    Extract the first HDF5 file found inside ``zip_path`` and place it at
    ``target_path``. The zip archive is removed after successful extraction.
    """
    log.debug("Extracting HDF5 from zip archive %s", zip_path)
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Find the first member that looks like an HDF5 file.
        h5_name = None
        for name in zf.namelist():
            if name.lower().endswith((".h5", ".hdf5")):
                h5_name = name
                break
        if h5_name is None:
            raise RuntimeError(f"No HDF5 file found inside zip archive {zip_path}")
        with zf.open(h5_name) as src, open(target_path, "wb") as dst:
            while True:
                chunk = src.read(1 << 20)
                if not chunk:
                    break
                dst.write(chunk)
    zip_path.unlink(missing_ok=True)
    log.debug("Extraction complete: %s → %s", zip_path, target_path)


def _compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hex digest of ``file_path``.
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def download_all() -> Dict[str, Path]:
    """
    Download the GWTC‑1 and GWTC‑2 posterior‑sample archives, verify their
    integrity, and write a ``checksums.json`` manifest.

    Returns
    -------
    dict
        Mapping ``filename -> Path`` for the extracted HDF5 files.
    """
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, str] = {}
    result_paths: Dict[str, Path] = {}

    for target_name, doi in GWTC_DOIS.items():
        record_id = _doi_to_record_id(doi)
        meta = _fetch_record_metadata(record_id)
        filename, download_url = _select_file_info(meta)

        # Destination path inside ``data/raw`` – we always name the final
        # file according to the expected target (gwtc1.h5 / gwtc2.h5).
        dest_path = raw_dir / target_name

        # Download to a temporary location first.
        tmp_path = raw_dir / filename
        _download_with_retries(download_url, tmp_path)

        # If we received a ZIP archive, extract the HDF5 payload.
        if zipfile.is_zipfile(tmp_path):
            _extract_hdf5_from_zip(tmp_path, dest_path)
        else:
            # Ensure the file is an HDF5 container; rename to the target name.
            if not _is_hdf5(tmp_path):
                raise RuntimeError(f"Downloaded file {tmp_path} is not a valid HDF5 archive.")
            tmp_path.rename(dest_path)

        # Verify the final file is HDF5.
        if not _is_hdf5(dest_path):
            raise RuntimeError(f"Extracted file {dest_path} failed HDF5 validation.")

        # Compute checksum and populate manifest.
        checksum = _compute_sha256(dest_path)
        manifest[target_name] = checksum
        result_paths[target_name] = dest_path
        log.info("Downloaded and verified %s (SHA‑256: %s)", dest_path, checksum)

    # Write the manifest.
    manifest_path = raw_dir / "checksums.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    log.info("Wrote checksum manifest to %s", manifest_path)

    return result_paths


def main() -> None:
    """
    CLI entry point used by ``code/src/data/download_gwtc.py``.
    """
    try:
        download_all()
        log.info("All GWTC files downloaded successfully.")
    except Exception as exc:
        log.error("GWTC download failed: %s", exc)
        raise


if __name__ == "__main__":
    main()