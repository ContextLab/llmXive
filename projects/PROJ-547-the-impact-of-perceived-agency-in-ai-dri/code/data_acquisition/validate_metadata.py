"""
validate_metadata.py

This script validates that the SHA‑256 checksums recorded in
``datasets/metadata.yaml`` match the actual contents of the files on disk.
It is intended to be run after datasets have been downloaded (e.g. by
``download_datasets.py``) to ensure data integrity before further processing.

The script aborts with a non‑zero exit code if any mismatch is detected.
Successful validation logs an informational message.

The expected format of ``metadata.yaml`` is a simple mapping where the key is
the path to the dataset file (relative to the repository root) and the value
is the expected SHA‑256 hexadecimal digest, e.g.:

.. code-block:: yaml

    data/raw/example.csv: d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2

The script makes no assumptions about the location of the files other than
that the paths are valid relative to the current working directory.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

import yaml

from data_acquisition.download_agency_scale import compute_sha256
from logging.pipeline_logger import get_logger, log_dict

LOGGER = get_logger(__name__)


def load_metadata(metadata_path: Path) -> Dict[str, str]:
    """
    Load the metadata YAML file.

    Parameters
    ----------
    metadata_path: Path
        Path to the ``metadata.yaml`` file.

    Returns
    -------
    dict
        Mapping of file paths (as strings) to expected SHA‑256 digests.
    """
    if not metadata_path.is_file():
        LOGGER.error(f"Metadata file not found: {metadata_path}")
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    with metadata_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        LOGGER.error("Metadata file format is invalid; expected a mapping.")
        raise ValueError("Metadata file format is invalid; expected a mapping.")

    return data


def verify_checksums(metadata: Dict[str, str]) -> None:
    """
    Verify that each file's actual checksum matches the expected checksum.

    Parameters
    ----------
    metadata: dict
        Mapping from file path (relative) to expected SHA‑256 digest.

    Raises
    ------
    RuntimeError
        If any file is missing or its checksum does not match.
    """
    mismatches = []

    for rel_path_str, expected_checksum in metadata.items():
        file_path = Path(rel_path_str)

        if not file_path.is_file():
            mismatches.append(
                f"Missing file: {rel_path_str} (expected checksum {expected_checksum})"
            )
            continue

        actual_checksum = compute_sha256(file_path)

        if actual_checksum.lower() != expected_checksum.lower():
            mismatches.append(
                f"Checksum mismatch for {rel_path_str}: expected {expected_checksum}, got {actual_checksum}"
            )

    if mismatches:
        for msg in mismatches:
            LOGGER.error(msg)

        # Log a structured dict for downstream tooling
        log_dict(
            LOGGER,
            {
                "event": "metadata_validation_failed",
                "issues": mismatches,
                "status": "failure",
            },
        )
        raise RuntimeError("One or more checksum validations failed.")
    else:
        LOGGER.info("All dataset checksums match expected values.")
        log_dict(
            LOGGER,
            {
                "event": "metadata_validation_success",
                "status": "success",
                "validated_files": list(metadata.keys()),
            },
        )


def main() -> None:
    """
    Entry point for the validation script.

    The default location of the metadata file is ``datasets/metadata.yaml``
    relative to the repository root. The script can be invoked directly:

    .. code-block:: bash

        python code/data_acquisition/validate_metadata.py

    It will exit with status ``0`` on success or ``1`` on failure.
    """
    metadata_path = Path("datasets") / "metadata.yaml"

    try:
        metadata = load_metadata(metadata_path)
        verify_checksums(metadata)
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception("Metadata validation failed.")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
