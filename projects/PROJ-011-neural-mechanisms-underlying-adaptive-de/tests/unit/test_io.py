"""
Unit tests for code/utils/io.py
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import yaml

from code.utils.io import (
    IOLoadError,
    IOSaveError,
    ensure_dir,
    file_exists,
    load_csv,
    save_csv,
    load_json,
    save_json,
    load_yaml,
    save_yaml,
    load_jsonl,
    save_jsonl,
    verify_checksums
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

def test_ensure_dir(temp_dir):
    new_dir = temp_dir / "sub" / "nested"
    result = ensure_dir(new_dir)
    assert result.exists()
    assert result.is_dir()

def test_file_exists(temp_dir):
    f = temp_dir / "test.txt"
    assert not file_exists(f)
    f.touch()
    assert file_exists(f)

def test_save_load_json(temp_dir):
    data = {"key": "value", "num": 42}
    path = temp_dir / "data.json"
    save_json(data, path)
    assert file_exists(path)
    loaded = load_json(path)
    assert loaded == data

def test_save_load_yaml(temp_dir):
    data = {"list": [1, 2, 3], "nested": {"a": 1}}
    path = temp_dir / "data.yaml"
    save_yaml(data, path)
    assert file_exists(path)
    loaded = load_yaml(path)
    assert loaded == data

def test_save_load_csv_dict_list(temp_dir):
    data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    path = temp_dir / "data.csv"
    save_csv(data, path)
    loaded = load_csv(path)
    assert len(loaded) == 2
    assert list(loaded.columns) == ["a", "b"]

def test_save_load_jsonl(temp_dir):
    data = [{"id": 1}, {"id": 2}]
    path = temp_dir / "data.jsonl"
    save_jsonl(data, path)
    loaded = load_jsonl(path)
    assert loaded == data

def test_ioload_error_on_missing_json(temp_dir):
    path = temp_dir / "missing.json"
    with pytest.raises(IOLoadError):
        load_json(path)

def test_ioload_error_on_invalid_yaml(temp_dir):
    path = temp_dir / "bad.yaml"
    path.write_text("key: [unclosed")
    with pytest.raises(IOLoadError):
        load_yaml(path)

def test_verify_checksums_success(temp_dir):
    # Create a file
    f = temp_dir / "file.txt"
    f.write_text("hello world")
    
    # Create checksum file
    import hashlib
    h = hashlib.sha256(b"hello world").hexdigest()
    checksums = {"file.txt": h}
    cs_path = temp_dir / "checksums.yaml"
    save_yaml(checksums, cs_path)
    
    assert verify_checksums(cs_path, temp_dir) is True

def test_verify_checksums_missing(temp_dir):
    checksums = {"missing.txt": "abc123"}
    cs_path = temp_dir / "checksums.yaml"
    save_yaml(checksums, cs_path)
    
    # Should return False and print missing
    assert verify_checksums(cs_path, temp_dir) is False