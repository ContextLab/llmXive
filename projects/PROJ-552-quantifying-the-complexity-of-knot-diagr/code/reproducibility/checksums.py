"""
Reproducibility checksums utility.

This module scans the project's ``data`` directory, computes SHA‑256 checksums
for every file it contains (recursively), and writes three artefacts:

1. ``data/checksums.json`` – a JSON list of checksum entries.
2. ``data/checksums.csv``  – a CSV representation of the same data.
3. ``docs/reproducibility/checksums.md`` – a human‑readable markdown
   document summarising the checksums in a table.

The implementation deliberately avoids the project's ``ReproducibilityLogger``
(which historically did not expose an ``info`` method) and instead uses the
generic ``log_operation`` decorator for consistency with the rest of the
code‑base.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from reproducibility.logs import log_operation, get_logger

@dataclass
class ChecksumEntry:
    """A single checksum record."""
    file_path: str          # Path relative to the repository root
    sha256: str
    size_bytes: int
    recorded_at: str        # ISO‑8601 timestamp

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of *file_path*."""
    import hashlib

    hash_sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def get_file_size(file_path: Path) -> int:
    """Return the size of *file_path* in bytes."""
    return file_path.stat().st_size

def find_data_files(base_dir: Path) -> List[Path]:
    """
    Recursively locate all files under *base_dir* (the project's ``data`` folder).

    Directories themselves are ignored; only regular files are returned.
    """
    return [p for p in base_dir.rglob("*") if p.is_file()]

def record_checksums(files: List[Path], repo_root: Path) -> List[ChecksumEntry]:
    """
    Compute checksums for *files* and return a list of :class:`ChecksumEntry`.

    ``repo_root`` is used to store file paths relative to the repository root.
    """
    entries: List[ChecksumEntry] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for file_path in files:
        rel_path = str(file_path.relative_to(repo_root))
        checksum = compute_sha256(file_path)
        size = get_file_size(file_path)
        entries.append(
            ChecksumEntry(
                file_path=rel_path,
                sha256=checksum,
                size_bytes=size,
                recorded_at=now_iso,
            )
        )
    return entries

def write_checksums_json(entries: List[ChecksumEntry], output_path: Path) -> None:
    """Write *entries* as JSON to *output_path*."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(e) for e in entries], f, indent=2)

def write_checksums_csv(entries: List[ChecksumEntry], output_path: Path) -> None:
    """Write *entries* as CSV to *output_path*."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["file_path", "sha256", "size_bytes", "recorded_at"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            writer.writerow(asdict(entry))

def write_checksums_markdown(entries: List[ChecksumEntry], output_path: Path) -> None:
    """
    Produce a markdown table documenting the checksums.

    The table contains columns: *File*, *SHA‑256*, *Size (bytes)*,
    *Recorded at*.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("# Data Files Checksums\n\n")
        f.write(
            "| File | SHA‑256 | Size (bytes) | Recorded at |\n"
            "|------|---------|--------------|-------------|\n"
        )
        for entry in entries:
            f.write(
                f"| `{entry.file_path}` | `{entry.sha256}` | {entry.size_bytes} | {entry.recorded_at} |\n"
            )
        f.write("\n*Generated on {}*\n".format(datetime.now(timezone.utc).isoformat()))

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
@log_operation(
    operation="checksum_generation",
    input_file="data/",
    output_file="data/checksums.json, data/checksums.csv, docs/reproducibility/checksums.md",
)
def main() -> None:
    """
    Compute and persist checksums for every file under the project's ``data``
    directory.

    The function:
    1. Discovers all data files.
    2. Records checksum information.
    3. Writes JSON, CSV, and markdown artefacts.
    """
    logger = get_logger()

    # Resolve repository root (two levels up from this file)
    repo_root = Path(__file__).resolve().parents[2]

    data_dir = repo_root / "data"
    if not data_dir.is_dir():
        logger.log("error", f"Data directory not found: {data_dir}")
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    logger.log("info", f"Scanning data directory: {data_dir}")

    files = find_data_files(data_dir)
    logger.log("info", f"Found {len(files)} data files to checksum.")

    entries = record_checksums(files, repo_root)

    # Write artefacts
    json_path = data_dir / "checksums.json"
    csv_path = data_dir / "checksums.csv"
    md_path = repo_root / "docs" / "reproducibility" / "checksums.md"

    write_checksums_json(entries, json_path)
    logger.log("info", f"Wrote JSON checksums to {json_path}")

    write_checksums_csv(entries, csv_path)
    logger.log("info", f"Wrote CSV checksums to {csv_path}")

    write_checksums_markdown(entries, md_path)
    logger.log("info", f"Wrote markdown documentation to {md_path}")

    logger.log("info", "Checksum generation completed successfully.")

if __name__ == "__main__":
    main()
