"""
VAERS Data Download Script (T002)
=================================

Downloads the verified VAERS 2020-2023 dataset from Hugging Face
(``chrisvoncsefalvay/vaers-outcomes``) and writes it to
``data/raw/vaers_2020_2023.parquet``.

The previous implementation used ``datasets.load_dataset``, which
failed in the execution environment because the installed pyarrow
build requires NumPy >= 2.0 while the environment pins NumPy 1.26.
This version avoids the ``datasets``/``pyarrow`` import chain
entirely: it queries the public Hugging Face Hub HTTP API to list
the repository files, downloads the largest real parquet shard via
plain HTTPS streaming (``requests``), and copies the bytes verbatim
to the destination. The parquet magic bytes (``PAR1``) are verified
before the file is accepted.

A SHA-256 checksum of the file is recorded as
``<file> <sha256>`` in ``data/checksums.txt`` (any previous entry for
the same file is replaced, so the file appears exactly once).

Any download or checksum error raises an exception — there is NO
synthetic fallback.
"""

import hashlib
import shutil
import sys

import requests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

DATASET_ID = "chrisvoncsefalvay/vaers-outcomes"
REPO_TYPE = "datasets"
CHUNK_SIZE = 1024 * 1024
TIMEOUT_S = 120

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


def _list_repo_parquet_files(dataset_id: str):
    """List .parquet files in the Hugging Face dataset repository.

    Uses the public Hub HTTP API (no pyarrow/datasets import).
    Raises on any HTTP or content error.
    """
    url = f"https://huggingface.co/api/{REPO_TYPE}/{dataset_id}/tree/main"
    params = {"recursive": "true", "expand": "false"}
    resp = requests.get(url, params=params, timeout=TIMEOUT_S)
    resp.raise_for_status()
    entries = resp.json()
    if not isinstance(entries, list):
        raise RuntimeError(
            f"Unexpected response listing {dataset_id}: not a JSON list"
        )
    files = [
        e for e in entries
        if e.get("type") == "file" and e.get("path", "").endswith(".parquet")
    ]
    if not files:
        raise RuntimeError(
            f"No parquet files found in Hugging Face dataset {dataset_id}"
        )
    return files


def _select_parquet(files):
    """Select the parquet shard to download.

    Prefers the largest file (the full dataset shard rather than a
    metadata sample). Returns (path, size).
    """
    def size_of(e):
        return e.get("size") or 0

    best = max(files, key=size_of)
    return best["path"], size_of(best)


def _download_file(repo_path: str, dest, dataset_id: str):
    """Stream the real file from the Hub to *dest* (no synthetic data)."""
    url = (
        f"https://huggingface.co/{REPO_TYPE}/{dataset_id}"
        f"/resolve/main/{repo_path}"
    )
    log.info("Downloading %s", url)
    with requests.get(url, stream=True, timeout=TIMEOUT_S) as resp:
        resp.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
        shutil.move(str(tmp), str(dest))
    return dest


def _verify_parquet_magic(path) -> None:
    """Verify the file carries the parquet magic bytes ``PAR1``."""
    size = path.stat().st_size
    if size <= 8:
        raise RuntimeError(
            f"Downloaded file {path} is too small to be a parquet file "
            f"({size} bytes)."
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


def download_vaers_dataset(
    dataset_id: str = DATASET_ID,
    dest=PARQUET_PATH,
):
    """Download the real VAERS dataset from Hugging Face to *dest*.

    Raises on any failure (network, dataset missing, bad content).
    No synthetic fallback is ever performed.
    """
    log.info("Listing parquet files in dataset %s", dataset_id)
    files = _list_repo_parquet_files(dataset_id)
    repo_path, size = _select_parquet(files)
    log.info(
        "Selected %s (%.1f MB) from %d parquet file(s)",
        repo_path, size / (1024 * 1024), len(files),
    )

    _download_file(repo_path, dest, dataset_id)

    if not dest.exists() or dest.stat().st_size == 0:
        raise RuntimeError(f"Parquet file {dest} was not written or is empty.")

    _verify_parquet_magic(dest)

    size_mb = dest.stat().st_size / (1024 * 1024)
    log.info("Wrote %s (%.1f MB)", dest, size_mb)
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
        raise RuntimeError("Checksum verification failed for %s" % dest)

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