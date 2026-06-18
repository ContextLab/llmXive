"""
Entry‑point script that records SHA‑256 checksums for all data files.
The script is invoked as part of the end‑to‑end run‑book and writes its
output to ``data/checksums.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

from reproducibility.checksums_recorder import (
    ChecksumEntry,
    find_data_files,
    record_checksums,
    write_checksums_json,
)

def main() -> None:
    """
    Locate data files, compute checksums, and write a JSON manifest.
    """
    data_root = Path("data")
    # Gather common data artefacts; adjust extensions if new types appear.
    files = find_data_files(data_root, extensions=(".csv", ".json", ".txt", ".png", ".md"))
    entries: list[ChecksumEntry] = record_checksums(files)
    out_path = data_root / "checksums.json"
    write_checksums_json(entries, out_path)
    print(f"Checksums written to {out_path}")

if __name__ == "__main__":
    main()
