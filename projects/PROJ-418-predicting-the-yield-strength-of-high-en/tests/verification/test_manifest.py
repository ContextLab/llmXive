import os
import json

import pytest


def test_manifest_contains_required_fields():
    """
    Verify that the generated manifest.json contains all required provenance fields.
    Required fields are: seeds, versions, checksums, and timestamp.
    """
    # Resolve the path to the manifest.json at the repository root
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifest_path = os.path.join(repo_root, "manifest.json")

    assert os.path.exists(
        manifest_path
    ), f"manifest.json not found at expected location: {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    required_fields = ["seeds", "versions", "checksums", "timestamp"]
    for field in required_fields:
        assert (
            field in manifest
        ), f"Required field '{field}' missing from manifest.json"
        # Ensure the field is not empty (basic sanity check)
        assert manifest[field], f"Field '{field}' is empty in manifest.json"