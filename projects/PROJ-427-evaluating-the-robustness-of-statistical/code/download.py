import argparse
import hashlib
import logging
import os
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Public API (as declared in the project specification)
# ----------------------------------------------------------------------
__all__ = [
    "load_config",
    "download_dataset",
    "clean_dataset",
    "compute_checksum",
    "record_checksums",
    "main",
]


def load_config(config_path: str = "config/datasets.yaml") -> List[Dict]:
    """
    Load the dataset configuration file.

    The configuration file is expected to be a YAML file containing a list of
    dataset entries. Each entry should have at least a ``url`` field; a
    ``filename`` field is optional – if omitted the filename is derived from
    the URL.

    Parameters
    ----------
    config_path: str
        Path to the YAML configuration file.

    Returns
    -------
    List[Dict]
        List of dataset specifications.
    """
    config_file = Path(config_path)
    if not config_file.is_file():
        logger.error("Configuration file %s does not exist.", config_path)
        raise FileNotFoundError(f"Configuration file {config_path} not found.")
    with config_file.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or []
    if not isinstance(config, list):
        logger.error("Configuration file %s must contain a list.", config_path)
        raise ValueError("Configuration file must contain a list of datasets.")
    logger.info("Loaded %d dataset specifications from %s.", len(config), config_path)
    return config


def download_dataset(entry: Dict, raw_dir: Path = Path("data/raw")) -> Path:
    """
    Download a single dataset CSV given its specification.

    Parameters
    ----------
    entry: Dict
        Dictionary with at least a ``url`` key. Optionally a ``filename`` key.
    raw_dir: Path
        Directory where the raw file will be saved.

    Returns
    -------
    Path
        Path to the downloaded file.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)

    url = entry.get("url")
    if not url:
        raise ValueError("Dataset entry must contain a 'url' key.")

    # Derive filename from URL if not explicitly provided
    filename = entry.get("filename") or Path(urllib.parse.urlparse(url).path).name
    if not filename:
        raise ValueError(f"Could not determine filename from URL: {url}")

    dest_path = raw_dir / filename

    # Skip download if file already exists (useful for re‑runs)
    if dest_path.is_file():
        logger.info("File %s already exists, skipping download.", dest_path)
        return dest_path

    logger.info("Downloading %s to %s", url, dest_path)
    try:
        with urllib.request.urlopen(url) as response, dest_path.open("wb") as out_file:
            out_file.write(response.read())
    except urllib.error.HTTPError as e:
        # Gracefully handle 404 and other HTTP errors
        logger.warning("Failed to download %s: %s (HTTP %s). Skipping.", url, e.reason, e.code)
        raise
    except Exception as e:
        logger.error("Unexpected error while downloading %s: %s", url, e)
        raise

    logger.info("Successfully downloaded %s", dest_path)
    return dest_path


def clean_dataset(
    input_path: Path,
    output_path: Path = Path("data/raw/cleaned"),
) -> Path:
    """
    Clean a raw CSV file.

    Cleaning steps:
    * Replace empty strings with NaN.
    * Coerce column types where possible (pandas will infer dtypes).
    * Write the cleaned CSV to the cleaned data directory, preserving the
      original filename.

    Parameters
    ----------
    input_path: Path
        Path to the raw CSV file.
    output_path: Path
        Directory where the cleaned CSV will be written.

    Returns
    -------
    Path
        Path to the cleaned CSV file.
    """
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Cleaning dataset %s", input_path)

    # Read CSV, treat empty strings as NaN
    df = pd.read_csv(input_path, dtype=str, na_values=["", " "], keep_default_na=True)

    # Replace any remaining empty string cells with NaN (pandas already does this,
    # but we keep the step for explicitness)
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    cleaned_file = output_path / input_path.name
    df.to_csv(cleaned_file, index=False)
    logger.info("Cleaned dataset written to %s", cleaned_file)
    return cleaned_file


def compute_checksum(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Parameters
    ----------
    file_path: Path
        Path to the file.
    chunk_size: int
        Number of bytes to read per iteration.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    logger.debug("Checksum for %s: %s", file_path, checksum)
    return checksum


def record_checksums(
    cleaned_dir: Path = Path("data/raw/cleaned"),
    output_yaml: Path = Path("state/dataset_checksums.yaml"),
) -> None:
    """
    Compute SHA‑256 checksums for all cleaned CSV files and write them to a
    YAML file.

    The resulting YAML file maps each filename (relative to the cleaned
    directory) to its checksum.

    Parameters
    ----------
    cleaned_dir: Path
        Directory containing cleaned CSV files.
    output_yaml: Path
        Destination YAML file to store the checksums.
    """
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    output_yaml.parent.mkdir(parents=True, exist_ok=True)

    checksums: Dict[str, str] = {}
    for file_path in cleaned_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".csv":
            checksum = compute_checksum(file_path)
            checksums[file_path.name] = checksum
            logger.info("Recorded checksum for %s", file_path.name)

    with output_yaml.open("w", encoding="utf-8") as f:
        yaml.safe_dump(checksums, f, default_flow_style=False)

    logger.info("All checksums written to %s", output_yaml)


def _process_all_datasets(config_path: str = "config/datasets.yaml") -> None:
    """
    Helper that runs the full download → clean → checksum pipeline.
    """
    # Load configuration
    datasets = load_config(config_path)

    # Process each dataset
    for entry in datasets:
        try:
            raw_file = download_dataset(entry)
            clean_dataset(raw_file)
        except Exception as e:
            # Errors are already logged inside the called functions; continue
            logger.warning("Skipping dataset due to error: %s", e)
            continue

    # After all cleaning is done, compute checksums
    record_checksums()


def main(argv: List[str] = None) -> None:
    """
    Entry‑point for the script. Supports an optional ``--config`` argument
    to point to a custom datasets configuration file.
    """
    parser = argparse.ArgumentParser(
        description="Download, clean, and checksum UCI datasets."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/datasets.yaml",
        help="Path to the datasets YAML configuration file.",
    )
    args = parser.parse_args(argv)

    _process_all_datasets(config_path=args.config)


if __name__ == "__main__":
    main()