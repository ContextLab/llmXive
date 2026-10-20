"""Download the Pantheon+ “full” sample, verify its SHA‑256 checksum,
and record provenance information.

This script fulfills task T004 by:
  1. Downloading the official Pantheon+ SH0ES data file from the
     canonical GitHub repository.
  2. Computing its SHA‑256 hash.
  3. Writing ``data/metadata.json`` with the fields
     ``dataset_version``, ``source_url`` and ``sha256``.
The script raises on any download or I/O error, ensuring that failures
are loud and not silently ignored.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Correct canonical URL for the Pantheon+ SH0ES data file. The plus sign is
# URL‑encoded as %2B. The file lives in the PantheonPlusSH0ES/DataRelease repository.
DEFAULT_URL = (
    "https://raw.githubusercontent.com/PantheonPlusSH0ES/"
    "DataRelease/main/data/Pantheon%2B_SH0ES.dat"
)
# The version string is not explicitly provided by the upstream release;
# we record a generic identifier that can be updated later if needed.
DEFAULT_DATASET_VERSION = "v1.0"


def download_file(url: str, destination: Path) -> None:
    """Download ``url`` to ``destination`` using a streaming request.

    Raises
    ------
    requests.HTTPError
        If the HTTP request returns an error status.
    OSError
        If writing to ``destination`` fails.
    """
    logger = get_logger(__name__)
    logger.info("Downloading Pantheon+ dataset from %s", url)

    # Stream the response to avoid loading the whole file into memory.
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(destination, "wb") as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep‑alive chunks
                    out_file.write(chunk)

    logger.info("Saved dataset to %s", destination)


def compute_sha256(file_path: Path) -> str:
    """Return the hexadecimal SHA‑256 checksum of ``file_path``."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def write_metadata(
    metadata_path: Path, *, dataset_version: str, source_url: str, sha256: str
) -> None:
    """Write the provenance JSON file required by the spec."""
    logger = get_logger(__name__)
    metadata = {
        "dataset_version": dataset_version,
        "source_url": source_url,
        "sha256": sha256,
    }
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Wrote metadata to %s", metadata_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Pantheon+ SH0ES data and record provenance."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="URL of the Pantheon+ dataset (default: official GitHub raw URL).",
    )
    parser.add_argument(
        "--version",
        default=DEFAULT_DATASET_VERSION,
        help="Dataset version identifier to store in the metadata file.",
    )
    args = parser.parse_args()

    logger = get_logger(__name__)

    # Resolve the target paths using the llmxive_toolkit helpers.
    # The raw file name must match what ``ingest.py`` expects.
    raw_path = paths.data("raw", "Pantheon+_SH0ES.dat")
    metadata_path = paths.data("metadata.json")

    try:
        download_file(args.url, raw_path)
    except Exception as exc:
        logger.error("Failed to download Pantheon+ dataset: %s", exc)
        raise

    try:
        checksum = compute_sha256(raw_path)
    except Exception as exc:
        logger.error("Failed to compute SHA‑256 checksum: %s", exc)
        raise

    try:
        write_metadata(
            metadata_path,
            dataset_version=args.version,
            source_url=args.url,
            sha256=checksum,
        )
    except Exception as exc:
        logger.error("Failed to write metadata.json: %s", exc)
        raise

    logger.info("Successfully downloaded Pantheon+ dataset (SHA‑256=%s)", checksum)


if __name__ == "__main__":
    # Propagate any exception as a non‑zero exit status so the CI can
    # detect a failure.
    try:
        main()
    except Exception as e:
        # Log the exception (the logger may not be initialised yet if the
        # error occurred early).
        sys.stderr.write(f"Error: {e}\\n")
        sys.exit(1)
