"""Tests for the checksum_raw_data script.

The test creates a temporary file inside ``data/raw``,
runs the script, and checks that the resulting ``checksums.txt``
contains the expected entry.
"""

import hashlib
from pathlib import Path

from llmxive_toolkit import paths

def test_checksum_raw_data_script(tmp_path, monkeypatch):
    # Arrange: create a temporary raw data file
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    test_file = raw_dir / "example.txt"
    test_content = b"llmXive checksum test"
    test_file.write_bytes(test_content)

    # Compute expected checksum
    expected_checksum = hashlib.sha256(test_content).hexdigest()
    expected_rel_path = test_file.relative_to(paths.root).as_posix()

    # Act: import and run the script's main function
    from code.scripts.checksum_raw_data import main as script_main

    exit_code = script_main()
    assert exit_code == 0

    # Assert: checksum manifest exists and contains the correct line
    checksum_file = paths.data("checksums.txt")
    assert checksum_file.is_file()
    lines = checksum_file.read_text(encoding="utf-8").strip().splitlines()
    assert any(line == f"{expected_checksum}  {expected_rel_path}" for line in lines)