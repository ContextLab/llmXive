"""
VAERS Data Download Script (T002)
=================================

Downloads the verified VAERS 2020-2023 dataset from Hugging Face
(``chrisvoncsefalvay/vaers-outcomes``) using the ``datasets`` library
and writes it to ``data/raw/vaers_2020_2023.parquet``.

A SHA-256 checksum of the parquet file is recorded as
``<file> <sha256>`` in ``data/checksums.txt`` (any previous entry for
the same file is replaced, so the file appears exactly once).

Any download or checksum error raises an exception — there is NO
synthetic fallback.
"""

import hashlib
import sys

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

DATASET_ID = "chrisvoncsefalvay/vaers-outcomes"
SPLIT = "train"
CHUNK_SIZE = 8192

# Output locations (project-relative via llmxive_toolkit.paths)
PARQUET_PATH = paths.data("raw", "vaers_2020_2023.parquet")
CHECKSUMS_PATH = paths.data("checksums.txt")


def sha256_checksum(file_path) -> str:
    """Return the SHA-256 hex digest of *file_path*."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def record_checksum(parquet_path, checksums_path) -> str:
    """Compute SHA-256 and record ``<file> <sha256>`` in checksums file.

    Replaces any existing entry for the same file so the filename
    appears exactly once. Returns the checksum.
    """
    checksum = sha256_checksum(parquet_path)
    rel = parquet_path.relative_to(paths.root)
    entry = f"{rel} {checksum}"

    existing_lines = []
    if checksums_path.exists():
        with open(checksums_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                # Drop stale entries for the same file
                if line.split(" ")[0] == str(rel):
                    continue
                existing_lines.append(line)

    with open(checksums_path, "w", encoding="utf-8") as f:
        for line in existing_lines:
            f.write(line + "\n")
        f.write(entry + "\n")
    return checksum


def download_vaers_dataset(
    dataset_id: str = DATASET_ID,
    split: str = SPLIT,
    dest=PARQUET_PATH,
):
    """Download the real VAERS dataset from Hugging Face to *dest*.

    Raises on any failure (network, dataset missing, empty data).
    No synthetic fallback is ever performed.
    """
    from datasets import load_dataset  # imported lazily so --help works fast

    log.info("Downloading dataset %s (split=%s)", dataset_id, split)
    try:
        ds = load_dataset(dataset_id, split=split)
    except Exception as exc:
        log.error("Failed to download dataset %s: %s", dataset_id, exc)
        raise

    if ds is None or len(ds) == 0:
        raise RuntimeError(
            f"Dataset {dataset_id} split {split} is empty; refusing to "
            "write an empty parquet file (no synthetic fallback)."
        )

    log.info("Downloaded %d rows; converting to pandas", len(ds))
    df = ds.to_pandas()

    dest.parent.mkdir(parents=True, exist_ok=True)
    log.info("Writing parquet to %s", dest)
    df.to_parquet(dest, index=False)

    if not dest.exists() or dest.stat().st_size == 0:
        raise RuntimeError(
          f"Parquet file {dest} was not written or is empty."
        )

    size_mb = dest.stat().st_size / (1024 * 1024)
    log.info("Wrote %s (%.1f MB, %d rows)", dest, size_mb, len(df))
    return dest


def main() -> None:
    """Entry point: download, checksum, verify."""
    log.info("Starting VAERS data download process")
    dest = download_vaers_dataset()

    try:
        checksum = record_checksum(dest, CHECKSUMS_PATH)
    except Exception as exc:
        log.error("Checksum computation failed for %s: %s", dest, exc)
        raise

    # Verify checksum entry: recompute and compare
    if checksum != sha256_checksum(dest):
        raise RuntimeError(
            "Checksum verification failed for %s" % dest
        )

    log.info(
        "Checksum recorded in %s: %s %s", CHECKSUMS_PATH, dest, checksum
    )
    log.info("VAERS data download and verification completed successfully.")


# Backwards-compatible alias used by src/main.py
def fetch_vaers_data() -> None:
    """Alias for main(); kept for pipeline import compatibility."""
    main()


if __name__ == "__main__":
    main()
