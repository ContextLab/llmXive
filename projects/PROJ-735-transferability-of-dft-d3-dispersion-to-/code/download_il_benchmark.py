"""
download_il_benchmark.py
-------------------------

This script implements Task T022 – download the IL-Benchmark dataset
from Zenodo (or fall back to the local archive) and extract its contents
into data/raw/.

The script follows this logic:
1. Attempt download from Zenodo using the DOI in the spec.
2. If download fails (or DOI is empty), use the bundled fallback archive
   at data/raw/IL-Benchmark-local.zip.
3. If the fallback archive is also missing, the script fails loudly
   to avoid using synthetic/fabricated data.
4. Verify the archive is a valid zip and extract it to data/raw/.
5. Confirm that metadata.csv exists after extraction.
"""

import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Optional
import requests
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Zenodo DOI from spec (empty in current spec, forcing fallback)
IL_BENCHMARK_DOI: str = ""
# Canonical path for the fallback zip as per plan.md
FALLBACK_ZIP_PATH = paths.data("raw", "IL-Benchmark-local.zip")
# Manifest path for checksums
MANIFEST_PATH = paths.path("state", "projects", "manifest.json")

def sha256_file(filepath: Path) -> str:
    """Return the SHA-256 hex digest of *filepath*."""
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_expected_checksum() -> Optional[str]:
    """Load expected checksum from manifest if available."""
    if not MANIFEST_PATH.is_file():
        return None
    try:
        with MANIFEST_PATH.open("r") as mf:
            data = json.load(mf)
        return data.get("IL-Benchmark.zip") or data.get(str(FALLBACK_ZIP_PATH))
    except Exception as exc:
        log.warning(f"Unable to read manifest {MANIFEST_PATH}: {exc}")
        return None

def download_from_zenodo(doi: str, dest_path: Path) -> bool:
    """Attempt to download the Zenodo record into *dest_path*."""
    if not doi:
        log.info("No DOI provided – skipping Zenodo download.")
        return False

    record_url = f"https://zenodo.org/api/records/{doi}"
    log.info(f"Attempting to download Zenodo record {doi}")

    try:
        resp = requests.get(record_url, timeout=30)
        resp.raise_for_status()
        record = resp.json()
        files = record.get("files", [])
        zip_file = next((f for f in files if f["key"].lower().endswith(".zip")), None)
        if not zip_file:
            log.warning("No zip file found in Zenodo record.")
            return False

        download_url = zip_file["links"]["self"]
        log.info(f"Downloading {download_url}")

        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with dest_path.open("wb") as out_f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        out_f.write(chunk)

        log.info(f"Downloaded Zenodo archive to {dest_path}")
        return True
    except Exception as exc:
        log.error(f"Zenodo download failed: {exc}")
        return False

def extract_zip(archive_path: Path, extract_to: Path) -> None:
    """Extract *archive_path* into *extract_to*."""
    if not zipfile.is_zipfile(archive_path):
        raise zipfile.BadZipFile(f"File is not a valid zip archive: {archive_path}")

    log.info(f"Extracting {archive_path} to {extract_to}")
    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(path=extract_to)
    log.info("Extraction complete.")

def main() -> None:
    """Orchestrate the dataset acquisition."""
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    archive_path = raw_dir / "IL-Benchmark.zip"

    # 1. Attempt Zenodo download
    downloaded = False
    if IL_BENCHMARK_DOI:
        downloaded = download_from_zenodo(IL_BENCHMARK_DOI, archive_path)

    # 2. Fallback to bundled archive
    if not downloaded:
        if FALLBACK_ZIP_PATH.is_file():
            log.info(f"Using bundled fallback archive {FALLBACK_ZIP_PATH}")
            # Copy fallback to the working archive path
            archive_path.write_bytes(FALLBACK_ZIP_PATH.read_bytes())
        else:
            # FAIL LOUDLY: No real data source found.
            # Do NOT create synthetic data.
            raise FileNotFoundError(
                f"Neither Zenodo download nor local fallback archive ({FALLBACK_ZIP_PATH}) "
                "could be located. Real dataset is required to proceed."
            )

    # 3. Checksum verification
    expected_checksum = load_expected_checksum()
    if expected_checksum:
        actual_checksum = sha256_file(archive_path)
        if actual_checksum.lower() != expected_checksum.lower():
            raise ValueError(
                f"Checksum mismatch for {archive_path}: "
                f"expected {expected_checksum}, got {actual_checksum}"
            )
        log.info("Checksum verification passed.")
    else:
        log.info("No checksum manifest found – skipping verification.")

    # 4. Extract
    extract_zip(archive_path, raw_dir)

    # 5. Sanity check
    metadata_path = raw_dir / "metadata.csv"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Expected metadata file not found after extraction: {metadata_path}")
    log.info(f"Dataset ready – metadata located at {metadata_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(f"Dataset preparation failed: {exc}")
        sys.exit(1)
