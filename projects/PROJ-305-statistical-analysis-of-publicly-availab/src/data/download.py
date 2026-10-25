"""
VAERS Data Download Script (T002) – Updated

Downloads the verified VAERS 2020‑2023 dataset from Hugging Face without
pulling in heavy dependencies that require newer NumPy versions.
The script writes the parquet file to ``data/raw/vaers_2020_2023.parquet``
and records a SHA‑256 checksum in ``data/checksums.txt``.
Any download, I/O, or checksum error raises an exception and aborts the run –
no synthetic fallback is performed.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Tuple

import requests
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Verified dataset URL – direct link to the parquet file on Hugging Face.
DATASET_URL = (
    "https://huggingface.co/datasets/vaers/vaers2020_2023/resolve/main/"
    "vaers_2020_2023.parquet"
)
PARQUET_FILENAME = "vaers_2020_2023.parquet"
CHUNK_SIZE = 1024 * 1024  # 1 MiB for streaming download & checksum

# Output locations (project‑relative via llmxive_toolkit.paths)
PARQUET_PATH = paths.data("raw", PARQUET_FILENAME)
CHECKSUMS_PATH = paths.data("checksums.txt")
SUMMARY_PATH = paths.data("results", "download_summary.txt")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def sha256_checksum(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of *file_path*."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def record_checksum(parquet_path: Path, checksums_path: Path) -> str:
    """
    Compute SHA‑256 and record ``<relative_path> <checksum>`` in the
    checksums file, replacing any previous entry for the same file.
    """
    checksum = sha256_checksum(parquet_path)
    rel = parquet_path.relative_to(paths.root)
    entry = f"{rel} {checksum}"

    existing = []
    if checksums_path.exists():
        for line in checksums_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            if line.split(" ")[0] == str(rel):
                continue  # drop stale entry
            existing.append(line)

    with checksums_path.open("w", encoding="utf-8") as f:
        for line in existing:
            f.write(line + "\n")
        f.write(entry + "\n")
    return checksum


def download_file(url: str, dest_path: Path) -> None:
    """
    Stream‑download *url* to *dest_path*.
    Raises an exception on HTTP errors or I/O problems.
    """
    log.info("Starting download from %s", url)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Use a streaming request to avoid loading the whole file into memory.
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with dest_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:  # filter out keep‑alive chunks
                    f.write(chunk)

    if not dest_path.exists() or dest_path.stat().st_size == 0:
        raise RuntimeError(
            f"Downloaded file {dest_path} is missing or empty."
        )
    log.info(
        "Download completed: %s (%d bytes)",
        dest_path,
        dest_path.stat().st_size,
    )


def write_summary(parquet_path: Path, checksum: str) -> None:
    """Write a human‑readable acquisition summary."""
    size_bytes = parquet_path.stat().st_size
    lines = [
        "VAERS 2020‑2023 dataset acquisition summary (T002)",
        f"source: {DATASET_URL}",
        f"file: {parquet_path.relative_to(paths.root)}",
        f"sha256: {checksum}",
        f"size_bytes: {size_bytes}",
        f"size_mb: {size_bytes / (1024 * 1024):.1f}",
    ]
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("Wrote acquisition summary to %s", SUMMARY_PATH)


# ----------------------------------------------------------------------
# Public API used by the pipeline orchestrator
# ----------------------------------------------------------------------
def fetch_vaers_data() -> None:
    """
    Orchestrates the download, checksum recording, and summary writing.
    """
    log.info("Starting VAERS data download process (fetch_vaers_data)")

    # 1. Download the parquet file
    download_file(DATASET_URL, PARQUET_PATH)

    # 2. Record checksum
    try:
        checksum = record_checksum(PARQUET_PATH, CHECKSUMS_PATH)
    except Exception as exc:
        log.error("Checksum recording failed: %s", exc)
        raise

    # 3. Verify checksum consistency
    if checksum != sha256_checksum(PARQUET_PATH):
        raise RuntimeError("Checksum verification failed after recording.")

    # 4. Write human‑readable summary
    write_summary(PARQUET_PATH, checksum)

    log.info(
        "Download and verification completed successfully. "
        "Checksum recorded in %s",
        CHECKSUMS_PATH,
    )


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI wrapper used by the quickstart.
    """
    fetch_vaers_data()


if __name__ == "__main__":
    main()