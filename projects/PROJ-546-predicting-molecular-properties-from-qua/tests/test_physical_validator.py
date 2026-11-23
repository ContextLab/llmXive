"""
Unit tests for the physical_validator module.

Tests validate the HOMO-LUMO energy relationship checking functionality,
logging behavior, and file processing capabilities.
"""

import csv
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from physical_validator import (
    validate_homo_lumo_relationship,
    log_structural_failure,
    validate_descriptors_file,
    setup_logger
)


class TestHomoLumoValidation:
    """Tests for the HOMO-LUMO relationship validation function."""

    def test_valid_homo_lumo_relationship(self):
        """Test that valid HOMO < LUMO returns True."""
        is_valid, message = validate_homo_lumo_relationship(-6.5, -2.3)
        assert is_valid is True
        assert "PASSED" in message
        assert "-6.5" in message
        assert "-2.3" in message

    def test_invalid_homo_equal_lumo(self):
        """Test that HOMO == LUMO is invalid."""
        is_valid, message = validate_homo_lumo_relationship(-5.0, -5.0)
        assert is_valid is False
        assert "FAILED" in message

    def test_invalid_homo_greater_than_lumo(self):
        """Test that HOMO > LUMO is invalid."""
        is_valid, message = validate_homo_lumo_relationship(-3.0, -5.0)
        assert is_valid is False
        assert "FAILED" in message

    def test_positive_energies_valid(self):
        """Test validation with positive energy values."""
        is_valid, message = validate_homo_lumo_relationship(1.0, 3.0)
        assert is_valid is True

    def test_negative_energies_invalid(self):
        """Test validation with both negative but invalid ordering."""
        is_valid, message = validate_homo_lumo_relationship(-1.0, -3.0)
        assert is_valid is False


class TestLoggerSetup:
    """Tests for logger configuration."""

    def test_logger_creates_file_handler(self, tmp_path):
        """Test that setup_logger creates a file handler."""
        log_file = tmp_path / "test.log"
        logger = setup_logger(str(log_file))

        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.FileHandler)
        assert logger.handlers[0].baseFilename == str(log_file)

    def test_logger_format(self, tmp_path):
        """Test that logger has correct format."""
        log_file = tmp_path / "test.log"
        logger = setup_logger(str(log_file))

        formatter = logger.handlers[0].formatter
        assert "%(asctime)s - %(levelname)s - %(message)s" == formatter._fmt


class TestStructuralFailureLogging:
    """Tests for structural failure logging."""

    def test_log_structural_failure_creates_entry(self, tmp_path):
        """Test that log_structural_failure writes to log file."""
        log_file = tmp_path / "failures.log"
        logger = setup_logger(str(log_file))

        log_structural_failure(
            logger,
            molecule_id="mol_001",
            homo_energy=-5.0,
            lumo_energy=-4.0,
            source_file="test.csv",
            row_index=10
        )

        # Read log file and verify content
        with open(log_file, 'r') as f:
            content = f.read()

        assert "mol_001" in content
        assert "-5.0" in content
        assert "-4.0" in content
        assert "failed_after_retry" in content
        assert "Source: test.csv" in content
        assert "Row: 10" in content


class TestDescriptorsFileValidation:
    """Tests for the main validation function."""

    def create_test_csv(self, tmp_path, rows, filename="test.csv"):
        """Helper to create a test CSV file."""
        file_path = tmp_path / filename
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["molecule_id", "HOMO_energy", "LUMO_energy", "other"])
            writer.writeheader()
            writer.writerows(rows)
        return str(file_path)

    def test_valid_file_all_passes(self, tmp_path):
        """Test validation with all valid records."""
        rows = [
            {"molecule_id": "mol_001", "HOMO_energy": -6.5, "LUMO_energy": -2.3, "other": "data1"},
            {"molecule_id": "mol_002", "HOMO_energy": -5.0, "LUMO_energy": -1.0, "other": "data2"},
            {"molecule_id": "mol_003", "HOMO_energy": -7.2, "LUMO_energy": -3.5, "other": "data3"},
        ]
        input_file = self.create_test_csv(tmp_path, rows)
        output_file = str(tmp_path / "output.csv")

        total, valid, failed = validate_descriptors_file(
            input_file=input_file,
            output_file=output_file,
            homo_column="HOMO_energy",
            lumo_column="LUMO_energy",
            id_column="molecule_id"
        )

        assert total == 3
        assert valid == 3
        assert len(failed) == 0

        # Verify output file
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            output_rows = list(reader)
        assert len(output_rows) == 3

    def test_file_with_invalid_records(self, tmp_path):
        """Test validation with some invalid records."""
        rows = [
            {"molecule_id": "mol_001", "HOMO_energy": -6.5, "LUMO_energy": -2.3, "other": "data1"},
            {"molecule_id": "mol_002", "HOMO_energy": -3.0, "LUMO_energy": -5.0, "other": "data2"},  # Invalid
            {"molecule_id": "mol_003", "HOMO_energy": -5.0, "LUMO_energy": -5.0, "other": "data3"},  # Invalid (equal)
            {"molecule_id": "mol_004", "HOMO_energy": -4.0, "LUMO_energy": -1.0, "other": "data4"},
        ]
        input_file = self.create_test_csv(tmp_path, rows)
        output_file = str(tmp_path / "output.csv")

        total, valid, failed = validate_descriptors_file(
            input_file=input_file,
            output_file=output_file,
            homo_column="HOMO_energy",
            lumo_column="LUMO_energy",
            id_column="molecule_id"
        )

        assert total == 4
        assert valid == 2
        assert len(failed) == 2

        # Verify only valid records in output
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            output_rows = list(reader)
        assert len(output_rows) == 2
        assert output_rows[0]["molecule_id"] == "mol_001"
        assert output_rows[1]["molecule_id"] == "mol_004"

    def test_non_numeric_values_handled(self, tmp_path):
        """Test that non-numeric energy values are handled gracefully."""
        rows = [
            {"molecule_id": "mol_001", "HOMO_energy": -6.5, "LUMO_energy": -2.3, "other": "data1"},
            {"molecule_id": "mol_002", "HOMO_energy": "invalid", "LUMO_energy": -5.0, "other": "data2"},
            {"molecule_id": "mol_003", "HOMO_energy": -4.0, "LUMO_energy": None, "other": "data3"},
        ]
        input_file = self.create_test_csv(tmp_path, rows)
        output_file = str(tmp_path / "output.csv")

        total, valid, failed = validate_descriptors_file(
            input_file=input_file,
            output_file=output_file,
            homo_column="HOMO_energy",
            lumo_column="LUMO_energy",
            id_column="molecule_id"
        )

        assert total == 3
        assert valid == 1
        assert len(failed) == 2

    def test_missing_columns_raises_error(self, tmp_path):
        """Test that missing required columns raise an error."""
        rows = [
            {"molecule_id": "mol_001", "HOMO_energy": -6.5},
        ]
        input_file = self.create_test_csv(tmp_path, rows)

        with pytest.raises(ValueError, match="Missing required columns"):
            validate_descriptors_file(
                input_file=input_file,
                output_file=str(tmp_path / "output.csv"),
                homo_column="HOMO_energy",
                lumo_column="LUMO_energy",
                id_column="molecule_id"
            )

    def test_file_not_found_raises_error(self, tmp_path):
        """Test that missing input file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            validate_descriptors_file(
                input_file=str(tmp_path / "nonexistent.csv"),
                output_file=str(tmp_path / "output.csv")
            )

    def test_empty_file(self, tmp_path):
        """Test validation of an empty file (only headers)."""
        rows = []
        input_file = self.create_test_csv(tmp_path, rows)
        output_file = str(tmp_path / "output.csv")

        total, valid, failed = validate_descriptors_file(
            input_file=input_file,
            output_file=output_file,
            homo_column="HOMO_energy",
            lumo_column="LUMO_energy",
            id_column="molecule_id"
        )

        assert total == 0
        assert valid == 0
        assert len(failed) == 0


class TestMainFunction:
    """Tests for the main() entry point."""

    def test_main_validates_file(self, tmp_path, capsys):
        """Test that main() correctly validates a file."""
        rows = [
            {"molecule_id": "mol_001", "HOMO_energy": -6.5, "LUMO_energy": -2.3},
            {"molecule_id": "mol_002", "HOMO_energy": -3.0, "LUMO_energy": -5.0},
        ]
        input_file = self.create_test_csv(tmp_path, rows)
        output_file = str(tmp_path / "output.csv")

        with patch('sys.argv', [
            'physical_validator.py',
            '--input', input_file,
            '--output', output_file
        ]):
            from physical_validator import main
            main()

        captured = capsys.readouterr()
        assert "Validation complete" in captured.out
        assert "Total rows processed: 2" in captured.out
        assert "Valid rows: 1" in captured.out
        assert "Failed rows: 1" in captured.out

    def test_main_missing_file_exits_with_error(self, tmp_path, capsys):
        """Test that main() exits with error for missing file."""
        with patch('sys.argv', [
            'physical_validator.py',
            '--input', str(tmp_path / "nonexistent.csv")
        ]):
            from physical_validator import main
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1