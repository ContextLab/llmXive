import os
import tempfile
import hashlib
import pytest
from pathlib import Path
import yaml

from src.data.download import calculate_sha256, verify_checksum, store_metadata

@pytest.fixture
def sample_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def metadata_path():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)

def test_calculate_sha256(sample_file):
    expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
    actual_hash = calculate_sha256(sample_file)
    assert actual_hash == expected_hash

def test_verify_checksum_success(sample_file):
    checksum = calculate_sha256(sample_file)
    assert verify_checksum(sample_file, checksum) is True

def test_verify_checksum_failure(sample_file):
    wrong_checksum = hashlib.sha256(b"Wrong Data").hexdigest()
    assert verify_checksum(sample_file, wrong_checksum) is False

def test_store_metadata(metadata_path):
    metadata = {
        'path': '/fake/path.nc',
        'checksum': 'abc123',
        'variable': 'test_var'
    }
    store_metadata(metadata, metadata_path)

    assert os.path.exists(metadata_path)
    with open(metadata_path, 'r') as f:
        loaded = yaml.safe_load(f)

    assert 'files' in loaded
    assert len(loaded['files']) == 1
    assert loaded['files'][0]['path'] == '/fake/path.nc'
    assert loaded['files'][0]['checksum'] == 'abc123'