"""
Unit tests for the checksum utilities.
"""
import hashlib
import os
import tempfile
import sys

# Ensure the project's code directory is on the import path so that
# `utils.checksums` can be imported (the utils package lives under `code/`).
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

from utils.checksums import calculate_sha256, generate_checksums_for_directory


def test_calculate_sha256_matches_manual():
    """The SHA‑256 returned by the utility must match hashlib directly."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"llmxive test payload")
        tmp_path = tmp.name

    try:
        # Expected hash using hashlib directly
        expected = hashlib.sha256(b"llmxive test payload").hexdigest()

        # Hash computed by the utility
        result = calculate_sha256(tmp_path)

        assert isinstance(result, str)
        assert len(result) == 64
        assert result == expected
    finally:
        os.remove(tmp_path)


def test_generate_checksums_for_directory_collects_files():
    """The directory scanner must return a dict with a hash for each file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a couple of files
        file_paths = []
        for i, content in enumerate([b"alpha", b"beta", b"gamma"]):
            path = os.path.join(tmpdir, f"file{i}.txt")
            with open(path, "wb") as f:
                f.write(content)
            file_paths.append(path)

        checksums = generate_checksums_for_directory(tmpdir)

        # All files should be present
        assert len(checksums) == 3
        for rel_path, expected_hash in zip(
            ["file0.txt", "file1.txt", "file2.txt"],
            [hashlib.sha256(b"alpha").hexdigest(),
             hashlib.sha256(b"beta").hexdigest(),
             hashlib.sha256(b"gamma").hexdigest()],
        ):
            assert checksums[rel_path] == expected_hash
