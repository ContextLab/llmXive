"""Core logic for downloading GWTC datasets from Zenodo with verification.

This module implements the robust download workflow including Zenodo API
metadata retrieval, exponential back-off retries, and SHA-256 verification.
"""
import json
import time
import requests
from pathlib import Path
from typing import Tuple, Dict

from llmxive_toolkit import paths, get_logger
from src.utils.checksum import compute_file_hash, verify_file

log = get_logger(__name__)

# DOIs for GWTC-1 and GWTC-2 posterior samples
GWTC_DOIS = {
    "gwtc1": "10.5281/zenodo.3966973",
    "gwtc2": "10.5281/zenodo.3966974",
}

def _doi_to_record_id(doi: str) -> str:
    """Convert a Zenodo DOI to the numeric record identifier."""
    return doi.split(".")[-1]

def _fetch_record_metadata(record_id: str) -> dict:
    """Retrieve JSON metadata for a Zenodo record via the public API."""
    url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def _select_file_info(meta: dict) -> Tuple[str, str, str]:
    """
    Select the HDF5 file from Zenodo metadata.
    Returns (filename, download_url, checksum).
    """
    files = meta.get("files", [])
    # Priority: .h5 or .hdf5
    for f in files:
        fname = f.get("key", "")
        if fname.endswith(".h5") or fname.endswith(".hdf5"):
            return fname, f.get("links", {}).get("download"), f.get("checksum")
    
    if not files:
        raise RuntimeError("No files found in Zenodo record metadata.")
    
    # Fallback to first file
    f = files[0]
    return f.get("key", "unknown"), f.get("links", {}).get("download"), f.get("checksum")

def _download_with_retries(url: str, dest: Path) -> None:
    """Download url to dest with exponential back-off (1s, 2s, 4s)."""
    delays = [1, 2, 4]
    for attempt in range(1, 4):
        try:
            log.info("Download attempt %d/3 for %s", attempt, url)
            with requests.get(url, timeout=60, stream=True) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return
        except Exception as e:
            if attempt == 3:
                raise RuntimeError(f"Failed to download {url} after 3 attempts: {e}")
            wait = delays[attempt - 1]
            log.warning("Attempt %d failed (%s). Retrying in %ds...", attempt, e, wait)
            time.sleep(wait)

def download_all() -> Dict[str, Path]:
    """
    Main orchestration: downloads GWTC-1 and GWTC-2, verifies checksums,
    and writes a checksums.json manifest.
    """
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    verified_files = {}
    checksum_manifest = {}

    for key, doi in GWTC_DOIS.items():
        record_id = _doi_to_record_id(doi)
        log.info("Processing %s (DOI: %s)", key, doi)
        
        meta = _fetch_record_metadata(record_id)
        filename, url, expected_hash = _select_file_info(meta)
        
        # We want the files named gwtc1.h5 and gwtc2.h5 specifically as per spec
        target_filename = f"{key}.h5"
        dest_path = raw_dir / target_filename
        
        _download_with_retries(url, dest_path)
        
        if expected_hash:
            if not verify_file(dest_path, expected_hash):
                raise RuntimeError(f"Checksum verification failed for {target_filename}")
            log.info("Checksum verified for %s", target_filename)
        else:
            log.warning("No checksum provided by Zenodo for %s; skipping verification.", target_filename)
        
        # Record the actual hash for the project's manifest
        actual_hash = compute_file_hash(dest_path)
        checksum_manifest[target_filename] = actual_hash
        verified_files[target_filename] = dest_path

    # Write the checksums.json manifest for T002
    manifest_path = raw_dir / "checksums.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(checksum_manifest, f, indent=2)
    
    log.info("All GWTC files downloaded and manifest written to %s", manifest_path)
    return verified_files
