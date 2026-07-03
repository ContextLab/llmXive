import os
import tempfile
import hashlib
from pathlib import Path

import pytest
import yaml

from utils import (
    setup_logging,
    compute_sha256,
    set_random_seed,
    load_metadata,
    update_metadata_entry,
    save_metadata,
)


def test_setup_logging_stream_only():
    logger = setup_logging()
    assert logger.name == "llmXive"
    assert len(logger.handlers) >= 1
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)


def test_setup_logging_with_file(tmp_path):
    log_file = tmp_path / "test.log"
    logger = setup_logging(str(log_file))
    assert log_file.exists()
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)


def test_compute_sha256(tmp_path):
    test_file = tmp_path / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_sha256(str(test_file))

    assert actual_hash == expected_hash


def test_set_random_seed():
    set_random_seed(123)
    val1 = random.random()

    set_random_seed(123)
    val2 = random.random()

    assert val1 == val2
    assert os.environ["PYTHONHASHSEED"] == "123"


def test_load_metadata_missing_file():
    result = load_metadata("/nonexistent/path/file.yaml")
    assert result == {}


def test_load_metadata_existing_file(tmp_path):
    data = {"key": "value", "number": 42}
    file_path = tmp_path / "meta.yaml"
    with open(file_path, "w") as f:
        yaml.dump(data, f)

    result = load_metadata(str(file_path))
    assert result == data


def test_update_metadata_entry(tmp_path):
    file_path = tmp_path / "meta.yaml"
    # Start empty
    save_metadata({}, str(file_path))

    update_metadata_entry(str(file_path), "new_key", "new_value")

    with open(file_path, "r") as f:
        loaded = yaml.safe_load(f)

    assert loaded["new_key"] == "new_value"


def test_save_metadata(tmp_path):
    data = {"project": "llmXive", "version": 1}
    file_path = tmp_path / "meta.yaml"

    save_metadata(data, str(file_path))

    with open(file_path, "r") as f:
        loaded = yaml.safe_load(f)

    assert loaded == data