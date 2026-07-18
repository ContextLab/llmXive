"""Unit tests for code/utils/io_utils.py."""

import csv
import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from code.utils.io_utils import (
    compute_sha256,
    ensure_dir,
    read_csv,
    read_json,
    read_yaml,
    verify_sha256,
    write_csv,
    write_json,
    write_yaml,
)


class TestEnsureDir:
    def test_creates_missing_directory(self, tmp_path):
        deep_path = tmp_path / "a" / "b" / "c" / "file.txt"
        ensure_dir(deep_path)
        assert deep_path.parent.exists()

    def test_exists_already(self, tmp_path):
        existing = tmp_path / "existing" / "file.txt"
        existing.parent.mkdir(parents=True)
        ensure_dir(existing)
        assert existing.parent.exists()


class TestJsonIO:
    def test_write_and_read_json(self, tmp_path):
        data = {"key": "value", "number": 42}
        path = tmp_path / "test.json"
        write_json(path, data)
        assert path.exists()
        loaded = read_json(path)
        assert loaded == data

    def test_invalid_json_raises_error(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{ invalid json }")
        with pytest.raises(json.JSONDecodeError):
            read_json(path)


class TestCsvIO:
    def test_write_and_read_csv(self, tmp_path):
        data = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]
        path = tmp_path / "test.csv"
        write_csv(path, data)
        assert path.exists()
        loaded = read_csv(path)
        assert loaded == data

    def test_empty_list_raises_error(self, tmp_path):
        path = tmp_path / "empty.csv"
        with pytest.raises(ValueError):
            write_csv(path, [])

    def test_read_skips_blank_lines(self, tmp_path):
        content = "a,b\n1,2\n\n3,4\n"
        path = tmp_path / "blank.csv"
        path.write_text(content)
        loaded = read_csv(path)
        assert len(loaded) == 2


class TestYamlIO:
    def test_write_and_read_yaml(self, tmp_path):
        data = {"list": [1, 2, 3], "nested": {"key": "val"}}
        path = tmp_path / "test.yaml"
        write_yaml(path, data)
        assert path.exists()
        loaded = read_yaml(path)
        assert loaded == data

    def test_invalid_yaml_raises_error(self, tmp_path):
        path = tmp_path / "bad.yaml"
        path.write_text("key: [invalid yaml")
        with pytest.raises(yaml.YAMLError):
            read_yaml(path)


class TestChecksum:
    def test_compute_and_verify(self, tmp_path):
        path = tmp_path / "data.txt"
        path.write_text("Hello, World!")
        hash_val = compute_sha256(path)
        assert verify_sha256(path, hash_val)
        assert not verify_sha256(path, "wrong_hash")

    def test_file_not_found(self, tmp_path):
        path = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            compute_sha256(path)
