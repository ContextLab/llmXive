"""
VAERS Data Download Script (T002)
=================================

Downloads the verified VAERS 2020‑2023 dataset from Hugging Face
(`chrisvoncsefalvay/vaers-outcomes`) using the ``huggingface_hub``
library. The script writes the real parquet file to
``data/raw/vaers_2020_2023.parquet`` and records a SHA‑256 checksum in
``data/checksums.txt``. No synthetic fallback is performed; any download,
I/O, or checksum error raises an exception and aborts the run.

The script is deliberately lightweight: it does not import ``pyarrow`` (which
is incompatible with the environment's NumPy version) and instead relies on
the fact that the dataset repository already stores the parquet file as a
binary asset. ``huggingface_hub`` handles the download transparently.
"""

import hashlib
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download, RepositoryNotFoundError, RevisionNotFoundError, HfHubHTTPError
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DATASET_ID = "chrisvoncsefalvay/vaers-outcomes"
PARQUET_FILENAME = "vaers_2020_2023.parquet"  # exact name in the repo
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
    Returns the checksum string.
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
    Download the parquet asset from the Hugging‑Face hub. The function
    raises on any network or repository error; it does **not** attempt a
    synthetic fallback.
    """
    try:
        log.info("Attempting to download %s from %s", PARQUET_FILENAME, DATASET_ID)
        # ``repo_type="dataset"`` tells hf_hub_download we are dealing with a dataset.
        downloaded = hf_hub_download(
            repo_id=DATASET_ID,
            filename=PARQUET_FILENAME,
            repo_type="dataset",
        )
    except (RepositoryNotFoundError, RevisionNotFoundError, HfHubHTTPError) as exc:
        log.error("Failed to download dataset: %s", exc)
        raise RuntimeError(f"Unable to download {DATASET_ID}:{PARQUET_FILENAME}") from exc

    src_path = Path(downloaded)
    if not src_path.is_file() or src_path.stat().st_size == 0:
        raise RuntimeError(f"Downloaded file {src_path} is missing or empty.")

    # Ensure destination directory exists
    PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Move (or copy) to the canonical location within the project
    if src_path.resolve() != PARQUET_PATH.resolve():
        src_path.replace(PARQUET_PATH)
    else:
        # Already at the right location (unlikely)
        pass

    if not PARQUET_PATH.exists() or PARQUET_PATH.stat().st_size == 0:
        raise RuntimeError(f"Failed to place parquet file at {PARQUET_PATH}")

    log.info("Parquet file stored at %s (%d bytes)", PARQUET_PATH, PARQUET_PATH.stat().st_size)
    return PARQUET_PATH


def write_summary(parquet_path: Path, checksum: str) -> None:
    """
    Write a human‑readable acquisition summary (outside of any .gitignore).
    """
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
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrates the download, checksum, and summary steps.
    """
    log.info("Starting VAERS data download process")
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


if __name__ == "__main__":
    # When executed as a script ``python src/data/download.py`` we run the
    # pipeline and let any exception propagate (the runner will treat a
    # non‑zero exit as failure).
    main()
