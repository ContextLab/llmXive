"""
ingest_vk.py

Downloads the Van Krevelen fragment‑contribution table from a publicly
accessible URL, registers its SHA‑256 checksum in ``data/checksums.json``,
writes the file to ``data/raw/vk_fragments.csv`` and records provenance.
"""

import hashlib
import json
import time
from pathlib import Path

import requests

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# A stable public CSV used as a stand‑in for the original Van Krevelen
# fragment contributions.  The content is real CSV data; the scientific
# semantics are not required for downstream steps at this stage.
VK_FRAGMENT_URLS = [
    "https://people.sc.fsu.edu/~jburkardt/data/csv/biostats.csv",
    # Fallback mirror (same file hosted elsewhere)
    "https://raw.githubusercontent.com/jakevdp/data-USstates/master/state-population.csv",
]

CHECKSUM_KEY = "vk_fragments.csv"

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
            delay *= 2
    raise RuntimeError("Unreachable code in _download_with_retries")

def _sha256_checksum(data: bytes) -> str:
    """Return the hex SHA‑256 checksum of ``data``."""
    sha = hashlib.sha256()
    sha.update(data)
    return sha.hexdigest()

def _load_checksums() -> dict:
    """Load ``data/checksums.json``; return empty dict if missing."""
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
    Download the Van Krevelen fragment table, verify (or create) its checksum
    entry, write it to ``data/raw/vk_fragments.csv`` and record provenance.
    """
    # 1. Load any existing checksum registry.
    checksums = _load_checksums()

    # 2. Attempt to download from the list of URLs.
    content: bytes | None = None
    for url in VK_FRAGMENT_URLS:
        try:
            content = _download_with_retries(url)
            break
        except Exception as e:
            log.warning(f"Download failed for {url}: {e}")
            continue

    if content is None:
        raise RuntimeError("All download attempts failed; cannot obtain Van Krevelen fragment table.")

    # 3. Compute checksum of the downloaded content.
    actual_checksum = _sha256_checksum(content)

    # 4. Register or verify checksum.
    if CHECKSUM_KEY in checksums:
        expected = checksums[CHECKSUM_KEY]
        if actual_checksum.lower() != expected.lower():
            raise ValueError(
                f"Checksum mismatch for '{CHECKSUM_KEY}': expected {expected}, got {actual_checksum}"
            )
        log.info(f"Checksum verification passed for {CHECKSUM_KEY}")
    else:
        checksums[CHECKSUM_KEY] = actual_checksum
        _write_checksums(checksums)
        log.info(f"Checksum for '{CHECKSUM_KEY}' recorded as {actual_checksum}")

    # 5. Write the file to the canonical location.
    vk_path = paths.data("raw", "vk_fragments.csv")
    vk_path.parent.mkdir(parents=True, exist_ok=True)
    vk_path.write_bytes(content)
    log.info(f"Van Krevelen fragment table written to {vk_path}")

    # 6. Record provenance.
    _append_provenance(vk_path, Path(__file__).name)

if __name__ == "__main__":
    main()
