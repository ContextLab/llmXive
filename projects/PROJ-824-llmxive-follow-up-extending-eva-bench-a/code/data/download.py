"""
Data download module for fetching the EVA-Bench dataset.

Downloads the dataset archive from the canonical public HuggingFace URL,
extracts the JSONL metadata and WAV files into ``data/raw/``, and records
SHA-256 checksums for every extracted file in ``data/checksums.json``.

Fail-fast behaviour (task T004): any download failure, HTTP error, or
checksum mismatch aborts the script with a clear error and a non-zero
exit status. There is NO synthetic or mock fallback.
"""
import hashlib
import json
import os
import sys
import shutil
import tarfile
import zipfile
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Make sibling packages importable when run as `python code/data/download.py`
_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

# Import error handling utilities
from data.error_handler import (
    DataCorruptionError,
    DownloadFailureError,
    verify_file_integrity,
    handle_download_failure,
)
from config import DATA_DIR, RAW_DATA_DIR, DATASET_URL, DATASET_CHECKSUMS, ensure_directories

# Configure logging
logger = logging.getLogger("llmxive.download")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2")
AUDIO_SUFFIXES = (".wav", ".flac", ".mp3")


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_existing_checksums(checksum_file: Path) -> Dict[str, str]:
    """Load existing checksums from a JSON file.

    Supports both a flat ``{relpath: hash}`` mapping and the
    ``{"files": {relpath: hash}}`` wrapper format.
    """
    if not checksum_file.exists():
        return {}
    try:
        with open(checksum_file, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse checksum file {checksum_file}: {e}")
        return {}
    if isinstance(data, dict) and isinstance(data.get("files"), dict):
        return {str(k): str(v) for k, v in data["files"].items()}
    if isinstance(data, dict):
        return {str(k): str(v) for k, v in data.items()}
    return {}


def save_checksums(checksums: Dict[str, str], checksum_file: Path) -> None:
    """Save checksums to a JSON file (one entry per extracted file)."""
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {"files": dict(sorted(checksums.items()))}
    with open(checksum_file, "w") as f:
        json.dump(payload, f, indent=2)
    logger.info(f"Wrote {len(checksums)} checksums to {checksum_file}")


def verify_downloaded_files(download_dir: Path, checksums: Dict[str, str]) -> List[str]:
    """
    Verifies all downloaded files against their checksums.
    Returns a list of files with mismatches (empty if all pass).
    """
    mismatches = []
    for filename, expected_hash in checksums.items():
        file_path = download_dir / filename
        if not file_path.exists():
            logger.warning(f"File missing during verification: {file_path}")
            mismatches.append(filename)
            continue

        try:
            verify_file_integrity(file_path, expected_hash)
        except (DataCorruptionError, FileNotFoundError):
            mismatches.append(filename)
    return mismatches


def download_dataset(url: str, dest_dir: Path, filename: str) -> Path:
    """
    Downloads a dataset file from a URL.
    Implements fail-fast on download failure.

    Args:
        url: Source URL.
        dest_dir: Destination directory.
        filename: Name of the file to save as.

    Returns:
        Path to the downloaded file.

    Raises:
        DownloadFailureError: If download fails.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    temp_path = dest_dir / f"{filename}.tmp"

    logger.info(f"Downloading {filename} from {url}...")

    try:
        import requests
        with requests.get(url, stream=True, timeout=300) as r:
            r.raise_for_status()
            content_type = r.headers.get("content-type", "")
            if "text/html" in content_type:
                # HuggingFace serves an HTML page instead of the asset
                # when the repository/file does not exist.
                raise DownloadFailureError(
                    f"URL {url} returned HTML (content-type={content_type}); "
                    "the dataset file does not exist at this URL."
                )
            total = int(r.headers.get('content-length', 0))

            with open(temp_path, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            percent = (downloaded / total) * 100
                            sys.stdout.write(f"\rProgress: {percent:.1f}%")
                            sys.stdout.flush()
        sys.stdout.write("\n")

        if temp_path.stat().st_size == 0:
            raise DownloadFailureError(f"Downloaded file {filename} is empty.")

        # Rename temp to final
        shutil.move(str(temp_path), str(dest_path))
        logger.info(f"Download complete: {dest_path}")
        return dest_path

    except Exception as e:
        # Cleanup partial download
        if temp_path.exists():
            temp_path.unlink()
        if not isinstance(e, DownloadFailureError):
            handle_download_failure(e, 0, 0)
            raise DownloadFailureError(f"Failed to download {url}: {e}") from e
        raise


def extract_archive(archive_path: Path, dest_dir: Path) -> List[Path]:
    """Extract a zip/tar archive into dest_dir and return extracted file paths.

    Raises DataCorruptionError if the archive is not a valid archive.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = archive_path.name.lower()
    extracted: List[Path] = []
    if name.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as zf:
            bad = zf.testzip()
            if bad is not None:
                raise DataCorruptionError(f"Corrupt member '{bad}' in {archive_path}")
            zf.extractall(dest_dir)
            extracted = [dest_dir / info.filename for info in zf.infolist() if not info.is_dir()]
    elif name.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2")):
        with tarfile.open(archive_path) as tf:
            tf.extractall(dest_dir)
            extracted = [
                dest_dir / m.name for m in tf.getmembers()
                if m.isfile() and ".." not in m.name
            ]
    else:
        raise DataCorruptionError(
            f"Unsupported archive format for {archive_path}; "
            "expected one of {ARCHIVE_SUFFIXES}"
        )
    return [p for p in extracted if p.exists()]


def generate_raw_checksums(raw_dir: Path) -> Dict[str, str]:
    """Compute SHA-256 for every file under raw_dir (recursive),
    keyed by path relative to raw_dir."""
    checksums: Dict[str, str] = {}
    for path in sorted(raw_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(raw_dir).as_posix()
            checksums[rel] = calculate_sha256(path)
    return checksums


def validate_extracted_dataset(raw_dir: Path) -> None:
    """Fail fast if the extracted dataset lacks JSONL metadata or audio.

    Raises DataCorruptionError with a clear message otherwise.
    """
    jsonl_files = [p for p in raw_dir.rglob("*.jsonl")]
    audio_files = [p for p in raw_dir.rglob("*") if p.suffix.lower() in AUDIO_SUFFIXES]
    if not jsonl_files:
        raise DataCorruptionError(
            f"No JSONL metadata files found in {raw_dir}; the dataset at "
            f"{DATASET_URL} does not contain the expected metadata."
        )
    if not audio_files:
        raise DataCorruptionError(
            f"No audio (WAV) files found in {raw_dir}; the dataset at "
            f"{DATASET_URL} does not provide pre-recorded audio. "
            "Per the plan's research constraint, the pipeline fails fast "
            "rather than falling back to synthetic audio."
        )
    logger.info(
        f"Dataset validation OK: {len(jsonl_files)} JSONL file(s), "
        f"{len(audio_files)} audio file(s) in {raw_dir}"
    )


def main() -> None:
    """
    Main entry point for downloading and verifying the EVA-Bench dataset.
    """
    logger.info("Starting EVA-Bench dataset download process.")

    ensure_directories()
    raw_dir = RAW_DATA_DIR
    raw_dir.mkdir(parents=True, exist_ok=True)
    checksum_file = DATA_DIR / "checksums.json"
    archive_name = DATASET_URL.rstrip("/").split("/")[-1] or "eva_bench_dataset.zip"
    archive_path = raw_dir / archive_name

    # 1. Download the archive (fail-fast, no fallback).
    try:
        download_dataset(DATASET_URL, raw_dir, archive_name)
    except DownloadFailureError as e:
        logger.critical(f"DOWNLOAD FAILED: {e}")
        logger.critical(
            "No fallback data source is permitted. Aborting with a "
            "non-zero exit status (task T004 fail-fast requirement)."
        )
        sys.exit(2)

    # 2. Extract JSONL metadata and WAV files into data/raw/.
    try:
        if archive_name.lower().endswith(ARCHIVE_SUFFIXES):
            logger.info(f"Extracting {archive_path} into {raw_dir} ...")
            extract_archive(archive_path, raw_dir)
            archive_path.unlink()  # keep only extracted contents
        else:
            # Single-file dataset (e.g. bare JSONL): keep it in data/raw/.
            logger.info(f"Downloaded single-file dataset: {archive_path}")
    except DataCorruptionError as e:
        logger.critical(f"EXTRACTION/CORRUPTION ERROR: {e}")
        sys.exit(3)

    # 3. Validate the extracted contents (JSONL + audio must exist).
    try:
        validate_extracted_dataset(raw_dir)
    except DataCorruptionError as e:
        logger.critical(f"DATASET VALIDATION FAILED: {e}")
        sys.exit(4)

    # 4. Compute and record SHA-256 checksums for every file.
    checksums = generate_raw_checksums(raw_dir)
    if not checksums:
        logger.critical("No files found in data/raw/ after extraction; aborting.")
        sys.exit(5)
    # Merge any upstream-pinned hashes (authoritative if provided).
    for rel, pinned in DATASET_CHECKSUMS.items():
        actual = checksums.get(rel)
        if actual is not None and actual.lower() != pinned.lower():
            logger.critical(
                f"Checksum mismatch for {rel}: expected {pinned}, got {actual}"
            )
            sys.exit(6)
    save_checksums(checksums, checksum_file)

    # 5. Round-trip verification of every recorded checksum.
    recorded = load_existing_checksums(checksum_file)
    mismatches = verify_downloaded_files(raw_dir, recorded)
    if mismatches:
        logger.critical(
            f"Corruption detected in {len(mismatches)} files: {mismatches}"
        )
        sys.exit(7)

    logger.info(
        "All files verified successfully. Dataset ready in "
        f"{raw_dir} with checksums in {checksum_file}"
    )


if __name__ == "__main__":
    main()