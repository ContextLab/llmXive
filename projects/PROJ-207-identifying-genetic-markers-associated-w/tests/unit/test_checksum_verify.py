"""
Unit tests for checksum_verify.py
"""
import hashlib
import os
import tempfile
from pathlib import Path
import sys

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.checksum_verify import compute_sha256, load_manifest, verify_checksums

def test_compute_sha256():
    """Test SHA-256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = compute_sha256(Path(temp_path))
        assert actual_hash == expected_hash, f"Hash mismatch: {actual_hash} != {expected_hash}"
    finally:
        os.unlink(temp_path)

def test_load_manifest_valid():
    """Test loading a valid manifest."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("# Comment\n")
        f.write("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  file1.txt\n")
        f.write("d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592  file2.txt\n")
        temp_path = f.name
    
    try:
        manifest = load_manifest(Path(temp_path))
        assert len(manifest) == 2
        assert "file1.txt" in manifest
        assert "file2.txt" in manifest
        assert manifest["file1.txt"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    finally:
        os.unlink(temp_path)

def test_load_manifest_invalid_format():
    """Test that invalid manifest format raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("invalid_line_without_two_parts\n")
        temp_path = f.name
    
    try:
        try:
            load_manifest(Path(temp_path))
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
    finally:
        os.unlink(temp_path)

def test_load_manifest_invalid_hash():
    """Test that invalid hash format raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("not_a_valid_hash  file.txt\n")
        temp_path = f.name
    
    try:
        try:
            load_manifest(Path(temp_path))
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
    finally:
        os.unlink(temp_path)