"""
Tests for logging_utils.py
"""

import os
import tempfile
import logging
from pathlib import Path
import pytest

from code.utils.logging_utils import (
    configure_logging,
    generate_checksum,
    write_checksum_file,
    validate_checksum,
    log_experiment_metadata
)


class TestConfigureLogging:
    def test_console_only(self, tmp_path):
        """Test logging to console only."""
        logger = configure_logging(log_level=logging.INFO)
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0  # At least console handler

    def test_file_logging(self, tmp_path):
        """Test logging to file."""
        log_file = tmp_path / "test.log"
        logger = configure_logging(log_file=str(log_file))
        assert log_file.exists()

    def test_experiment_name_logged(self, tmp_path, caplog):
        """Test that experiment name is logged."""
        log_file = tmp_path / "test.log"
        with caplog.at_level(logging.INFO):
            configure_logging(log_file=str(log_file), experiment_name="test_exp")
            assert "Starting experiment: test_exp" in caplog.text


class TestChecksumGeneration:
    def test_generate_checksum_valid_file(self, tmp_path):
        """Test checksum generation for a valid file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        checksum = generate_checksum(str(test_file))
        assert len(checksum) == 64  # SHA256 hex length

    def test_generate_checksum_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            generate_checksum(str(tmp_path / "nonexistent.txt"))

    def test_different_content_different_checksum(self, tmp_path):
        """Test that different content produces different checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_text("Content A")
        file2.write_text("Content B")

        checksum1 = generate_checksum(str(file1))
        checksum2 = generate_checksum(str(file2))

        assert checksum1 != checksum2

    def test_same_content_same_checksum(self, tmp_path):
        """Test that same content produces same checksum."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_text("Same Content")
        file2.write_text("Same Content")

        checksum1 = generate_checksum(str(file1))
        checksum2 = generate_checksum(str(file2))

        assert checksum1 == checksum2


class TestWriteChecksumFile:
    def test_write_checksum_file(self, tmp_path):
        """Test writing checksum to file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        checksum_file = tmp_path / "checksums.txt"
        write_checksum_file(str(test_file), str(checksum_file))

        assert checksum_file.exists()
        content = checksum_file.read_text()
        assert "  test.txt" in content
        assert len(content.split()[0]) == 64  # Checksum length


class TestValidateChecksum:
    def test_validate_correct_checksum(self, tmp_path):
        """Test validation with correct checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        checksum = generate_checksum(str(test_file))
        assert validate_checksum(str(test_file), checksum) is True

    def test_validate_incorrect_checksum(self, tmp_path):
        """Test validation with incorrect checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        wrong_checksum = "a" * 64
        assert validate_checksum(str(test_file), wrong_checksum) is False


class TestLogExperimentMetadata:
    def test_log_metadata(self, tmp_path, caplog):
        """Test logging metadata."""
        logger = configure_logging(log_level=logging.INFO)
        metadata = {"param1": "value1", "param2": 42}

        with caplog.at_level(logging.INFO):
            log_experiment_metadata(logger, metadata)
            assert "param1: value1" in caplog.text
            assert "param2: 42" in caplog.text

    def test_write_metadata_to_file(self, tmp_path):
        """Test writing metadata to JSON file."""
        logger = configure_logging()
        metadata = {"param1": "value1", "param2": 42}
        output_file = tmp_path / "metadata.json"

        log_experiment_metadata(logger, metadata, str(output_file))

        assert output_file.exists()
        import json
        with open(output_file) as f:
            loaded = json.load(f)
        assert loaded["param1"] == "value1"
        assert loaded["param2"] == 42