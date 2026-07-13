"""
Unit tests for code/data_utils.py
"""
import os
import json
import tempfile
import pytest
import pandas as pd
from unittest.mock import patch

from data_utils import (
    calculate_checksum,
    verify_checksum,
    load_draws_csv,
    save_checksums_file,
    load_checksums_file
)
from exceptions import LotteryDataError  # Assuming this exists as per API surface


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("draw_date,numbers,jackpot\n")
        f.write("2023-01-01,\"[1,2,3,4,5,6]\",1000000\n")
        f.write("2023-01-08,\"[7,8,9,10,11,12]\",2000000\n")
        f.write("2023-01-15,\"[13,14,15,16,17,18]\",3000000\n")
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def empty_csv_file():
    """Create an empty temporary CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("")
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def temp_checksum_file():
    """Create a temporary JSON file for checksums."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"test.csv": "abc123"}, f)
        path = f.name
    yield path
    os.unlink(path)


def test_calculate_checksum(tmp_path):
    """Test checksum calculation."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello, World!")

    checksum = calculate_checksum(str(file_path))
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)


def test_calculate_checksum_file_not_found():
    """Test checksum calculation on non-existent file."""
    with pytest.raises(FileNotFoundError):
        calculate_checksum("/non/existent/file.txt")


def test_calculate_checksum_invalid_algorithm(tmp_path):
    """Test checksum calculation with invalid algorithm."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Data")
    with pytest.raises(ValueError):
        calculate_checksum(str(file_path), algorithm='invalid_algo')


def test_verify_checksum_positive(tmp_path):
    """Test checksum verification with matching checksum."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Data")
    correct_checksum = calculate_checksum(str(file_path))

    assert verify_checksum(str(file_path), correct_checksum) is True


def test_verify_checksum_negative(tmp_path):
    """Test checksum verification with mismatched checksum."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Data")
    wrong_checksum = "a" * 64

    assert verify_checksum(str(file_path), wrong_checksum) is False


def test_verify_checksum_file_not_found():
    """Test checksum verification on non-existent file."""
    with pytest.raises(FileNotFoundError):
        verify_checksum("/non/existent/file.txt", "abc123")


def test_load_draws_csv_basic(temp_csv_file):
    """Test basic CSV loading."""
    df, msg = load_draws_csv(temp_csv_file)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert 'draw_date' in df.columns
    assert 'jackpot' in df.columns
    # Check sorting
    assert df['draw_date'].is_monotonic_increasing


def test_load_draws_csv_checksum_match(temp_csv_file):
    """Test CSV loading with correct checksum."""
    expected_checksum = calculate_checksum(temp_csv_file)
    df, msg = load_draws_csv(temp_csv_file, checksum=expected_checksum)

    assert df is not None
    assert "PASSED" in msg


def test_load_draws_csv_checksum_fail_strict(temp_csv_file):
    """Test CSV loading with wrong checksum in strict mode."""
    wrong_checksum = "a" * 64
    with pytest.raises(ValueError, match="Checksum verification FAILED"):
        load_draws_csv(temp_csv_file, checksum=wrong_checksum, strict=True)


def test_load_draws_csv_checksum_fail_non_strict(temp_csv_file):
    """Test CSV loading with wrong checksum in non-strict mode."""
    wrong_checksum = "a" * 64
    df, msg = load_draws_csv(temp_csv_file, checksum=wrong_checksum, strict=False)

    assert df is not None
    assert "WARNING" in msg
    assert "FAILED" in msg


def test_load_draws_csv_empty_file(empty_csv_file):
    """Test CSV loading on empty file."""
    with pytest.raises(ValueError, match="CSV file is empty"):
        load_draws_csv(empty_csv_file)


def test_save_and_load_checksums_file(tmp_path):
    """Test saving and loading checksums."""
    test_data = {"file1.csv": "abc123", "file2.csv": "def456"}
    output_path = str(tmp_path / "checksums.json")

    save_checksums_file(test_data, output_path)
    loaded_data = load_checksums_file(output_path)

    assert loaded_data == test_data


def test_load_checksums_file_not_found():
    """Test loading checksums from non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_checksums_file("/non/existent/checksums.json")