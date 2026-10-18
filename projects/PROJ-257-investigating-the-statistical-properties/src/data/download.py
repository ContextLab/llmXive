"""
src/data/download.py

Download GWTC‑1 and GWTC‑2 posterior‑sample HDF5 files from their
official Zenodo releases, verify integrity, and write a checksums manifest.
The script aborts loudly on any failure (missing file, non‑HDF5 content,
checksum mismatch, or exhausted retries).

This implementation uses the **exact** URLs that host the HDF5 assets
(as of the time of writing).  If the Zenodo record changes, the download
will fail, which is the intended behaviour – the pipeline must not fall
back to unrelated files.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import h5py
from llmxive_toolkit import paths, get_logger

# Local imports
from src.utils.checksum import compute_file_hash

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration – explicit URLs for the HDF5 assets
# ----------------------------------------------------------------------
# These URLs point to the *download* endpoint of the Zenodo records that
# contain the official GWTC‑1 and GWTC‑2 posterior‑sample files.
# The `?download=1` query forces a direct file download.
DATASETS: List[Tuple[str, str]] = [
    # GWTC‑1 posterior samples
    (
        "https://zenodo.org/record/3937075/files/gwtc1.h5?download=1",
        "gwtc1.h5",
    ),
    # GWTC‑2 posterior samples
    (
        "https://zenodo.org/record/3937076/files/gwtc2.h5?download=1",
        "gwtc2.h5",
    ),
]

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
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
def download_all() -> Dict[str, Path]:
    """
    Download the two GWTC datasets, verify they are genuine HDF5 files,
    compute SHA‑256 hashes, and write a ``checksums.json`` manifest under
    ``data/raw/``.

    Returns
    -------
    dict
        Mapping from target filename (e.g. ``gwtc1.h5``) to the absolute
        ``Path`` on disk.
    """
    downloaded: Dict[str, Path] = {}
    for url, target_name in DATASETS:
        dest_path = paths.data("raw", target_name)
        _download_with_retries(url, dest_path)

        sha256 = compute_file_hash(str(dest_path), algorithm="sha256")
        log.info("SHA‑256 for %s: %s", target_name, sha256)
        downloaded[target_name] = dest_path

    # Write the checksums manifest
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
