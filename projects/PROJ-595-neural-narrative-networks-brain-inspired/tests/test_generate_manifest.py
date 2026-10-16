"""
Unit test for the reproducibility manifest generator.

The test simply runs the generator (by importing the function) and
verifies that the resulting ``manifest.json`` contains the required
top‑level keys and that each section is non‑empty.
"""
import json
from pathlib import Path

from code.generate_manifest import generate_manifest

def test_manifest_structure(tmp_path: Path):
    """
    Execute the manifest generator and assert the structure of the output.
    """
    # The generator writes to the repository root; we run it in the
    # current working directory (the project root) which is the same as
    # ``paths.root`` used inside the module.
    manifest_path = generate_manifest()
    assert manifest_path.is_file(), "manifest.json was not created"

    data = json.loads(manifest_path.read_text())

    # Required top‑level fields
    required_keys = {"datasets", "commit_hash", "software_versions", "checksums"}
    assert required_keys.issubset(data.keys()), f"Missing keys in manifest: {required_keys - data.keys()}"

    # Each section must contain at least one entry
    assert isinstance(data["datasets"], dict) and data["datasets"], "datasets section is empty"
    assert isinstance(data["commit_hash"], str) and data["commit_hash"], "commit_hash is empty"
    assert isinstance(data["software_versions"], dict) and data["software_versions"], "software_versions section is empty"
    assert isinstance(data["checksums"], dict) and data["checksums"], "checksums section is empty"