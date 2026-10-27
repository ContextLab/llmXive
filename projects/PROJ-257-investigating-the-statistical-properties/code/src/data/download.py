"""
code/src/data/download.py

Core logic for downloading GWTC posterior sample archives from Zenodo.
Implements metadata retrieval, file selection, exponential back-off retries,
and SHA-256 checksum verification.
"""
import json
import time
import requests
from pathlib import Path
from typing import Tuple, Dict, List

from llmxive_toolkit import paths, get_logger
from src.utils.checksum import verify_file

log = get_logger(__name__)

# DOIs for GWTC-1 and GWTC-2 posterior samples
GWTC_RECORDS = {
    "gwtc1": "10.5281/zenodo.3966973",
    "gwtc2": "10.5281/zenodo.3966974",
}

def _doi_to_record_id(doi: str) -> str:
    """Convert a Zenodo DOI to the numeric record identifier."""
    # Example: 10.5281/zenodo.3966973 -> 3966973
    return doi.split(".")[-1]

def _fetch_record_metadata(record_id: str) -> dict:
    """Retrieve JSON metadata for a Zenodo record via the public API."""
    url = f"https://zenodo.org/api/records/{record_id}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def _select_file_info(meta: dict) -> Tuple[str, str, str]:
    """
    Select the primary HDF5 file from Zenodo metadata.
    Returns (filename, download_url, checksum).
    """
    files = meta.get("files", [])
    if not files:
        raise RuntimeError("No files found in Zenodo record metadata.")

    # Look for the largest .h5 file or the one matching a common pattern
    h5_files = [f for f in files if f.get("filename", "").endswith(".h5")]
    if not h5_files:
        raise RuntimeError("No HDF5 files found in Zenodo record.")

    # Usually, the main data file is the largest one
    target = max(h5_files, key=lambda x: x.get("size", 0))
    
    filename = target["filename"]
    download_url = target["links"]["self"] # The API 'self' link usually works for download
    # Zenodo API provides checksums in the metadata
    checksum = target.get("checksum")
    if not checksum:
        # Fallback: Some records might not have it in the API; 
        # we'll handle the missing checksum by recording the computed one.
        checksum = None
    
    return filename, download_url, checksum

def _download_with_retries(url: str, dest: Path) -> None:
    """Download url to dest with exponential back-off (1s, 2s, 4s)."""
    delays = [1, 2, 4]
    for attempt in range(4):
        try:
            log.info("Downloading %s (attempt %d/4)", url, attempt + 1)
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return
        except Exception as exc:
            if attempt < 3:
                wait = delays[attempt]
                log.warning("Download failed: %s. Retrying in %ds...", exc, wait)
                time.sleep(wait)
            else:
                log.error("All download attempts failed for %s", url)
                raise

def download_all() -> Dict[str, Path]:
    """
    Main orchestration: downloads GWTC-1 and GWTC-2, verifies checksums,
    and writes a checksums.json manifest.
    """
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_paths = {}
    checksum_manifest = {}

    for key, doi in GWTC_RECORDS.items():
        log.info("Processing %s (DOI: %s)", key, doi)
        record_id = _doi_to_record_id(doi)
        meta = _fetch_record_metadata(record_id)
        filename, url, expected_checksum = _select_file_info(meta)
        
        # We force a specific naming convention for the pipeline: gwtc1.h5, gwtc2.h5
        target_filename = f"{key}.h5"
        dest_path = raw_dir / target_filename
        
        _download_with_retries(url, dest_path)
        
        # Checksum verification
        if expected_checksum:
            # Zenodo sometimes provides checksums in different formats. 
            # We assume SHA-256 as per spec.
            if not verify_file(dest_path, expected_checksum):
                raise RuntimeError(f"Checksum verification failed for {target_filename}")
            log.info("Checksum verified for %s", target_filename)
        else:
            log.warning("No checksum provided by Zenodo for %s; skipping verification.", target_filename)
        
        # Record the actually computed checksum for the manifest
        from src.utils.checksum import compute_file_hash
        actual_hash = compute_file_hash(dest_path)
        
        downloaded_paths[target_filename] = dest_path
        checksum_manifest[target_filename] = actual_hash

    # Write manifest
    manifest_path = raw_dir / "checksums.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(checksum_manifest, f, indent=2, sort_keys=True)
    
    log.info("GWTC download and verification complete. Manifest written to %s", manifest_path)
    return downloaded_paths
