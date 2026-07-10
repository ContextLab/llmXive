"""
Unit tests for the checksum utilities.
"""
import hashlib
import tempfile
from pathlib import Path

import pytest

from src.utils.checksums import (
    compute_sha256,
    read_checksum_file,
    verify_checksum,
    verify_file_with_checksum_file,
    write_checksum_file,
)


class TestComputeSha256:
    def test_compute_sha256_known_value(self):
        """Test against a known string's SHA256."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            computed = compute_sha256(temp_path)
            expected = hashlib.sha256(b"Hello, World!").hexdigest()
            assert computed == expected
        finally:
            Path(temp_path).unlink()

    def test_compute_sha256_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            computed = compute_sha256(temp_path)
            expected = hashlib.sha256(b"").hexdigest()
            assert computed == expected
        finally:
            Path(temp_path).unlink()

    def test_compute_sha256_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")


class TestVerifyChecksum:
    def test_verify_checksum_success(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            is_valid, message = verify_checksum(temp_path, checksum)
            assert is_valid is True
            assert "successful" in message.lower()
        finally:
            Path(temp_path).unlink()

    def test_verify_checksum_failure(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            is_valid, message = verify_checksum(temp_path, "wrongchecksum")
            assert is_valid is False
            assert "mismatch" in message.lower()
        finally:
            Path(temp_path).unlink()

    def test_verify_checksum_case_insensitive(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            # Use uppercase version
            is_valid, message = verify_checksum(temp_path, checksum.upper())
            assert is_valid is True
        finally:
            Path(temp_path).unlink()


class TestWriteChecksumFile:
    def test_write_checksum_file_creates_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            checksum_file = Path(temp_path).with_suffix(Path(temp_path).suffix + ".sha256")
            checksum = write_checksum_file(temp_path, str(checksum_file))

            assert checksum_file.exists()
            assert checksum == compute_sha256(temp_path)

            with open(checksum_file, "r") as f:
                content = f.read()
                assert checksum in content
        finally:
            Path(temp_path).unlink()
            if checksum_file.exists():
                checksum_file.unlink()


class TestVerifyFileWithChecksumFile:
    def test_verify_file_with_checksum_file_success(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            write_checksum_file(temp_path)
            is_valid, message = verify_file_with_checksum_file(temp_path)
            assert is_valid is True
        finally:
            Path(temp_path).unlink()
            checksum_file = Path(temp_path).with_suffix(Path(temp_path).suffix + ".sha256")
            if checksum_file.exists():
                checksum_file.unlink()

    def test_verify_file_with_checksum_file_missing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            write_checksum_file(temp_path)
            # Delete the actual file, keep checksum file
            Path(temp_path).unlink()
            is_valid, message = verify_file_with_checksum_file(temp_path)
            assert is_valid is False
            assert "not found" in message.lower()
        finally:
            checksum_file = Path(temp_path).with_suffix(Path(temp_path).suffix + ".sha256")
            if checksum_file.exists():
                checksum_file.unlink()
