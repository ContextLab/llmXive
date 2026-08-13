"""
Contract test for checksum generation.

This test verifies that the file ``data/checksums.txt`` exists and that it
contains a checksum entry for every file produced by the GSM8K download
and split process (i.e., every regular file under ``data/gsm8k/``).

The checksum file may be stored either as a JSON mapping
``{ "relative/path/to/file": "sha256hex", ... }`` or as whitespace‑separated
lines ``relative/path/to/file  sha256hex``.  The test supports both formats.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def checksums_path() -> Path:
    """Path to the generated checksums file."""
    return Path("data/checksums.txt")


@pytest.fixture(scope="module")
def data_dir() -> Path:
    """Root directory containing the downloaded GSM8K split files."""
    return Path("data/gsm8k")


def _load_checksums(path: Path) -> dict[str, str]:
    """
    Load the checksum mapping from ``path``.

    Supports two formats:
    1. JSON object mapping relative file paths to SHA‑256 hex strings.
    2. Plain‑text lines ``<relative_path> <sha256>`` (any amount of whitespace).

    Returns:
        dict mapping relative POSIX paths (as strings) to checksum strings.
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Fallback to line‑based format
        checksums: dict[str, str] = {}
        with path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                # Split on whitespace; the last token is the checksum
                parts = line.split()
                if len(parts) < 2:
                    continue
                checksum = parts[-1]
                # Re‑join any spaces that might be part of the filename
                filename = " ".join(parts[:-1])
                checksums[filename] = checksum
        return checksums


def test_checksums_file_exists(checksums_path: Path):
    """The checksums file must be present."""
    assert checksums_path.is_file(), f"Missing checksums file at {checksums_path}"


def test_checksums_cover_all_downloaded_files(checksums_path: Path, data_dir: Path):
    """
    Every regular file under ``data/gsm8k/`` must have an entry in the
    checksums file, and conversely every entry must point to an existing file.
    """
    # Load the checksum mapping
    checksums = _load_checksums(checksums_path)

    # Collect all regular files under the data directory (relative to project root)
    actual_files = {
        p.relative_to(Path(".")).as_posix()
        for p in data_dir.rglob("*")
        if p.is_file()
    }

    # Keys in the checksum mapping are expected to be relative POSIX paths.
    checksum_files = set(checksums.keys())

    # Files that are present but missing a checksum entry
    missing_entries = actual_files - checksum_files
    assert not missing_entries, (
        f"The following downloaded files are missing checksum entries: {sorted(missing_entries)}"
    )

    # Entries that reference non‑existent files
    nonexistent_entries = checksum_files - actual_files
    assert not nonexistent_entries, (
        f"The checksums file contains entries for files that do not exist: {sorted(nonexistent_entries)}"
    )