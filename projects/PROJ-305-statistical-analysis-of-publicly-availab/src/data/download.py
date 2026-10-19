"""
VAERS Data Download Script (T002)
=================================

Downloads the verified VAERS 2020-2023 dataset from Hugging Face
(``chrisvoncsefalvay/vaers-outcomes``) using the ``datasets``
library, exactly as required by the task:

    datasets.load_dataset("chrisvoncsefalvay/vaers-outcomes",
                          split="train")

The dataset is streamed in batches and written to
``data/raw/vaers_2020_2023.parquet`` via ``pyarrow`` so that the
full real dataset drives the output without ever materialising it
all in memory at once.

A SHA-256 checksum of the file is recorded as
``<file> <sha256>`` in ``data/checksums.txt`` (any previous entry
for the same file is replaced, so the file appears exactly once).
A durable, non-gitignored summary (row count, columns, size,
checksum) is also written to ``data/results/download_summary.txt``
so reviewers can inspect the acquisition without reading the
gitignored raw parquet.

Any download or checksum error raises an exception — there is NO
synthetic fallback.
"""

import hashlib
import shutil

import pyarrow as pa
import pyarrow.parquet as pq
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

DATASET_ID = "chrisvoncsefalvay/vaers-outcomes"
BATCH_SIZE = 50_000
CHUNK_SIZE = 1024 * 1024

# Output locations (project-relative via llmxive_toolkit.paths)
PARQUET_PATH = paths.data("raw", "vaers_2020_2023.parquet")
CHECKSUMS_PATH = paths.data("checksums.txt")
SUMMARY_PATH = paths.data("results", "download_summary.txt")


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


def _open_streaming_split(dataset_id: str):
    """Open the real dataset as a streaming iterable of batches.

    Prefers the ``train`` split as required by the task; if the
    repository does not expose one, falls back to the first
    available split. Raises on any failure (no synthetic data).
    """
    try:
        ds = load_dataset(dataset_id, split="train", streaming=True)
        log.info("Opened streaming split 'train' of %s", dataset_id)
        return ds, "train"
    except Exception as exc:
        log.warning(
            "Could not open split 'train' directly (%s); listing "
            "available splits", exc,
        )
        dset_dict = load_dataset(dataset_id, streaming=True)
        splits = list(dset_dict.keys())
        if not splits:
            raise RuntimeError(
                f"Dataset {dataset_id} exposes no splits"
            )
        split = splits[0]
        log.info("Falling back to split %r of %s", split, dataset_id)
        return dset_dict[split], split


def download_vaers_dataset(
    dataset_id: str = DATASET_ID,
    dest=PARQUET_PATH,
):
    """Download the real VAERS dataset from Hugging Face to *dest*.

    Uses ``datasets.load_dataset`` (streaming) and writes the full
    real data to a parquet file. Raises on any failure — network,
    dataset missing, empty result, bad content. No synthetic
    fallback is ever performed.

    Returns (dest, row_count, columns, split).
    """
    ds, split = _open_streaming_split(dataset_id)

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")

    writer = None
    n_rows = 0
    columns = None
    try:
        for batch in ds.iter(batch_size=BATCH_SIZE):
            if not batch:
                raise RuntimeError(
                    "Received an empty batch while streaming the "
                    "real dataset; refusing to write an empty file."
                )
            if columns is None:
                columns = list(batch.keys())
            table = pa.Table.from_pydict(
                {k: list(v) for k, v in batch.items()}
            )
            if writer is None:
                writer = pq.ParquetWriter(str(tmp), table.schema)
            writer.write_table(table)
            n_rows += table.num_rows
            if n_rows % 500_000 < BATCH_SIZE:
                log.info("Streamed %d rows so far", n_rows)
    finally:
        if writer is not None:
            writer.close()

    if n_rows == 0 or writer is None:
        raise RuntimeError(
            "The real dataset produced zero rows; refusing to "
            "write an empty parquet file."
        )

    shutil.move(str(tmp), str(dest))

    if not dest.exists() or dest.stat().st_size == 0:
        raise RuntimeError(
            f"Parquet file {dest} was not written or is empty."
        )

    _verify_parquet_magic(dest)

    size_mb = dest.stat().st_size / (1024 * 1024)
    log.info(
        "Wrote %s (%d rows, %.1f MB) from split %r",
        dest, n_rows, size_mb, split,
    )
    return dest, n_rows, columns, split


def _verify_parquet_magic(path) -> None:
    """Verify the file carries the parquet magic bytes ``PAR1``."""
    size = path.stat().st_size
    if size <= 8:
        raise RuntimeError(
            f"Downloaded file {path} is too small to be a parquet "
            f"file ({size} bytes)."
        )
    with open(path, "rb") as f:
        head = f.read(4)
        f.seek(-4, 2)
        tail = f.read(4)
    if head != b"PAR1" or tail != b"PAR1":
        raise RuntimeError(
            f"File {path} does not carry parquet magic bytes "
            f"(head={head!r}, tail={tail!r}); refusing to accept it."
        )


def _write_summary(dest, n_rows, columns, split, checksum) -> None:
    """Write durable acquisition evidence outside gitignored caches."""
    rel = dest.relative_to(paths.root)
    size_bytes = dest.stat().st_size
    lines = [
        "VAERS 2020-2023 dataset acquisition summary (T002)",
        f"source: Hugging Face dataset {DATASET_ID!r} "
        f"(datasets.load_dataset, streaming)",
        f"split: {split}",
        f"file: {rel}",
        f"sha256: {checksum}",
        f"size_bytes: {size_bytes}",
        f"size_mb: {size_bytes / (1024 * 1024):.1f}",
        f"row_count: {n_rows}",
        f"columns ({len(columns)}): {', '.join(columns)}",
    ]
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("Wrote acquisition summary to %s", SUMMARY_PATH)


def main() -> None:
    """Entry point: download, checksum, verify, summarise."""
    log.info("Starting VAERS data download process")
    dest, n_rows, columns, split = download_vaers_dataset()

    try:
        checksum = record_checksum(dest, CHECKSUMS_PATH)
    except Exception as exc:
        log.error("Checksum computation failed for %s: %s", dest, exc)
        raise

    # Verify checksum entry: recompute and compare
    if checksum != sha256_checksum(dest):
        raise RuntimeError("Checksum verification failed for %s" % dest)

    _write_summary(dest, n_rows, columns, split, checksum)

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