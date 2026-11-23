"""Test that the generated manifest.json contains all required provenance fields.

This verification corresponds to task T122. It ensures that the manifest produced by the
full pipeline includes the keys:
  - seeds
  - versions
  - artifact_hashes (checksums)

If the manifest does not exist, the test will invoke the pipeline helper
`build_manifest` (exposed by `code/run_full_pipeline.py`) to create it before
performing the checks.
"""

import json
from pathlib import Path

# The manifest is written to the ``output`` directory by the pipeline.
MANIFEST_PATH = Path("output") / "manifest.json"

# The keys that must be present in a valid manifest.
REQUIRED_TOP_LEVEL_KEYS = {"seeds", "versions", "artifact_hashes"}

def _ensure_manifest_exists() -> dict:
    """Return the manifest dictionary, creating it if necessary."""
    if MANIFEST_PATH.is_file():
        with MANIFEST_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)

    # Import the helper that builds the manifest.  The function is part of the
    # public API of ``code/run_full_pipeline.py``.
    try:
        from run_full_pipeline import build_manifest
    except ImportError as exc:
        raise ImportError(
            "Unable to import `build_manifest` from `run_full_pipeline`. "
            "Ensure that the pipeline code is present and importable."
        ) from exc

    # ``build_manifest`` is expected to write the manifest to the same location
    # (output/manifest.json) and return the manifest dictionary.
    manifest = build_manifest()
    if not isinstance(manifest, dict):
        raise TypeError(
            "`build_manifest` should return a dict representing the manifest, "
            f"got {type(manifest)} instead."
        )
    # Double‑check that the file was written.
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(
            f"`build_manifest` did not create the expected file at {MANIFEST_PATH}"
        )
    return manifest

def test_manifest_contains_required_fields():
    """Verify that the manifest includes seeds, versions, and checksums."""
    manifest = _ensure_manifest_exists()

    missing = REQUIRED_TOP_LEVEL_KEYS - manifest.keys()
    assert not missing, f"Manifest is missing required top‑level keys: {sorted(missing)}"

    # Additional sanity checks – ensure each required field is a non‑empty mapping.
    for key in REQUIRED_TOP_LEVEL_KEYS:
        value = manifest.get(key)
        assert isinstance(value, dict), f"`{key}` should be a dict, got {type(value)}"
        assert value, f"`{key}` dict is empty; expected provenance information"

    # Optional: verify that the checksums look like SHA‑256 hex digests.
    checksums = manifest.get("artifact_hashes", {})
    for artifact, checksum in checksums.items():
        assert isinstance(checksum, str), f"Checksum for {artifact} must be a string"
        assert len(checksum) == 64, (
            f"Checksum for {artifact} does not appear to be a SHA‑256 hex digest "
            f"(got {checksum})"
        )
        # Simple hex validation
        int(checksum, 16)  # will raise ValueError if not valid hex

# The test can be executed directly for quick debugging:
if __name__ == "__main__":
    test_manifest_contains_required_fields()
    print("Manifest verification passed.")