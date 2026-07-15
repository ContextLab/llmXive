"""Tests for I/O utilities."""
import json
import tempfile
from pathlib import Path
import pandas as pd
import pytest

from src.utils.io import (
    ensure_dir,
    calculate_checksum,
    load_json,
    save_json,
    load_csv,
    save_csv,
    validate_file_exists,
)


def test_ensure_dir_creates_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = Path(tmpdir) / "nested" / "path"
        ensure_dir(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()


def test_calculate_checksum():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello, World!")
        
        checksum = calculate_checksum(test_file)
        assert len(checksum) == 32  # MD5 hex length


def test_checksum_fails_on_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_file = Path(tmpdir) / "missing.txt"
        with pytest.raises(FileNotFoundError):
            calculate_checksum(missing_file)


def test_json_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "data.json"
        data = {"key": "value", "number": 42}
        
        save_json(data, test_file)
        loaded = load_json(test_file)
        
        assert loaded == data


def test_json_fails_on_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_file = Path(tmpdir) / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_json(missing_file)


def test_csv_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "data.csv"
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        
        save_csv(df, test_file)
        loaded = load_csv(test_file)
        
        assert loaded.equals(df)


def test_validate_file_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        existing_file = Path(tmpdir) / "exists.txt"
        existing_file.write_text("test")
        
        # Should not raise
        validate_file_exists(existing_file)
        
        missing_file = Path(tmpdir) / "missing.txt"
        with pytest.raises(FileNotFoundError):
            validate_file_exists(missing_file)
