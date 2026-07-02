import json
import os
import tempfile
from pathlib import Path
import pytest
from code.utils.artifact_hash import (
    compute_file_hash,
    compute_directory_hash,
    hash_artifact,
    verify_artifact
)

@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write("test content")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create some files
        Path(tmpdirname, "file1.txt").write_text("content1")
        Path(tmpdirname, "file2.txt").write_text("content2")
        subdir = Path(tmpdirname, "subdir")
        subdir.mkdir()
        Path(subdir, "file3.txt").write_text("content3")
        yield tmpdirname

def test_compute_file_hash(temp_file):
    h = compute_file_hash(temp_file)
    assert len(h) == 64  # SHA256 hex length
    assert isinstance(h, str)

def test_compute_file_hash_content_change(temp_file):
    original_hash = compute_file_hash(temp_file)
    with open(temp_file, 'w') as f:
        f.write("modified content")
    new_hash = compute_file_hash(temp_file)
    assert original_hash != new_hash

def test_compute_directory_hash(temp_dir):
    h = compute_directory_hash(temp_dir)
    assert len(h) == 64
    assert isinstance(h, str)

def test_compute_directory_hash_file_count(temp_dir):
    # Hash should change if we add a file
    h1 = compute_directory_hash(temp_dir)
    Path(temp_dir, "new_file.txt").write_text("new content")
    h2 = compute_directory_hash(temp_dir)
    assert h1 != h2

def test_hash_artifact_file(temp_file):
    result = hash_artifact(temp_file)
    assert result["type"] == "file"
    assert "hash" in result
    assert result["path"] == str(Path(temp_file).resolve())

def test_verify_artifact_success(temp_file):
    h = compute_file_hash(temp_file)
    assert verify_artifact(temp_file, h) is True

def test_verify_artifact_failure(temp_file):
    h = compute_file_hash(temp_file)
    assert verify_artifact(temp_file, "wrong_hash") is False

def test_verify_directory_artifact(temp_dir):
    h = compute_directory_hash(temp_dir)
    assert verify_artifact(temp_dir, h) is True
