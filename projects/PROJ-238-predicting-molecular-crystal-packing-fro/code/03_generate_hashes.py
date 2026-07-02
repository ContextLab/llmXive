"""
Generate SHA-256 checksums for raw CIF files and all derived CSV/JSON artifacts.

The script scans the repository for:
  * *.cif files under ``data/raw``
  * *.csv files under ``data`` (any sub‑directory)
  * *.json files under ``data`` and ``results`` (any sub‑directory)

For each discovered file the SHA‑256 hash is computed and written to
``state/projects/PROJ-238-predicting-molecular-crystal-packing-fro/artifact_hashes``.
The output format mirrors the classic ``sha256sum`` layout:

    <hash>  <relative_path>

The script is intended to be run from the repository root:

    python code/03_generate_hashes.py

It creates any missing parent directories automatically.
"""

import hashlib
import os
from pathlib import Path
from typing import Iterable, List

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
PROJECT_NAME = "PROJ-238-predicting-molecular-crystal-packing-fro"
OUTPUT_RELATIVE_PATH = Path("state") / "projects" / PROJECT_NAME / "artifact_hashes"

# Directories to search (relative to repository root)
SEARCH_ROOT = Path(__file__).resolve().parents[1]  # repository root (two levels up from code/)
DATA_ROOT = SEARCH_ROOT / "data"
RESULTS_ROOT = SEARCH_ROOT / "results"

# File extensions we care about
TARGET_EXTENSIONS = {".cif", ".csv", ".json"}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def iter_target_files(root: Path) -> Iterable[Path]:
    """
    Yield all files under *root* (recursively) whose suffix is in TARGET_EXTENSIONS.
    """
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in TARGET_EXTENSIONS:
            yield path

def compute_sha256(file_path: Path, block_size: int = 65536) -> str:
    """
    Compute the SHA‑256 hash of *file_path*.

    Parameters
    ----------
    file_path: Path
        Path to the file.
    block_size: int, optional
        Number of bytes to read per iteration.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()

def collect_hashes() -> List[str]:
    """
    Walk the relevant directories, compute hashes and return a list of formatted lines.
    """
    lines: List[str] = []

    # 1. Raw CIF files (usually under data/raw)
    raw_cif_dir = DATA_ROOT / "raw"
    if raw_cif_dir.is_dir():
        for file_path in iter_target_files(raw_cif_dir):
            rel_path = file_path.relative_to(SEARCH_ROOT).as_posix()
            hash_val = compute_sha256(file_path)
            lines.append(f"{hash_val}  {rel_path}")

    # 2. All CSV/JSON artifacts under data
    for file_path in iter_target_files(DATA_ROOT):
        # Skip CIFs already handled above
        if file_path.suffix.lower() == ".cif":
            continue
        rel_path = file_path.relative_to(SEARCH_ROOT).as_posix()
        hash_val = compute_sha256(file_path)
        lines.append(f"{hash_val}  {rel_path}")

    # 3. All CSV/JSON artifacts under results
    if RESULTS_ROOT.is_dir():
        for file_path in iter_target_files(RESULTS_ROOT):
            rel_path = file_path.relative_to(SEARCH_ROOT).as_posix()
            hash_val = compute_sha256(file_path)
            lines.append(f"{hash_val}  {rel_path}")

    # Sort for reproducibility
    lines.sort()
    return lines

def write_hash_file(lines: List[str]) -> None:
    """
    Write *lines* to the output file, creating parent directories if necessary.
    """
    output_path = SEARCH_ROOT / OUTPUT_RELATIVE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Compute hashes and write them to the configured output location.
    """
    lines = collect_hashes()
    write_hash_file(lines)
    print(f"Generated {len(lines)} checksum entries at {OUTPUT_RELATIVE_PATH}")

if __name__ == "__main__":
    main()
