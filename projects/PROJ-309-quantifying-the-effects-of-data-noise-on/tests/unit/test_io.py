import pytest
import numpy as np
import json
import tempfile
import os
from pathlib import Path

from code.utils.io import compute_file_checksum, write_json_artifact, export_csv

def test_compute_file_checksum():
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("test content")
        temp_path = f.name

    try:
        checksum = compute_file_checksum(temp_path)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length
    finally:
        os.unlink(temp_path)

def test_write_json_artifact():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.json"
        data = {"key": "value", "number": 42}
        write_json_artifact(data, file_path)

        assert file_path.exists()
        with open(file_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == data

def test_export_csv_dicts():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.csv"
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        export_csv(data, file_path)

        assert file_path.exists()
        with open(file_path, 'r') as f:
            content = f.read()
        assert "a,b" in content
        assert "1,2" in content
