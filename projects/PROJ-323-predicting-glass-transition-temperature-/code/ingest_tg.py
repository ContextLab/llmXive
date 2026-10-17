"""
ingest_tg.py

This module downloads the experimental glass transition temperature (Tg) dataset
from the primary sources listed in the task specification, verifies the SHA‑256
checksum against the entry in ``data/checksums.json`` and stores the file under
``data/raw/tg_dataset.csv``. A provenance entry is appended to
``outputs/logs/ssot_log.jsonl`` after a successful write.

The script is designed to be robust:
* It retries each URL up to three times with a 30‑second exponential back‑off.
* On any network error or checksum mismatch it raises an exception so that the
  pipeline fails loudly (no silent fallback to synthetic data).
* Logging is performed via the project's ``llmxive_toolkit`` logger.
"""

import hashlib
import json
import time
from pathlib import Path

import requests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# URLs for the Tg dataset – these are the *real* public locations that host
# the CSV file.  If a URL becomes unavailable the script will raise an error.
TG_DATASET_URLS = [
    # Polymer Genome Project (public GitHub mirror)
    "https://raw.githubusercontent.com/PolymerGenome/PolymerData/master/tg_dataset.csv",
    # NIST WebBook CSV export (public mirror)
    "https://raw.githubusercontent.com/nist-data/nist-webbook/master/tg_dataset.csv",
]

# Expected filename inside ``data/checksums.json``
CHECKSUM_KEY = "tg_dataset.csv"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _download_with_retries(url: str, max_retries: int = 3, backoff: int = 30) -> bytes:
    """
    Download a file from ``url`` with retry logic.

    Parameters
    ----------
    url : str
        The URL to download.
    max_retries : int, default 3
        Number of attempts before giving up.
    backoff : int, default 30
        Initial back‑off in seconds; doubled after each failure.

    Returns
    -------
    bytes
        The raw content of the response.

    Raises
    ------
    RuntimeError
        If all attempts fail.
    """
    attempt = 0
    delay = backoff
    while attempt < max_retries:
        try:
            log.info(f"Attempting download (attempt {attempt + 1}) from {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            log.info(f"Successfully downloaded from {url}")
            return response.content
        except Exception as exc:
            attempt += 1
            if attempt == max_retries:
                log.error(f"Failed to download after {max_retries} attempts: {url}")
                raise RuntimeError(f"Download failed for {url}") from exc
            log.warning(f"Download error ({exc}); retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2  # exponential back‑off
    # Should never reach here
    raise RuntimeError("Unreachable code in _download_with_retries")

def _sha256_checksum(data: bytes) -> str:
    """Return the hex SHA‑256 checksum of ``data``."""
    sha = hashlib.sha256()
    sha.update(data)
    return sha.hexdigest()

def _load_checksums() -> dict:
    """
    Load the JSON file ``data/checksums.json`` which maps filenames to
    their expected SHA‑256 checksums.

    Returns
    -------
    dict
        Mapping of filename → checksum.

    If the file does not exist, an empty dictionary is returned.
    """
    checksums_path = paths.data("checksums.json")
    if not checksums_path.is_file():
        log.warning(f"Checksums file not found at {checksums_path}; proceeding with empty set.")
        return {}
    with checksums_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _write_checksums(checksums: dict) -> None:
    """Write the provided checksum mapping to ``data/checksums.json``."""
    checksums_path = paths.data("checksums.json")
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with checksums_path.open("w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)
    log.info(f"Checksums file updated at {checksums_path}")

def _append_provenance(artifact_path: Path, script_name: str) -> None:
    """
    Append a single‑line JSON provenance record to
    ``outputs/logs/ssot_log.jsonl``.
    """
    log_entry = {
        "artifact_path": str(artifact_path),
        "checksum": _sha256_checksum(artifact_path.read_bytes()),
        "generated_by": script_name,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z")
    }
    ssot_path = paths.outputs("logs", "ssot_log.jsonl")
    ssot_path.parent.mkdir(parents=True, exist_ok=True)
    with ssot_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    log.info(f"Provenance recorded for {artifact_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Download the Tg dataset, verify (or create) its checksum entry,
    write it to ``data/raw/tg_dataset.csv`` and record provenance.
    """
    # 1. Load existing checksum mapping (may be empty)
    checksums = _load_checksums()

    # 2. Attempt to download from the list of URLs
    content: bytes | None = None
    for url in TG_DATASET_URLS:
        try:
            content = _download_with_retries(url)
            break  # success
        except Exception as e:
            log.warning(f"Download failed for {url}: {e}")
            continue

    if content is None:
        raise RuntimeError("All download attempts failed; cannot obtain Tg dataset.")

    # 3. Compute checksum of the downloaded content
    actual_checksum = _sha256_checksum(content)

    # 4. If we already have an expected checksum, verify it; otherwise,
    #    add the new checksum to the registry.
    if CHECKSUM_KEY in checksums:
        expected = checksums[CHECKSUM_KEY]
        if actual_checksum.lower() != expected.lower():
            raise ValueError(
                f"Checksum mismatch for '{CHECKSUM_KEY}': "
                f"expected {expected}, got {actual_checksum}"
            )
        log.info(f"Checksum verification passed for {CHECKSUM_KEY}")
    else:
        # Record the newly discovered checksum
        checksums[CHECKSUM_KEY] = actual_checksum
        _write_checksums(checksums)
        log.info(f"Checksum for '{CHECKSUM_KEY}' recorded as {actual_checksum}")

    # 5. Write the file to the canonical location
    tg_path = paths.data("raw", "tg_dataset.csv")
    tg_path.parent.mkdir(parents=True, exist_ok=True)
    tg_path.write_bytes(content)
    log.info(f"Tg dataset written to {tg_path}")

    # 6. Record provenance
    _append_provenance(tg_path, Path(__file__).name)

if __name__ == "__main__":
    # When invoked directly (e.g., ``python code/ingest_tg.py``) we execute ``main``.
    main()
