import pytest
import os
from pathlib import Path
from code.utils.checksums import sha256, calculate_sha256, generate_checksums_for_directory

def test_sha256_length(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello world")
    # Test both aliases
    assert len(sha256(f)) == 64
    assert len(calculate_sha256(f)) == 64
    assert sha256(f) == calculate_sha256(f)

def test_directory_checksums(tmp_path):
    (tmp_path / "f1.txt").write_text("a")
    (tmp_path / "f2.txt").write_text("b")
    checksums = generate_checksums_for_directory(tmp_path)
    assert len(checksums) == 2
    assert "f1.txt" in checksums
    assert len(checksums["f1.txt"]) == 64
