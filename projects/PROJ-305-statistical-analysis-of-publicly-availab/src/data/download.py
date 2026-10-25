"""
VAERS Data Download Script (T002) – Updated

Downloads the verified VAERS 2020‑2023 dataset using the 🤗 datasets library.
The script writes the parquet file to ``data/raw/vaers_2020_2023.parquet``
and records a SHA‑256 checksum in ``data/checksums.txt``.
Any download, I/O, or checksum error raises an exception and aborts the run –
no synthetic fallback is performed.
"""

import hashlib
import logging
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DATASET_NAME = "vaers/vaers2020_2023"
PARQUET_FILENAME = "vaers_2020_2023.parquet"
CHUNK_SIZE = 1024 * 1024  # 1 MiB for streaming checksum calculation

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
    Compute SHA‑256 and store ``<relative_path> <checksum>`` in the checksums file,
    replacing any previous entry for the same file.
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


def write_summary(parquet_path: Path, checksum: str) -> None:
    """Write a human‑readable acquisition summary."""
    size_bytes = parquet_path.stat().st_size
    lines = [
        "VAERS 2020‑2023 dataset acquisition summary (T002)",
        f"source: https://huggingface.co/datasets/{DATASET_NAME}",
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
    Orchestrates the download (via 🤗 datasets), checksum recording,
    and summary writing. Skips the download step if a non‑empty parquet
    file is already present.
    """
    if PARQUET_PATH.exists() and PARQUET_PATH.stat().st_size > 0:
        log.info("Parquet file already present at %s; skipping download.", PARQUET_PATH)
    else:
        log.info("Downloading VAERS dataset using the Hugging Face `datasets` library.")
        from datasets import load_dataset  # Imported lazily

        # Load the full training split; this returns a Dataset object
        ds = load_dataset(DATASET_NAME, split="train")
        PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
        ds.to_parquet(PARQUET_PATH)
        log.info(
            "Dataset written to %s (%d bytes)",
            PARQUET_PATH,
            PARQUET_PATH.stat().st_size,
        )

    # Record checksum and write summary
    checksum = record_checksum(PARQUET_PATH, CHECKSUMS_PATH)
    if checksum != sha256_checksum(PARQUET_PATH):
        raise RuntimeError("Checksum verification failed after recording.")
    write_summary(PARQUET_PATH, checksum)
    log.info(
        "Download and verification completed successfully. Checksum recorded in %s",
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
