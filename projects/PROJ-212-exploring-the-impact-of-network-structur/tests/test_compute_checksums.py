"""
Test that the ``compute_checksums`` script creates a non‑empty checksums file
and that the file contains a valid SHA‑256 hash for each file in ``data/raw/``.
"""

import re
from pathlib import Path
from llmxive_toolkit import paths


def test_checksums_file_exists():
    """The script should have produced ``data/checksums.txt``."""
    checksum_file = paths.data("checksums.txt")
    assert checksum_file.is_file(), "checksums.txt was not created"


def test_checksum_format():
    """
    Each line must match the pattern:
    <64‑hex‑digits><two spaces><relative path>
    """
    checksum_file = paths.data("checksums.txt")
    pattern = re.compile(r"^[a-f0-9]{64}  .+$")

    with checksum_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            assert pattern.match(line), f"Invalid checksum line: {line}"


def test_all_raw_files_have_entries():
    """
    Verify that every file under ``data/raw/`` appears exactly once in the
    checksum manifest.
    """
    raw_dir = paths.data("raw")
    checksum_file = paths.data("checksums.txt")

    # Build a set of relative paths from the checksum file
    listed_paths = set()
    with checksum_file.open("r", encoding="utf-8") as f:
        for line in f:
            _, rel_path = line.strip().split("  ", 1)
            listed_paths.add(Path(rel_path))

    # Collect actual raw file paths
    actual_paths = {p.relative_to(Path.cwd()) for p in raw_dir.rglob("*") if p.is_file()}

    assert actual_paths == listed_paths, (
        f"Checksum manifest missing entries or contains extra entries.\n"
        f"Missing: {actual_paths - listed_paths}\\n"
        f"Extra: {listed_paths - actual_paths}"
    )