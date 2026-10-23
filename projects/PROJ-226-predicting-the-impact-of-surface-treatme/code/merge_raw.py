"""
merge_raw.py

This script merges the verified raw CSV datasets produced by T001 into a single
unified CSV file. It adds a ``source`` column indicating the origin of each
record, writes the merged dataset to ``data/raw/adhesion_raw.csv`` and updates
the SHA‑256 checksum manifest ``data/raw/checksums.txt``.
"""

import hashlib
import logging
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger

# Initialise logger
log: logging.Logger = get_logger(__name__)

def _list_raw_csv_files() -> list[Path]:
    """
    Return a list of raw CSV files in the ``data/raw`` directory,
    excluding any previously generated ``adhesion_raw.csv`` and the checksum file.
    """
    raw_dir = paths.data("raw")
    csv_files = [
        p
        for p in raw_dir.glob("*.csv")
        if p.name not in {"adhesion_raw.csv"} and p.is_file()
    ]
    if not csv_files:
        raise FileNotFoundError(
            f"No raw CSV files found in {raw_dir}. Expected files such as "
            "'nist.csv', 'zenodo.csv', 'materials_project.csv'."
        )
    return csv_files

def _read_and_tag(csv_path: Path) -> pd.DataFrame:
    """
    Read a CSV and add a ``source`` column derived from the file stem.
    """
    log.info("Reading raw file %s", csv_path)
    df = pd.read_csv(csv_path)
    source_name = csv_path.stem  # e.g. 'nist' from 'nist.csv'
    df["source"] = source_name
    return df

def _write_merged_dataframe(df: pd.DataFrame) -> Path:
    """
    Write the merged dataframe to ``data/raw/adhesion_raw.csv``.
    """
    out_path = paths.data("raw", "adhesion_raw.csv")
    log.info("Writing merged dataset to %s", out_path)
    df.to_csv(out_path, index=False)
    return out_path

def _compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path``.
    """
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def _update_checksums_file(target_path: Path, checksum: str) -> None:
    """
    Ensure ``checksums.txt`` contains an entry for ``target_path`` with the
    supplied ``checksum``. Existing entry for the same filename is replaced.
    """
    checksums_path = paths.data("raw", "checksums.txt")
    entry_line = f"{checksum}  {target_path.name}\n"

    # Read existing lines if the file already exists
    if checksums_path.is_file():
        with checksums_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        # Filter out any line that refers to the same file name
        lines = [ln for ln in lines if not ln.strip().endswith(target_path.name)]
    else:
        lines = []

    # Append the new entry
    lines.append(entry_line)

    # Write back the manifest
    with checksums_path.open("w", encoding="utf-8") as f:
        f.writelines(lines)

    log.info("Updated checksum manifest at %s", checksums_path)

def main() -> None:
    """
    Entry point for the merge script.

    Steps:
    1. Locate the raw CSV files produced by T001.
    2. Read each file, tag rows with a ``source`` column.
    3. Concatenate all dataframes.
    4. Write the merged CSV.
    5. Compute its SHA‑256 checksum and update ``checksums.txt``.
    """
    log.info("Starting merge of raw datasets")

    # 1. Locate raw CSV files
    raw_files = _list_raw_csv_files()
    log.debug("Found raw CSV files: %s", [p.name for p in raw_files])

    # 2. Read and tag each file
    dfs = [_read_and_tag(p) for p in raw_files]

    # 3. Concatenate
    merged_df = pd.concat(dfs, ignore_index=True)
    if merged_df.empty:
        raise ValueError("Merged dataframe is empty after concatenation.")

    # 4. Write merged CSV
    merged_path = _write_merged_dataframe(merged_df)

    # 5. Compute checksum and update manifest
    checksum = _compute_sha256(merged_path)
    _update_checksums_file(merged_path, checksum)

    log.info(
        "Merge completed successfully. %d records written to %s",
        len(merged_df),
        merged_path,
    )

if __name__ == "__main__":
    main()
