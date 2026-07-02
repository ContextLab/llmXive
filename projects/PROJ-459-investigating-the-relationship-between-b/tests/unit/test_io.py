"""
Unit tests for code/utils/io.py
"""
import os
import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from code.utils.io import (
    ensure_dir,
    compute_checksum,
    save_parquet,
    load_parquet,
    save_json,
    load_json,
    write_text,
    read_text,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def test_ensure_dir_creates_parents(temp_dir):
    target = temp_dir / "a" / "b" / "c"
    result = ensure_dir(target)
    assert result.exists()
    assert result.is_dir()


def test_compute_checksum_sha256(temp_dir):
    file_path = temp_dir / "test.txt"
    content = "Hello, world!"
    file_path.write_text(content)

    checksum = compute_checksum(file_path)
    # Known SHA256 for "Hello, world!"
    expected = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
    assert checksum == expected


def test_compute_checksum_missing_file(temp_dir):
    file_path = temp_dir / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        compute_checksum(file_path)


def test_save_and_load_parquet(temp_dir):
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    path = temp_dir / "data.parquet"

    save_parquet(df, path)
    assert path.exists()

    loaded = load_parquet(path)
    assert list(loaded.columns) == ["a", "b"]
    assert len(loaded) == 3


def test_save_and_load_json(temp_dir):
    data = {"key": "value", "number": 42}
    path = temp_dir / "config.json"

    save_json(data, path)
    assert path.exists()

    loaded = load_json(path)
    assert loaded == data


def test_write_and_read_text(temp_dir):
    path = temp_dir / "notes.txt"
    content = "Line 1\nLine 2"

    write_text(path, content)
    assert path.exists()

    read = read_text(path)
    assert read == content