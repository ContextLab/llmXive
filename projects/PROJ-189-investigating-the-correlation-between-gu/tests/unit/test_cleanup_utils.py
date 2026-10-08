"""Unit tests for code/utils/cleanup_utils.py helper functions."""

import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from utils.cleanup_utils import (
    ensure_directory_exists,
    load_json_config,
    save_json_config,
    calculate_file_checksum,
    validate_data_integrity
)


class TestEnsureDirectoryExists:
    """Tests for ensure_directory_exists function."""

    def test_create_new_directory(self):
        """Test creating a new directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            new_dir = os.path.join(tmp_dir, "new_dir")
            ensure_directory_exists(new_dir)
            assert os.path.exists(new_dir)
            assert os.path.isdir(new_dir)

    def test_existing_directory_no_error(self):
        """Test that existing directory does not raise error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            ensure_directory_exists(tmp_dir)
            assert os.path.exists(tmp_dir)

    def test_create_nested_directories(self):
        """Test creating nested directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            nested_dir = os.path.join(tmp_dir, "a", "b", "c")
            ensure_directory_exists(nested_dir)
            assert os.path.exists(nested_dir)


class TestLoadJsonConfig:
    """Tests for load_json_config function."""

    def test_load_valid_json(self):
        """Test loading a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "config.json")
            config_data = {"key": "value", "number": 42}
            with open(config_path, "w") as f:
                json.dump(config_data, f)

            loaded = load_json_config(config_path)
            assert loaded == config_data

    def test_load_nonexistent_file(self):
        """Test that loading nonexistent file raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "nonexistent.json")
            with pytest.raises(FileNotFoundError):
                load_json_config(config_path)

    def test_load_invalid_json(self):
        """Test that loading invalid JSON raises JSONDecodeError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "invalid.json")
            with open(config_path, "w") as f:
                f.write("{invalid json}")

            with pytest.raises(json.JSONDecodeError):
                load_json_config(config_path)


class TestSaveJsonConfig:
    """Tests for save_json_config function."""

    def test_save_valid_config(self):
        """Test saving a valid config."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "config.json")
            config_data = {"key": "value", "number": 42}
            save_json_config(config_path, config_data)

            assert os.path.exists(config_path)
            with open(config_path, "r") as f:
                loaded = json.load(f)
            assert loaded == config_data

    def test_save_creates_directory(self):
        """Test that save_json_config creates directory if needed."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            nested_path = os.path.join(tmp_dir, "a", "b", "config.json")
            config_data = {"key": "value"}
            save_json_config(nested_path, config_data)
            assert os.path.exists(nested_path)


class TestCalculateFileChecksum:
    """Tests for calculate_file_checksum function."""

    def test_calculate_sha256_checksum(self):
        """Test calculating SHA256 checksum."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "test.txt")
            content = b"Hello, World!"
            with open(file_path, "wb") as f:
                f.write(content)

            checksum = calculate_file_checksum(file_path, algorithm="sha256")
            assert isinstance(checksum, str)
            assert len(checksum) == 64  # SHA256 hex length

    def test_calculate_md5_checksum(self):
        """Test calculating MD5 checksum."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "test.txt")
            content = b"Hello, World!"
            with open(file_path, "wb") as f:
                f.write(content)

            checksum = calculate_file_checksum(file_path, algorithm="md5")
            assert isinstance(checksum, str)
            assert len(checksum) == 32  # MD5 hex length

    def test_calculate_checksum_nonexistent_file(self):
        """Test that calculating checksum of nonexistent file raises error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "nonexistent.txt")
            with pytest.raises(FileNotFoundError):
                calculate_file_checksum(file_path)


class TestValidateDataIntegrity:
    """Tests for validate_data_integrity function."""

    def test_validate_integrity_matches(self):
        """Test validation when checksums match."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "test.txt")
            content = b"Hello, World!"
            with open(file_path, "wb") as f:
                f.write(content)

            checksum = calculate_file_checksum(file_path, algorithm="sha256")
            result = validate_data_integrity(file_path, checksum, algorithm="sha256")
            assert result is True

    def test_validate_integrity_mismatch(self):
        """Test validation when checksums do not match."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "test.txt")
            content = b"Hello, World!"
            with open(file_path, "wb") as f:
                f.write(content)

            # Use wrong checksum
            wrong_checksum = "0" * 64
            result = validate_data_integrity(file_path, wrong_checksum, algorithm="sha256")
            assert result is False

    def test_validate_integrity_nonexistent_file(self):
        """Test validation when file does not exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "nonexistent.txt")
            checksum = "0" * 64
            with pytest.raises(FileNotFoundError):
                validate_data_integrity(file_path, checksum, algorithm="sha256")
