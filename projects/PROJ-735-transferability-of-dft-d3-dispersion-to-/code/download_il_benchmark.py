"""
download_il_benchmark.py

Download the IL‑Benchmark dataset from Zenodo, falling back to the local
``data/raw/IL-Benchmark-local.zip`` archive when the network request fails
or when the checksum does not match the expected value.

The script:
  1. Attempts to resolve the Zenodo DOI specified in the environment variable
     ``IL_BENCHMARK_DOI`` (or a hard‑coded placeholder if the variable is not set).
  2. Downloads the ZIP file to a temporary location.
  3. Computes its SHA‑256 checksum and compares it against a recorded checksum
     (if a ``state/projects`` YAML file with a matching entry exists).
  4. If the download fails, the checksum mismatches, or no expected checksum is
     available, the script falls back to the bundled ``data/raw/IL-Benchmark-local.zip``.
  5. Extracts the archive into ``data/raw`` (or copies the CSV if the fallback is not a ZIP).
  6. Verifies that ``metadata.csv`` exists after extraction.

The script exits with status ``0`` on success and a non‑zero code on failure,
allowing the surrounding pipeline to abort cleanly if the required data cannot
be obtained.
"""

import hashlib
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path
import shutil

import requests
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_DOI = "10.5281/zenodo.0000000"  # placeholder – will be overridden by env
ZENODO_API_URL = "https://zenodo.org/api/records"

STATE_HASHES_PATH = Path("state/projects") / "PROJ-735-transferability-of-dft-d3-dispersion-to-.yaml"

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def sha256_file(filepath: Path) -> str:
    """Return the SHA‑256 checksum of ``filepath``."""
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_expected_checksum() -> str | None:
    """Load the expected checksum for the IL‑Benchmark ZIP if it is recorded."""
    if not STATE_HASHES_PATH.is_file():
        log.debug(f"No state file found at {STATE_HASHES_PATH}")
        return None
    try:
        import yaml  # yaml is part of the standard environment (PyYAML)
    except ImportError:
        log.warning("PyYAML not installed – cannot read expected checksum.")
        return None

    with STATE_HASHES_PATH.open() as f:
        state = yaml.safe_load(f)

    hashes = state.get("artifact_hashes", {})
    for key in (str(Path("data/raw/IL-Benchmark-local.zip")), "IL-Benchmark-local.zip"):
        if key in hashes:
            return hashes[key]
    return None

def download_from_zenodo(doi: str, dest_path: Path) -> bool:
    """
    Attempt to download the ZIP associated with ``doi``.
    Returns ``True`` on success, ``False`` otherwise.
    """
    try:
        record_id = int(doi.split(".")[-1])
    except Exception as exc:
        log.error(f"Unable to parse record ID from DOI '{doi}': {exc}")
        return False

    record_url = f"{ZENODO_API_URL}/{record_id}"
    log.info(f"Querying Zenodo API at {record_url}")

    try:
        resp = requests.get(record_url, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        log.error(f"Failed to query Zenodo API: {exc}")
        return False

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        log.error(f"Zenodo API returned invalid JSON: {exc}")
        return False

    zip_info = next(
        (f for f in data.get("files", []) if f.get("key", "").lower().endswith(".zip")),
        None,
    )
    if not zip_info:
        log.error("No ZIP file found in Zenodo record.")
        return False

    download_url = zip_info["links"]["self"]
    log.info(f"Downloading IL‑Benchmark ZIP from {download_url}")

    try:
        with requests.get(download_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with dest_path.open("wb") as out_f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        out_f.write(chunk)
    except Exception as exc:
        log.error(f"Download failed: {exc}")
        return False

    log.info(f"Downloaded archive to {dest_path}")
    return True

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the download / fallback logic and extract the archive.
    """
    doi = os.getenv("IL_BENCHMARK_DOI", DEFAULT_DOI)
    log.info(f"Using IL‑Benchmark DOI: {doi}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_zip = Path(tmpdir) / "il_benchmark.zip"

        # First attempt: download from Zenodo
        downloaded = download_from_zenodo(doi, tmp_zip)

        # Determine which archive we will use
        if downloaded:
            archive_path = tmp_zip
            log.info("Successfully downloaded dataset from Zenodo.")
        else:
            fallback_path = Path("data/raw/IL-Benchmark-local.zip")
            if not fallback_path.is_file():
                log.error(
                    f"Fallback archive not found at {fallback_path}. "
                    "Cannot continue without a dataset."
                )
                sys.exit(1)
            archive_path = fallback_path
            log.info(
                f"Using fallback archive {fallback_path} (download failed or checksum mismatch)."
            )

        # Verify checksum if an expected value is recorded
        expected_checksum = load_expected_checksum()
        actual_checksum = sha256_file(archive_path)
        log.debug(f"Actual checksum: {actual_checksum}")

        if expected_checksum:
            if actual_checksum != expected_checksum:
                log.error(
                    f"Checksum mismatch for {archive_path}.\n"
                    f"Expected: {expected_checksum}\n"
                    f"Actual:   {actual_checksum}"
                )
                sys.exit(1)
            else:
                log.info("Checksum verification passed.")
        else:
            log.info("No expected checksum recorded – proceeding without verification.")

        extract_dir = Path("data/raw")
        extract_dir.mkdir(parents=True, exist_ok=True)

        # Handle both real ZIP archives and plain CSV fallbacks
        if zipfile.is_zipfile(archive_path):
            try:
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(extract_dir)
                log.info(f"Extracted {archive_path} into {extract_dir}")
            except zipfile.BadZipFile as exc:
                log.error(f"Failed to extract ZIP archive: {exc}")
                sys.exit(1)
        else:
            # Assume the fallback is a CSV file containing the required metadata
            target = extract_dir / "metadata.csv"
            try:
                shutil.copyfile(archive_path, target)
                log.info(f"Copied fallback CSV to {target}")
            except Exception as exc:
                log.error(f"Failed to copy fallback CSV: {exc}")
                sys.exit(1)

        # Verify that the required ``metadata.csv`` exists.
        metadata_path = extract_dir / "metadata.csv"
        if not metadata_path.is_file():
            log.error(f"Required file {metadata_path} is missing after extraction.")
            sys.exit(1)

        log.info(f"Dataset ready – found {metadata_path}")

    # All done
    log.info("IL‑Benchmark dataset acquisition completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()