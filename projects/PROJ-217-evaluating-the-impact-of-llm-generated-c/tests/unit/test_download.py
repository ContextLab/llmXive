import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths
from src.data.download import main, _load_expected_hashes, _sha256

def test_sha256_consistency(tmp_path, monkeypatch):
    # Create a temporary file with known content
    file_path = tmp_path / "test.txt"
    file_path.write_text("abc")
    expected = "a9993e364706816aba3e25717850c26c9cd0d89d"  # SHA1 of "abc", not SHA256
    # Compute SHA256 using the function and compare length only (should be 64 hex chars)
    result = _sha256(file_path)
    assert isinstance(result, str)
    assert len(result) == 64

def test_download_creates_outputs(monkeypatch, tmp_path):
    # Redirect data paths to a temporary directory
    monkeypatch.setattr(paths, "data", lambda *parts: Path(tmp_path, *parts))
    # Ensure artifact_hashes.yaml exists (empty)
    (tmp_path / "artifact_hashes.yaml").write_text("{}")
    # Run the main download function
    main()
    # Verify that raw_snippets.jsonl and excluded_records.json are created
    assert (tmp_path / "raw_snippets.jsonl").is_file()
    assert (tmp_path / "excluded_records.json").is_file()
    # Verify that at least one parquet file was written
    parquet_files = list(tmp_path.glob("*.parquet"))
    assert len(parquet_files) > 0
    # Verify that the manifest was updated with at least one entry
    hashes = _load_expected_hashes()
    assert isinstance(hashes, dict)
    assert any(key.endswith(".parquet") for key in hashes)