"""
Manifest Validator for Data Integrity (FR-007).

This module provides validation logic for the data manifest file (`data_manifest.json`).
It ensures that every data source entry possesses a valid DOI or URL field,
as required by FR-007 for scientific reproducibility and traceability.

It raises `ManifestError` if validation fails.
"""

import json
import os
from typing import Any

from errors import ManifestError


def validate_manifest(manifest_path: str) -> bool:
    """
    Verify that all data sources in the manifest possess valid DOI or URL fields.

    Args:
        manifest_path: Absolute or relative path to the `data_manifest.json` file.

    Returns:
        True if the manifest is valid.

    Raises:
        ManifestError: If the file does not exist, cannot be parsed, or
                       if any source lacks both a valid DOI and a valid URL.
    """
    if not os.path.exists(manifest_path):
        raise ManifestError(f"Manifest file not found: {manifest_path}")

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ManifestError(f"Failed to parse manifest JSON: {e}") from e

    if not isinstance(data, dict):
        raise ManifestError("Manifest root must be a JSON object (dict).")

    sources = data.get("sources", [])
    if not isinstance(sources, list):
        raise ManifestError("Manifest 'sources' field must be a list.")

    if not sources:
        # Technically valid if empty, but usually indicates a configuration error.
        # We allow it but log a warning conceptually.
        return True

    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ManifestError(f"Source at index {index} is not a valid object.")

        doi = source.get("doi")
        url = source.get("url")

        # Validation Logic: Must have at least one valid identifier
        has_doi = bool(doi and isinstance(doi, str) and doi.strip())
        has_url = bool(url and isinstance(url, str) and url.strip())

        if not has_doi and not has_url:
            source_id = source.get("source_id", f"index_{index}")
            raise ManifestError(
                f"FR-007 Violation: Data source '{source_id}' (index {index}) "
                "must possess a valid 'doi' or 'url' field. Neither was found or valid."
            )

    return True


def main() -> None:
    """
    CLI entry point for the manifest validator.
    Expects the manifest path as the first argument, or defaults to 'data/data_manifest.json'.
    """
    import sys

    # Default path relative to project root
    default_path = "data/data_manifest.json"
    manifest_path = sys.argv[1] if len(sys.argv) > 1 else default_path

    try:
        if validate_manifest(manifest_path):
            print(f"Manifest validation successful: {manifest_path}")
    except ManifestError as e:
        print(f"Manifest validation FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
