"""
Dataset acquisition script.

This script reads a YAML file (``datasets/sources.yaml``) that lists URLs for
external datasets, downloads each file into ``data/raw/``, computes its
SHA‑256 checksum and records the checksum in ``datasets/metadata.yaml``.

The format of ``sources.yaml`` can be either:

1. A mapping of ``filename: url`` pairs, e.g.:

    my_dataset.csv: https://example.com/data/my_dataset.csv

2. A list of dictionaries with ``filename`` and ``url`` keys, e.g.:

    - filename: my_dataset.csv
      url: https://example.com/data/my_dataset.csv

The script is idempotent – if a file already exists and its checksum matches
the recorded value, the download is skipped.
"""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path
from typing import Dict, List, Mapping, Tuple, Union

import yaml

from logging.pipeline_logger import get_logger
from data_acquisition.download_agency_scale import compute_sha256, download_file

logger = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def _load_sources(sources_path: Path) -> List[Tuple[str, str]]:
    """
    Load the dataset source definitions.

    Parameters
    ----------
    sources_path: Path
        Path to the ``sources.yaml`` file.

    Returns
    ----------
    List[Tuple[str, str]]
        A list of (filename, url) tuples.
    """
    if not sources_path.is_file():
        raise FileNotFoundError(f"Sources file not found: {sources_path}")

    with sources_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Accept both dict and list representations
    if isinstance(raw, Mapping):
        return [(str(k), str(v)) for k, v in raw.items()]
    elif isinstance(raw, list):
        entries = []
        for entry in raw:
            if not isinstance(entry, Mapping):
                raise ValueError(
                    f"Invalid entry in sources.yaml (expected mapping): {entry}"
                )
            filename = entry.get("filename")
            url = entry.get("url")
            if not filename or not url:
                raise ValueError(
                    f"Each entry must contain 'filename' and 'url': {entry}"
                )
            entries.append((str(filename), str(url)))
        return entries
    else:
        raise ValueError(
            f"Unsupported structure in sources.yaml: {type(raw).__name__}"
        )

def _load_metadata(metadata_path: Path) -> Dict[str, str]:
    """
    Load existing checksum metadata.

    Returns an empty dict if the file does not exist.
    """
    if not metadata_path.is_file():
        return {}
    with metadata_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, Mapping):
        raise ValueError("metadata.yaml must contain a mapping of filename to checksum")
    return {str(k): str(v) for k, v in data.items()}

def _save_metadata(metadata_path: Path, metadata: Mapping[str, str]) -> None:
    """
    Persist checksum metadata to ``metadata.yaml``.
    """
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(dict(metadata), f, sort_keys=True)

# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Execute the dataset acquisition pipeline.

    Steps:
    1. Load source definitions.
    2. Ensure ``data/raw`` exists.
    3. For each source:
       a. Download the file (skip if already present with matching checksum).
       b. Compute its SHA‑256 checksum.
    4. Write/Update ``datasets/metadata.yaml`` with the computed checksums.
    """
    project_root = Path(__file__).resolve().parents[2]

    sources_path = project_root / "datasets" / "sources.yaml"
    metadata_path = project_root / "datasets" / "metadata.yaml"
    raw_dir = project_root / "data" / "raw"

    logger.info("Starting dataset acquisition")
    logger.debug(f"Sources file: {sources_path}")
    logger.debug(f"Metadata file: {metadata_path}")
    logger.debug(f"Raw data directory: {raw_dir}")

    sources = _load_sources(sources_path)
    logger.info(f"Found {len(sources)} dataset source(s)")

    raw_dir.mkdir(parents=True, exist_ok=True)

    existing_metadata = _load_metadata(metadata_path)

    updated_metadata: Dict[str, str] = {}

    for filename, url in sources:
        target_path = raw_dir / filename
        logger.info(f"Processing {filename} from {url}")

        # Download if the file does not exist or its checksum differs
        need_download = True
        if target_path.is_file():
            current_checksum = compute_sha256(target_path)
            recorded_checksum = existing_metadata.get(filename)
            if recorded_checksum and current_checksum == recorded_checksum:
                logger.info(f"File {filename} already present with matching checksum; skipping download")
                need_download = False
            else:
                logger.info(f"Existing file {filename} checksum mismatch or not recorded; re‑downloading")

        if need_download:
            try:
                download_file(url, target_path)
            except Exception as exc:
                logger.error(f"Failed to download {url} -> {target_path}: {exc}")
                raise

        # Compute (or recompute) checksum
        checksum = compute_sha256(target_path)
        logger.debug(f"Checksum for {filename}: {checksum}")
        updated_metadata[filename] = checksum

    # Merge with any previously stored entries that were not part of the current sources
    for k, v in existing_metadata.items():
        if k not in updated_metadata:
            updated_metadata[k] = v

    _save_metadata(metadata_path, updated_metadata)
    logger.info(f"Metadata written to {metadata_path}")

if __name__ == "__main__":
    main()