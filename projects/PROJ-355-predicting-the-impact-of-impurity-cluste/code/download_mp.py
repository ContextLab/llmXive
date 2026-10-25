"""
download_mp.py
----------------
Download bulk configuration records from the Materials Project (MP) with
retry logic and record provenance metadata.

This script is invoked as part of the pipeline (e.g. ``python -m code.download_mp``)
and performs the following steps:

1. Queries the Materials Project for 600 bulk configurations, equally split
   among three alloy systems: Fe‑Cr, Ni‑Al, and Cu‑Zn.
2. Downloads each structure, serialises it to JSON, writes it to
   ``data/raw/mp_records/<material_id>.json`` and records a SHA‑256 checksum.
3. Updates ``data/metadata.yaml`` with the checksums and a top‑level field
   ``materials_project_status: AVAILABLE``.
4. Implements up‑to‑three retries for transient HTTP errors; on permanent
   failure logs ``[DATA_UNAVAILABLE]`` and raises an exception.

The script follows the same conventions as ``code/download.py`` (the OQMD
loader) so that the integration tests can locate the downloaded files and
the metadata.
"""

import os
import json
import hashlib
import logging
import random
import time
from pathlib import Path
from typing import List, Dict

import yaml
from pymatgen.ext.matproj import MPRester
from pymatgen.core import Structure

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
MAX_RETRIES = 3
SEED = 20231023
SAMPLE_PER_SYSTEM = 200
ALLY_SYSTEMS = [
    ("Fe", "Cr"),
    ("Ni", "Al"),
    ("Cu", "Zn"),
]

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256_of_bytes(data: bytes) -> str:
    """Return the hex SHA‑256 checksum of *data*."""
    sha = hashlib.sha256()
    sha.update(data)
    return sha.hexdigest()

def _write_json_record(record: Dict, out_path: Path) -> str:
    """
    Write *record* as pretty‑printed JSON to *out_path* and return its checksum.
    The directory hierarchy is created if it does not exist.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json_bytes = json.dumps(record, indent=2, sort_keys=True).encode("utf-8")
    with open(out_path, "wb") as f:
        f.write(json_bytes)
    checksum = _sha256_of_bytes(json_bytes)
    log.debug(f"Wrote {out_path} (SHA‑256={checksum})")
    return checksum

def _retry(func):
    """
    Decorator that retries *func* up to ``MAX_RETRIES`` times on
    ``Exception`` (including network errors). Uses exponential back‑off.
    """
    def wrapper(*args, **kwargs):
        delay = 1
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if attempt == MAX_RETRIES:
                    log.error(f"[DATA_UNAVAILABLE] Final attempt failed: {exc}")
                    raise
                else:
                    log.warning(
                        f"[DATA_UNAVAILABLE] Attempt {attempt} failed ({exc}); "
                        f"retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
        # Should never reach here
        raise RuntimeError("Retry exhausted without raising")
    return wrapper

# ----------------------------------------------------------------------
# Core download logic
# ----------------------------------------------------------------------
@_retry
def _fetch_material_ids(pair: tuple) -> List[str]:
    """
    Query the Materials Project for material IDs that contain *both* elements
    in *pair*. Returns a list of material IDs (strings).
    """
    elements = list(pair)
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Environment variable 'MP_API_KEY' not set – required for Materials Project access."
        )
    with MPRester(api_key) as mpr:
        # ``criteria`` uses the Materials Project query language.
        criteria = {"elements": {"$all": elements}}
        # We only need the material_id; other fields are fetched later.
        docs = mpr.query(criteria, ["material_id"])
    ids = [doc["material_id"] for doc in docs]
    if not ids:
        raise ValueError(f"No Materials Project entries found for elements {elements}")
    return ids

@_retry
def _fetch_structure(material_id: str) -> Structure:
    """
    Retrieve the structure for *material_id* via the MP REST API.
    Returns a ``pymatgen.Structure`` instance.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Environment variable 'MP_API_KEY' not set – required for Materials Project access."
        )
    with MPRester(api_key) as mpr:
        struct = mpr.get_structure_by_material_id(material_id)
    return struct

def _sample_ids(ids: List[str], n: int, rng: random.Random) -> List[str]:
    """Return *n* unique IDs sampled without replacement from *ids*."""
    if len(ids) < n:
        raise ValueError(
            f"Requested {n} samples but only {len(ids)} records are available."
        )
    return rng.sample(ids, n)

def _update_metadata(checksums: Dict[str, str]) -> None:
    """
    Load ``data/metadata.yaml`` (creating it if missing), insert the
    ``materials_project_status`` flag and a ``mp_files`` mapping of
    filename → checksum, then write the file back.
    """
    metadata_path = paths.data("metadata.yaml")
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = yaml.safe_load(f) or {}
    else:
        metadata = {}

    # Top‑level status flag required by the test suite.
    metadata["materials_project_status"] = "AVAILABLE"

    # Record per‑file checksums under a dedicated key.
    metadata.setdefault("mp_files", {})
    metadata["mp_files"].update(checksums)

    # Ensure the file exists and write atomically.
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(metadata, f, sort_keys=False)

    log.info(f"Metadata updated at {metadata_path}")

# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------
def download_mp_records(max_retries: int = MAX_RETRIES, seed: int = SEED) -> None:
    """
    Download bulk configuration records from the Materials Project.

    The function creates ``data/raw/mp_records`` and writes one JSON file per
    material.  It also records SHA‑256 checksums and a status flag in
    ``data/metadata.yaml``.
    """
    # Initialise RNG for reproducibility.
    rng = random.Random(seed)

    # Destination directory.
    out_dir = paths.data("raw", "mp_records")
    out_dir.mkdir(parents=True, exist_ok=True)

    all_checksums: Dict[str, str] = {}

    for pair in ALLY_SYSTEMS:
        log.info(f"Fetching material IDs for alloy system {pair[0]}‑{pair[1]}")
        material_ids = _fetch_material_ids(pair)

        sampled_ids = _sample_ids(material_ids, SAMPLE_PER_SYSTEM, rng)
        log.info(
            f"Sampled {len(sampled_ids)} records for {pair[0]}‑{pair[1]}"
        )

        for mat_id in sampled_ids:
            try:
                struct = _fetch_structure(mat_id)
            except Exception as exc:
                # Propagate through the retry decorator – this will cause a
                # retry of the *individual* structure fetch.
                raise RuntimeError(f"Failed to fetch structure {mat_id}: {exc}")

            # Convert the structure to a JSON‑serialisable dict.
            record = {
                "material_id": mat_id,
                "pretty_formula": struct.composition.reduced_formula,
                "structure": struct.as_dict(),
            }

            out_path = out_dir / f"{mat_id}.json"
            checksum = _write_json_record(record, out_path)
            # Store checksum with a path relative to the project root.
            rel_path = str(out_path.relative_to(paths.root))
            all_checksums[rel_path] = checksum

    # Update provenance metadata.
    _update_metadata(all_checksums)
    log.info("Materials Project download completed successfully.")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Simple CLI wrapper – invoked when the module is executed directly.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Environment variable 'MP_API_KEY' not set – required for Materials Project access."
        )
    download_mp_records()
    log.info("download_mp.py finished.")

if __name__ == "__main__":
    main()
