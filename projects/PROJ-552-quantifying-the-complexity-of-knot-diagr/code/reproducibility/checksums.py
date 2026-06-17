"""Checksum recording entry point.

This script is invoked by the run‑book to produce a JSON file containing
SHA‑256 checksums for every file in the ``data`` directory.  The original
implementation referenced ``LogEntry`` without importing it, raising a
``NameError``.  The fix imports the class from ``logs`` and uses it for a
concise summary log entry.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from reproducibility.checksums_recorder import (
    ChecksumEntry,
    compute_sha256,
    get_file_size,
    find_data_files,
    record_checksums,
    write_checksums_json,
)
from reproducibility.logs import LogEntry, get_logger, log_operation


@log_operation
def main() -> None:
    """Compute checksums for all files under ``data/`` and write a JSON report."""
    logger = get_logger()
    data_dir = Path("data")
    if not data_dir.is_dir():
        raise FileNotFoundError("Data directory does not exist; nothing to checksum.")

    files = list(find_data_files(data_dir))
    entries: List[ChecksumEntry] = [record_checksums(p) for p in files]

    checksums_path = data_dir / "checksums.json"
    write_checksums_json(entries, checksums_path)

    # Log a concise summary using the shared LogEntry type.
    summary_entry = LogEntry(
        timestamp=Path().stat().st_mtime,
        operation="checksums",
        input_file=str(data_dir),
        output_file=str(checksums_path),
        parameters={"file_count": len(files)},
        status="success",
        duration_ms=None,
        level="INFO",
        message=f"Recorded checksums for {len(files)} files.",
    )
    # Directly write the summary entry to the same log file.
    with (Path("data") / "logs.jsonl").open("a", encoding="utf-8") as f:
        f.write(summary_entry.to_json() + "\n")
