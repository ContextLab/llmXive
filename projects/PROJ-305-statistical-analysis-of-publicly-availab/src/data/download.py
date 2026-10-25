"""
VAERS Data Download Script (T002) – Updated

Downloads the verified VAERS 2020‑2023 dataset from Hugging Face.
The official dataset identifier is
``chrisvoncsefalvay/vaers-outcomes``. The script writes the parquet file to
``data/raw/vaers_2020_2023.parquet`` and records a SHA‑256 checksum in
``data/checksums.txt``. Any download, I/O, or checksum error raises an
exception and aborts the run – no synthetic fallback is performed.
"""

import hashlib
import sys
from pathlib import Path

from datasets import load_dataset, Dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Verified dataset identifier as per the specification and quickstart
DATASET_ID = "chrisvoncsefalvay/vaers-outcomes"
PARQUET_FILENAME = "vaers_2020_2023.parquet"
CHUNK_SIZE = 1024 * 1024  # 1 MiB for checksum streaming

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


def download_parquet() -> Path:
    """
    Acquire the dataset from Hugging Face using the ``datasets`` library
    and save it as a local parquet file.
    """
    try:
        log.info("Loading dataset %s from Hugging Face", DATASET_ID)
        # ``load_dataset`` handles the download and caching.
        # We request the ``train`` split because the dataset is a single
        # collection of reports.
        ds: Dataset = load_dataset(DATASET_ID, split="train")
    except Exception as exc:
        log.error("Failed to load dataset %s: %s", DATASET_ID, exc)
        raise RuntimeError(
            f"Unable to acquire {DATASET_ID} via datasets.load_dataset"
        ) from exc

    # Ensure destination directory exists
    PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Write directly to parquet – this is memory‑efficient because
        # ``datasets`` streams to disk.
        ds.to_parquet(PARQUET_PATH)
    except Exception as exc:
        log.error("Failed to write parquet file: %s", exc)
        raise RuntimeError(f"Could not write parquet to {PARQUET_PATH}") from exc

    if not PARQUET_PATH.exists() or PARQUET_PATH.stat().st_size == 0:
        raise RuntimeError(
            f"Saved parquet file {PARQUET_PATH} is missing or empty."
        )

    log.info(
        "Parquet file stored at %s (%d bytes)",
        PARQUET_PATH,
        PARQUET_PATH.stat().st_size,
    )
    return PARQUET_PATH


def write_summary(parquet_path: Path, checksum: str) -> None:
    """Write a human‑readable acquisition summary."""
    size_bytes = parquet_path.stat().st_size
    lines = [
        "VAERS 2020‑2023 dataset acquisition summary (T002)",
        f"source: Hugging Face dataset {DATASET_ID!r}",
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
    parquet_path = download_parquet()

    try:
        checksum = record_checksum(parquet_path, CHECKSUMS_PATH)
    except Exception as exc:
        log.error("Checksum recording failed: %s", exc)
        raise

    # Verify we can recompute the same checksum
    if checksum != sha256_checksum(parquet_path):
        raise RuntimeError("Checksum verification failed after recording.")

    write_summary(parquet_path, checksum)

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
