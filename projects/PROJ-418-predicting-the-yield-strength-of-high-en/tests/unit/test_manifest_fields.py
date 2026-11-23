"""
Test to verify that the generated manifest.json contains all required provenance fields.

Required fields (as per project specification):
  - seeds
  - versions
  - checksums

If the manifest does not exist, the test will invoke the full pipeline's
``run_full_pipeline`` entry point to generate it.
"""

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def manifest_path():
    """
    Resolve the path to the manifest file. The manifest is expected to be located
    under the ``outputs`` directory as ``outputs/manifest.json``.
    """
    return Path("outputs/manifest.json")


def generate_manifest_if_missing():
    """
    Run the full pipeline's main entry point to produce the manifest.

    The ``run_full_pipeline`` module already implements the logic for building
    the manifest (collecting checksums, version information, and random seeds).
    """
    from run_full_pipeline import main as run_full_pipeline_main

    # The main function writes the manifest to the correct location.
    run_full_pipeline_main()


def test_manifest_contains_required_fields(manifest_path):
    """
    Ensure that ``manifest.json`` exists and includes the required top‑level keys.
    """
    if not manifest_path.is_file():
        # If the manifest is missing, generate it by executing the pipeline.
        generate_manifest_if_missing()

    assert manifest_path.is_file(), f"Manifest file not found at {manifest_path}"

    with manifest_path.open("r", encoding="utf-8") as fp:
        manifest = json.load(fp)

    # Required top‑level fields as defined in the specification.
    required_fields = {"seeds", "versions", "checksums"}

    missing = required_fields - manifest.keys()
    assert not missing, f"Manifest is missing required fields: {missing}"

    # Additional sanity checks (optional but helpful for future debugging)
    # Ensure that each required field is a mapping/dictionary.
    for field in required_fields:
        assert isinstance(
            manifest[field], dict
        ), f"The field '{field}' should be a JSON object (dict)."

    # Example of a deeper check: at least one checksum entry should be present.
    if manifest["checksums"]:
        # Verify that checksum values look like SHA256 hex strings (64 hex chars)
        for name, checksum in manifest["checksums"].items():
            assert (
                isinstance(checksum, str) and len(checksum) == 64
            ), f"Checksum for '{name}' does not appear to be a valid SHA256 hash."
    else:
        pytest.fail("Manifest 'checksums' section is empty.")