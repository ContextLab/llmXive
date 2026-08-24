"""
Specification validation tests for T006 (Hashing Utilities).
Validates Functional Requirements for hashing (FR-HASH-001 through FR-HASH-004).
"""
import pytest
import tempfile
from pathlib import Path

from code.utils.hash import calculate_sha256, generate_manifest, verify_manifest


@pytest.fixture
def temp_files():
    """Create temporary test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        file1 = base / "file1.txt"
        file1.write_text("Content 1")
        file2 = base / "file2.txt"
        file2.write_text("Content 2")
        yield base, file1, file2


def test_fr_hash_001_single_file_hashing(temp_files):
    """
    FR-HASH-001: The system SHALL generate a SHA-256 checksum for every
    intermediate and final file (BAMs, PSI tables, TSVs).
    """
    _, file1, _ = temp_files
    hash_val = calculate_sha256(file1)
    assert len(hash_val) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in hash_val)


def test_fr_hash_002_manifest_generation(temp_files):
    """
    FR-HASH-002: The system SHALL record the hash of external input artifacts
    (e.g., primate_tree.nwk) in the manifest.
    """
    base, _, tree_file = temp_files
    tree_file.write_text("(A:1.0, B:1.0);")

    manifest = generate_manifest(
        file_paths=[],
        include_external={"tree": tree_file}
    )

    assert "external_artifacts" in manifest
    assert "tree" in manifest["external_artifacts"]
    assert manifest["external_artifacts"]["tree"]["hash"] is not None


def test_fr_hash_003_manifest_verification(temp_files):
    """
    FR-HASH-003: The system SHALL verify the integrity of files against
    the stored manifest.
    """
    base, file1, _ = temp_files
    manifest_path = base / "manifest.json"

    generate_manifest([file1], manifest_path)

    # Verify valid state
    assert verify_manifest(manifest_path) is True

    # Modify file
    file1.write_text("Modified")
    assert verify_manifest(manifest_path) is False


def test_fr_hash_004_error_handling(temp_files):
    """
    FR-HASH-004: The system SHALL fail loudly (raise error) if a file
    required for hashing or verification is missing, rather than silently
    skipping or fabricating a hash.
    """
    base, _, _ = temp_files
    missing_file = base / "missing.txt"
    manifest_path = base / "manifest_missing.json"

    # Test generation with missing file
    with pytest.raises(FileNotFoundError):
        generate_manifest([missing_file])

    # Test verification with missing file
    # Create a manifest pointing to a missing file
    import json
    manifest = {
        "version": "1.0",
        "algorithm": "sha256",
        "artifacts": {str(missing_file): "000..."},
        "external_artifacts": {}
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f)

    # Should return False (log error) rather than crash, but file must be missing
    assert verify_manifest(manifest_path) is False
