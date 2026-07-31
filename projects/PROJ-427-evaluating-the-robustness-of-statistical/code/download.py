"""
download.py
-------------
Implements the dataset download, cleaning, and checksum recording pipeline
for the project.

The public API (as declared in the project specification) includes:
  - load_config
  - download_dataset
  - clean_dataset
  - compute_checksum
  - main

The script is intentionally self‑contained: it can be executed directly
(`python code/download.py`) and will:
  1. Load the dataset list from ``config/datasets.yaml``.
  2. Download each CSV into ``data/raw/`` (skipping any that raise HTTP errors).
  3. Clean each downloaded CSV and write the cleaned version to
     ``data/raw/cleaned/``.
  4. Compute a SHA‑256 checksum for every cleaned file.
  5. Record the mapping ``relative_path: checksum`` in
     ``state/dataset_checksums.yaml`` (creating the ``state`` directory if needed).

All steps log progress and errors via the standard ``logging`` module.
"""

import argparse
import hashlib
import logging
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml

# ----------------------------------------------------------------------
# Configuration loading
# ----------------------------------------------------------------------
def load_config(config_path: Path = Path("config/datasets.yaml")) -> List[Dict[str, Any]]:
    """
    Load the dataset configuration file.

    The expected format is a YAML list where each entry is a mapping with at
    least the keys ``url`` and ``filename``. Example::

        - url: https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data
          filename: iris.csv
          type: numerical

    Returns a list of dictionaries.
    """
    if not config_path.is_file():
        logging.error("Configuration file %s does not exist.", config_path)
        raise FileNotFoundError(f"Configuration file {config_path} not found")
    with config_path.open("r", encoding="utf-8") as f:
        try:
            cfg = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logging.error("Failed to parse %s: %s", config_path, e)
            raise
    if not isinstance(cfg, list):
        raise ValueError(f"Expected a list of datasets in {config_path}")
    return cfg

# ----------------------------------------------------------------------
# Download helper
# ----------------------------------------------------------------------
def download_dataset(entry: Dict[str, Any],
                     raw_dir: Path = Path("data/raw")) -> Path:
    """
    Download a single dataset described by ``entry`` into ``raw_dir``.

    Parameters
    ----------
    entry: dict
        Must contain at least ``url`` and ``filename``.
    raw_dir: Path
        Destination directory for the raw CSV files.

    Returns
    -------
    Path
        Path to the downloaded file.

    Raises
    ------
    urllib.error.HTTPError
        If the HTTP request fails (e.g., 404). The caller should handle this.
    """
    url = entry["url"]
    filename = entry["filename"]
    dest_path = raw_dir / filename

    raw_dir.mkdir(parents=True, exist_ok=True)

    try:
        logging.info("Downloading %s → %s", url, dest_path)
        # urllib.request.urlretrieve will raise an HTTPError for non‑200 responses.
        urllib.request.urlretrieve(url, dest_path)
    except urllib.error.HTTPError as e:
        logging.warning("Failed to download %s (HTTP %s). Skipping.", url, e.code)
        raise
    except Exception as e:
        logging.warning("Unexpected error while downloading %s: %s", url, e)
        raise
    return dest_path

# ----------------------------------------------------------------------
# Cleaning helper
# ----------------------------------------------------------------------
def clean_dataset(raw_path: Path,
                  cleaned_dir: Path = Path("data/raw/cleaned")) -> Path:
    """
    Perform basic cleaning on a raw CSV file.

    Cleaning steps:
      * Read CSV with pandas (let pandas infer types).
      * Replace empty strings with ``NaN``.
      * Coerce numeric columns where possible.
      * Write the cleaned DataFrame to ``cleaned_dir`` preserving the filename.

    Parameters
    ----------
    raw_path: Path
        Path to the raw CSV file.
    cleaned_dir: Path
        Destination directory for cleaned CSV files.

    Returns
    -------
    Path
        Path to the cleaned CSV file.
    """
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = cleaned_dir / raw_path.name

    logging.info("Cleaning %s → %s", raw_path, cleaned_path)

    # pandas will treat empty strings as NaN if we specify na_values.
    df = pd.read_csv(raw_path, na_values=["", " "], keep_default_na=True)

    # Attempt to convert object columns that look numeric.
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except ValueError:
            # Column is genuinely non‑numeric; leave as‑is.
            pass

    df.to_csv(cleaned_path, index=False)
    return cleaned_path

# ----------------------------------------------------------------------
# Checksum helper
# ----------------------------------------------------------------------
def compute_checksum(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path``.

    The file is read in ``chunk_size`` byte blocks to avoid loading large
    files entirely into memory.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum should be computed.
    chunk_size: int, optional
        Number of bytes to read per iteration (default 8192).

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# ----------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------
def record_checksums(cleaned_dir: Path = Path("data/raw/cleaned"),
                    output_yaml: Path = Path("state/dataset_checksums.yaml")) -> None:
    """
    Compute checksums for all files in ``cleaned_dir`` and write them to
    ``output_yaml`` (as a mapping of relative POSIX paths → checksum strings).

    The function creates the ``state`` directory if it does not exist.
    """
    if not cleaned_dir.is_dir():
        logging.error("Cleaned data directory %s does not exist.", cleaned_dir)
        raise FileNotFoundError(f"{cleaned_dir} not found")

    output_yaml.parent.mkdir(parents=True, exist_ok=True)

    checksums: Dict[str, str] = {}
    for file_path in cleaned_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(Path.cwd()).as_posix()
            checksum = compute_checksum(file_path)
            checksums[rel_path] = checksum
            logging.debug("Checksum for %s: %s", rel_path, checksum)

    with output_yaml.open("w", encoding="utf-8") as f:
        yaml.safe_dump(checksums, f, default_flow_style=False)

    logging.info("Recorded %d checksums in %s", len(checksums), output_yaml)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> int:
    """
    Command‑line interface for the download‑clean‑checksum pipeline.

    Usage example::
        python code/download.py --config config/datasets.yaml

    Returns exit code ``0`` on success, non‑zero on failure.
    """
    parser = argparse.ArgumentParser(
        description="Download datasets, clean them, and record SHA‑256 checksums."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/datasets.yaml"),
        help="Path to the YAML configuration listing datasets to download.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    try:
        dataset_entries = load_config(args.config)
    except Exception as e:
        logging.error("Failed to load configuration: %s", e)
        return 1

    # Step 1: download each dataset (skip those that error)
    downloaded_paths: List[Path] = []
    for entry in dataset_entries:
        try:
            downloaded = download_dataset(entry)
            downloaded_paths.append(downloaded)
        except Exception:
            # Error already logged inside download_dataset; continue with next.
            continue

    if not downloaded_paths:
        logging.warning("No datasets were successfully downloaded.")
    else:
        logging.info("Downloaded %d dataset(s).", len(downloaded_paths))

    # Step 2: clean each downloaded file
    cleaned_paths: List[Path] = []
    for raw_path in downloaded_paths:
        try:
            cleaned = clean_dataset(raw_path)
            cleaned_paths.append(cleaned)
        except Exception as e:
            logging.error("Failed to clean %s: %s", raw_path, e)

    if not cleaned_paths:
        logging.warning("No datasets were successfully cleaned.")
    else:
        logging.info("Cleaned %d dataset(s).", len(cleaned_paths))

    # Step 3: compute and record checksums
    try:
        record_checksums()
    except Exception as e:
        logging.error("Failed to record checksums: %s", e)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
