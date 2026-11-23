import os
import tempfile
import hashlib
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock config for testing
TEST_RAW_DIR = tempfile.mkdtemp()
TEST_CHECKSUMS_FILE = os.path.join(TEST_RAW_DIR, "checksums.csv")

@pytest.fixture(autouse=True)
def mock_config():
    with patch("code.checksum_verify.DATA_RAW_DIR", TEST_RAW_DIR):
        with patch("code.checksum_verify.DATA_CHECKSUMS_FILE", TEST_CHECKSUMS_FILE):
            yield

def test_compute_sha256():
    """Test SHA256 computation."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name

    try:
        expected = hashlib.sha256(b"test data").hexdigest()
        actual = __import__("code.checksum_verify", fromlist=["compute_sha256"]).compute_sha256(temp_path)
        assert actual == expected
    finally:
        os.unlink(temp_path)

def test_ensure_raw_directory():
    """Test directory creation."""
    import code.checksum_verify as cv
    new_dir = os.path.join(TEST_RAW_DIR, "new_subdir")
    result = cv.ensure_raw_directory()
    assert result.exists()

def test_load_and_save_checksums():
    """Test loading and saving checksums."""
    import code.checksum_verify as cv
    test_checksums = {"file1.txt": "abc123", "file2.txt": "def456"}
    cv.save_checksums(test_checksums)

    loaded = cv.load_checksums()
    assert loaded == test_checksums

def test_verify_file_success():
    """Test successful file verification."""
    import code.checksum_verify as cv
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name

    try:
        checksum = cv.compute_sha256(temp_path)
        assert cv.verify_file(temp_path, checksum) is True
    finally:
        os.unlink(temp_path)

def test_verify_file_failure():
    """Test failed file verification (wrong checksum)."""
    import code.checksum_verify as cv
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name

    try:
        assert cv.verify_file(temp_path, "wrong_checksum") is False
    finally:
        os.unlink(temp_path)

def test_verify_file_missing():
    """Test verification of missing file."""
    import code.checksum_verify as cv
    assert cv.verify_file("/nonexistent/file.txt", "abc") is False

def test_compute_and_store_checksum():
    """Test computing and storing a checksum."""
    import code.checksum_verify as cv
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name

    try:
        stored_checksum = cv.compute_and_store_checksum(temp_path)
        assert stored_checksum == cv.compute_sha256(temp_path)
    finally:
        os.unlink(temp_path)

def test_verify_all_missing_file():
    """Test verify_all when a file is missing."""
    import code.checksum_verify as cv
    cv.save_checksums({"missing.txt": "abc123"})
    assert cv.verify_all() is False

def test_verify_all_success():
    """Test verify_all when all files exist and match."""
    import code.checksum_verify as cv
    with tempfile.NamedTemporaryFile(dir=TEST_RAW_DIR, delete=False) as f:
        f.write(b"test data")
        temp_path = f.name

    try:
        checksum = cv.compute_sha256(temp_path)
        cv.save_checksums({os.path.basename(temp_path): checksum})
        assert cv.verify_all() is True
    finally:
        os.unlink(temp_path)

def test_store_all():
    """Test storing checksums for all files."""
    import code.checksum_verify as cv
    with tempfile.NamedTemporaryFile(dir=TEST_RAW_DIR, delete=False) as f:
        f.write(b"test data")
        temp_path = f.name

    try:
        cv.store_all()
        checksums = cv.load_checksums()
        assert os.path.basename(temp_path) in checksums
    finally:
        os.unlink(temp_path)

def test_main_verify_command():
    """Test main function with verify command."""
    import code.checksum_verify as cv
    import sys

    with tempfile.NamedTemporaryFile(dir=TEST_RAW_DIR, delete=False) as f:
        f.write(b"test data")
        temp_path = f.name

    try:
        checksum = cv.compute_sha256(temp_path)
        cv.save_checksums({os.path.basename(temp_path): checksum})

        with patch.object(sys, 'argv', ['checksum_verify.py', 'verify']):
            with patch.object(sys, 'exit') as mock_exit:
                cv.main()
                mock_exit.assert_called_with(0)
    finally:
        os.unlink(temp_path)

def test_main_store_command():
    """Test main function with store command."""
    import code.checksum_verify as cv
    import sys

    with tempfile.NamedTemporaryFile(dir=TEST_RAW_DIR, delete=False) as f:
        f.write(b"test data")
        temp_path = f.name

    try:
        with patch.object(sys, 'argv', ['checksum_verify.py', 'store']):
            with patch.object(sys, 'exit') as mock_exit:
                cv.main()
                mock_exit.assert_called_with(0)
    finally:
        os.unlink(temp_path)

def test_main_invalid_command():
    """Test main function with invalid command."""
    import code.checksum_verify as cv
    import sys

    with patch.object(sys, 'argv', ['checksum_verify.py', 'invalid']):
        with patch.object(sys, 'exit') as mock_exit:
            cv.main()
            mock_exit.assert_called_with(1)

def test_main_no_command():
    """Test main function with no command."""
    import code.checksum_verify as cv
    import sys

    with patch.object(sys, 'argv', ['checksum_verify.py']):
        with patch.object(sys, 'exit') as mock_exit:
            cv.main()
            mock_exit.assert_called_with(1)
