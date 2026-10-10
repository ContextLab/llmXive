"""
Provenance‑metadata utilities for the HEA pipeline.

The ``write_metadata_entry`` function appends a single provenance record
to ``data/source_metadata.yaml`` while ensuring the file conforms to the
JSON‑Schema defined in ``contracts/metadata.schema.yaml``.

The ``check_and_update_provenance`` function can be called before a
fetch operation; it compares the stored checksum with the checksum of the
existing raw file and, if they differ, triggers a re‑download of the
affected source.
"""

import json
import logging
import os
from pathlib import Path
from datetime import datetime
import hashlib

import yaml
from jsonschema import validate, ValidationError as JsonSchemaError

logger = logging.getLogger(__name__)

METADATA_SCHEMA_PATH = Path("contracts/metadata.schema.yaml")
METADATA_OUTPUT_PATH = Path("data/source_metadata.yaml")


def _load_schema() -> dict:
    """Load the JSON‑Schema for source metadata."""
    if not METADATA_SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"Metadata schema not found at {METADATA_SCHEMA_PATH}")
    with METADATA_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _validate_metadata(metadata: dict) -> None:
    """Validate ``metadata`` against the schema; raise if invalid."""
    schema = _load_schema()
    try:
        validate(instance=metadata, schema=schema)
    except JsonSchemaError as exc:
        logger.error("Metadata validation error: %s", exc)
        raise


def write_metadata_entry(metadata: dict) -> None:
    """
    Write a single provenance entry to ``data/source_metadata.yaml``.

    The file stores a **list** of metadata objects (one per data source).
    If the file already exists, the new entry is appended; otherwise a new
    list is created.

    Parameters
    ----------
    metadata
        Dictionary adhering to ``contracts/metadata.schema.yaml``.
    """
    _validate_metadata(metadata)

    # Load existing entries if present
    if METADATA_OUTPUT_PATH.is_file():
        with METADATA_OUTPUT_PATH.open("r", encoding="utf-8") as f:
            existing = yaml.safe_load(f) or []
        if not isinstance(existing, list):
            # Preserve backward compatibility – treat a single dict as a list
            existing = [existing]
    else:
        existing = []

    # Replace any existing entry with the same ``source_name`` to keep the file
    # up‑to‑date (e.g. after a re‑download).
    existing = [
        entry for entry in existing if entry.get("source_name") != metadata.get("source_name")
    ]
    existing.append(metadata)

    # Write back
    with METADATA_OUTPUT_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(existing, f, default_flow_style=False, sort_keys=False)

    logger.info(
        "Provenance metadata for source '%s' written to %s",
        metadata.get("source_name"),
        METADATA_OUTPUT_PATH,
    )


def _compute_checksum(file_path: Path) -> str:
    """Return SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def check_and_update_provenance(
    source_name: str,
    raw_file_path: Path,
    query_parameters: dict,
    api_version: str = "unknown",
) -> None:
    """
    Verify the stored checksum for ``raw_file_path`` matches the entry in
    ``data/source_metadata.yaml``.  If the checksums differ (or no entry
    exists), the function re‑downloads the source by invoking the appropriate
    fetch routine from ``code.data.fetch`` and updates the provenance record.

    This function is deliberately **strict** – it raises if a download
    fails, never falling back to synthetic data.

    Parameters
    ----------
    source_name
        Identifier used in the metadata file (e.g. ``"Materials Project"``).
    raw_file_path
        Path to the raw JSON dump produced by the fetcher.
    query_parameters
        The exact query parameters that were used for the fetch.
    api_version
        Version string of the remote API.
    """
    # Load current metadata (if any)
    if METADATA_OUTPUT_PATH.is_file():
        with METADATA_OUTPUT_PATH.open("r", encoding="utf-8") as f:
            entries = yaml.safe_load(f) or []
        if not isinstance(entries, list):
            entries = [entries]
    else:
        entries = []

    # Find existing entry for this source
    matching = [
        e for e in entries if e.get("source_name") == source_name
    ]

    current_checksum = _compute_checksum(raw_file_path)

    if matching and matching[0].get("checksum") == current_checksum:
        logger.info(
            "Provenance for '%s' is up‑to‑date (checksum %s).",
            source_name,
            current_checksum,
        )
        return  # No action required

    # Checksums differ or entry missing → re‑download
    logger.info(
        "Provenance mismatch or missing for '%s'; re‑fetching data.",
        source_name,
    )
    from .fetch import fetch_all  # Local import to avoid circular dependency

    # ``fetch_all`` re‑downloads **both** sources; we then recompute
    # the checksum for the specific file we care about.
    fetch_all()

    # After re‑download, recompute checksum and write a fresh entry
    new_checksum = _compute_checksum(raw_file_path)
    new_entry = {
        "source_name": source_name,
        "api_version": api_version,
        "query_parameters": query_parameters,
        "timestamp": datetime.utcnow().isoformat(),
        "checksum": new_checksum,
        "file_path": str(raw_file_path),
    }
    write_metadata_entry(new_entry)
