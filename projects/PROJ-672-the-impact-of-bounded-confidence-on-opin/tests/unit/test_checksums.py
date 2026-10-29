"""
Unit tests for the checksum utilities.
"""
import hashlib
from pathlib import Path
import tempfile

# Import the sha256 function from the project's utils package
from code.utils.checksums import sha256


def test_sha256_matches_hashlib():
    # Create a temporary file with known content
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "sample.txt"
        content = b"OpenAI LLMXive test content"
        tmp_path.write_bytes(content)

        # Compute hash using the utility
        util_hash = sha256(tmp_path)

        # Compute hash directly with hashlib for verification
        expected_hash = hashlib.sha256(content).hexdigest()

        assert util_hash == expected_hash
        assert len(util_hash) == 64, "SHA‑256 hash should be 64 hexadecimal characters"
