"""
Simple integration test that ensures the checksum manifest can be regenerated
without error and that it contains an entry for the packed Möbius file.
"""

import pathlib

from code.generate_checksum import generate_checksum_manifest
from llmxive_toolkit import paths

def test_checksum_manifest_contains_packed_file():
    # Regenerate the manifest
    generate_checksum_manifest()

    manifest_path = paths.data("checksums", "manifest.sha256")
    assert manifest_path.is_file(), "Checksum manifest was not created."

    packed_path = pathlib.Path("data/raw/mobius_2bit.npy")
    # Compute the expected digest directly
    import hashlib

    hasher = hashlib.sha256()
    with packed_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    expected_digest = hasher.hexdigest()

    # Verify that the manifest contains the correct line
    expected_line = f"{expected_digest} {packed_path.as_posix()}"
    manifest_contents = manifest_path.read_text(encoding="utf-8").splitlines()
    assert any(line.strip() == expected_line for line in manifest_contents), (
        f"Packed Möbius file checksum not found or mismatched in {manifest_path}"
    )