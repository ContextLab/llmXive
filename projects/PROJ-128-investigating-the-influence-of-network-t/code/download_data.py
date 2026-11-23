"""
download_data.py

Script to download the HCP OpenNeuro dataset (ds000224) using the HuggingFace
`datasets` library, validate its schema (if a schema is provided), compute
SHA‑256 checksums for all downloaded files, and write a verified manifest
JSON file.  Any subjects/files that cannot be processed are recorded in
`data/logs/exclusion_log.json`.

This script is invoked by the quick‑start run‑book (`python code/download_data.py`).
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict

from datasets import load_dataset
from llmxive_toolkit import paths, get_logger
from config import get_config_dict

log = get_logger(__name__)

def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """Compute the SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def write_exclusion_log(exclusions: List[Dict]) -> None:
    """Write exclusions to `data/logs/exclusion_log.json`."""
    exclusion_path = paths.data("logs", "exclusion_log.json")
    exclusion_path.parent.mkdir(parents=True, exist_ok=True)
    with exclusion_path.open("w") as f:
        json.dump(exclusions, f, indent=2)
    log.info(f"Exclusion log written to {exclusion_path}")

def main() -> None:
    """
    Main entry point.

    Steps:
    1. Download the OpenNeuro ds000224 dataset via `datasets.load_dataset`.
    2. (Optional) Validate the dataset against a JSON‑Schema if one exists.
    3. Compute SHA‑256 checksums for every file that was downloaded.
    4. Write a manifest (`data/raw/verified_manifest.json`) containing the
       relative paths and checksums.
    5. Record any exclusions (e.g., download failures) in
       `data/logs/exclusion_log.json`.
    """
    config = get_config_dict()
    # Ensure the raw data directory exists
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    exclusions: List[Dict] = []

    try:
        # The HuggingFace `datasets` library will download the dataset into its
        # own cache directory.  We request the full (non‑streaming) version so
        # that all files are materialised on disk.
        log.info("Downloading OpenNeuro dataset ds000224 …")
        ds = load_dataset("openneuro/ds000224")
    except Exception as exc:
        log.error(f"Failed to download dataset: {exc}")
        # Record a single exclusion entry indicating the whole download failed
        exclusions.append(
            {
                "subject_id": None,
                "reason": "dataset_download_failure",
                "error_message": str(exc),
            }
        )
        write_exclusion_log(exclusions)
        raise

    # ----------------------------------------------------------------------
    # OPTIONAL: Schema validation
    # ----------------------------------------------------------------------
    # The specification mentions a schema file `contracts/dataset.schema.yaml`.
    # If the file exists we validate the dataset rows against it using
    # `jsonschema`.  The validation is non‑fatal – rows that do not conform
    # are added to the exclusion log.
    try:
        from jsonschema import validate, ValidationError
        import yaml

        schema_path = Path("contracts", "dataset.schema.yaml")
        if schema_path.is_file():
            with schema_path.open() as sf:
                schema = yaml.safe_load(sf)
            # The dataset is a `datasets.Dataset`; convert to a list of dicts
            for row in ds:
                try:
                    validate(instance=row, schema=schema)
                except ValidationError as ve:
                    exclusions.append(
                        {
                            "subject_id": row.get("subject_id"),
                            "reason": "schema_validation_failure",
                            "error_message": str(ve),
                        }
                    )
    except Exception as e:
        # If jsonschema or yaml are unavailable we simply skip validation.
        log.debug(f"Schema validation skipped or failed: {e}")

    # ----------------------------------------------------------------------
    # Compute checksums for every file that the `datasets` library has cached.
    # ----------------------------------------------------------------------
    file_paths = set()
    # `ds.cache_files` is a dict mapping column names to a list of dicts,
    # each containing a `'filename'` key pointing at the cached file.
    for col_files in ds.cache_files.values():
        for entry in col_files:
            filename = entry.get("filename")
            if filename:
                file_paths.add(Path(filename))

    manifest: List[Dict[str, str]] = []
    for fp in sorted(file_paths):
        try:
            checksum = compute_sha256(fp)
            rel_path = fp.relative_to(Path.cwd())
            manifest.append({"path": str(rel_path), "sha256": checksum})
        except Exception as exc:
            log.warning(f"Could not checksum file {fp}: {exc}")
            exclusions.append(
                {
                    "subject_id": None,
                    "reason": "checksum_failure",
                    "file": str(fp),
                    "error_message": str(exc),
                }
            )

    # Write the verified manifest
    manifest_path = paths.data("raw", "verified_manifest.json")
    with manifest_path.open("w") as f:
        json.dump(manifest, f, indent=2)
    log.info(f"Verified manifest written to {manifest_path}")

    # Finally, write any exclusions discovered during the run
    write_exclusion_log(exclusions)

if __name__ == "__main__":
    main()
