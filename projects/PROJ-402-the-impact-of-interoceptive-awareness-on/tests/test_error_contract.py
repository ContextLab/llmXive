"""
Tests for the Error Contract Module (T004).

Tests cover:
1. Checksum calculation correctness.
2. Schema loading and basic validation.
3. Download behavior with timeouts and HTTP errors.
4. Checksum mismatch detection.
5. Schema mismatch detection.
"""

import os
import sys
import tempfile
import time
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Import the module under test
# Note: Adjust import path if running from different directory
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
from utils.error_contract import (
    ContractViolationError,
    calculate_checksum,
    load_schema,
    validate_schema,
    download_with_contract,
    enforce_error_contract
)


class TestChecksumCalculation:
    def test_calculate_checksum_correctness(self):
        """Test that checksum is calculated correctly."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            content = b"Hello, World! This is a test file."
            f.write(content)
            f.flush()
            temp_path = Path(f.name)

        try:
            expected_hash = hashlib.sha256(content).hexdigest()
            actual_hash = calculate_checksum(temp_path)
            assert actual_hash == expected_hash
        finally:
            os.unlink(temp_path)

    def test_calculate_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_checksum(Path("non_existent_file.txt"))


class TestSchemaLoading:
    def test_load_schema_success(self, tmp_path):
        """Test loading a valid YAML schema."""
        schema_content = {"type": "csv", "required_columns": ["id", "value"]}
        schema_file = tmp_path / "schema.yaml"
        schema_file.write_text(yaml.dump(schema_content))

        loaded = load_schema(schema_file)
        assert loaded == schema_content

    def test_load_schema_file_not_found(self):
        """Test that FileNotFoundError is raised for missing schema."""
        with pytest.raises(FileNotFoundError):
            load_schema(Path("non_existent_schema.yaml"))


class TestSchemaValidation:
    def test_validate_csv_schema_success(self, tmp_path):
        """Test successful CSV schema validation."""
        # Create schema
        schema = {"type": "csv", "required_columns": ["id", "value"]}

        # Create data
        data_path = tmp_path / "data.csv"
        data_path.write_text("id,value\n1,10\n2,20\n")

        is_valid, error = validate_schema(data_path, schema)
        assert is_valid
        assert error is None

    def test_validate_csv_schema_failure(self, tmp_path):
        """Test failed CSV schema validation (missing column)."""
        schema = {"type": "csv", "required_columns": ["id", "value", "missing_col"]}
        data_path = tmp_path / "data.csv"
        data_path.write_text("id,value\n1,10\n")

        is_valid, error = validate_schema(data_path, schema)
        assert not is_valid
        assert "missing_col" in error

    def test_validate_file_not_found(self, tmp_path):
        """Test validation fails if data file is missing."""
        schema = {"type": "csv", "required_columns": ["id"]}
        is_valid, error = validate_schema(Path("non_existent.csv"), schema)
        assert not is_valid
        assert "does not exist" in error


class TestDownloadWithContract:
    @pytest.fixture
    def mock_response(self):
        """Mock requests.Response."""
        mock = MagicMock()
        mock.status_code = 200
        mock.iter_content = lambda chunk_size: [b"test content"]
        return mock

    @patch('utils.error_contract.requests.get')
    def test_download_success(self, mock_get, mock_response, tmp_path):
        """Test successful download."""
        mock_get.return_value = mock_response
        output_path = tmp_path / "downloaded.txt"

        result = download_with_contract("http://example.com/file.txt", output_path)

        assert result.exists()
        assert result.read_bytes() == b"test content"

    @patch('utils.error_contract.requests.get')
    def test_download_404(self, mock_get, tmp_path):
        """Test 404 error raises ContractViolationError."""
        mock = MagicMock()
        mock.status_code = 404
        mock.raise_for_status.side_effect = Exception("404") # requests usually raises on 404 if check=True, but we handle status manually
        mock_get.return_value = mock

        output_path = tmp_path / "downloaded.txt"
        with pytest.raises(ContractViolationError) as exc_info:
            download_with_contract("http://example.com/missing.txt", output_path)
        assert "404" in str(exc_info.value)

    @patch('utils.error_contract.requests.get')
    def test_download_timeout(self, mock_get, tmp_path):
        """Test timeout raises ContractViolationError."""
        mock_get.side_effect = Exception("Timeout") # Simulate timeout exception
        # Or use requests.exceptions.Timeout
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        output_path = tmp_path / "downloaded.txt"
        with pytest.raises(ContractViolationError) as exc_info:
            download_with_contract("http://example.com/slow.txt", output_path, timeout=1)
        assert "timed out" in str(exc_info.value).lower()

    def test_download_checksum_mismatch(self, tmp_path):
        """Test checksum mismatch raises ContractViolationError."""
        # Create a fake file to simulate download
        output_path = tmp_path / "fake_download.txt"
        output_path.write_text("content")

        # We can't easily test the full download flow with checksum mismatch
        # without mocking the response content.
        # Instead, we test the logic by creating a file with wrong checksum
        # and calling the validation part manually or mocking the response.

        # Let's mock the response to return specific content
        with patch('utils.error_contract.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.iter_content = lambda cs: [b"wrong content"]
            mock_get.return_value = mock_resp

            output_path = tmp_path / "downloaded.txt"
            # Calculate checksum of "wrong content"
            wrong_checksum = hashlib.sha256(b"wrong content").hexdigest()
            # Provide a different expected checksum
            with pytest.raises(ContractViolationError) as exc_info:
                download_with_contract(
                    "http://example.com/file.txt",
                    output_path,
                    expected_checksum="different_checksum"
                )
            assert "Checksum mismatch" in str(exc_info.value)


class TestEnforceErrorContract:
    def test_decorator_catches_contract_violation(self):
        """Test that decorator catches ContractViolationError and exits."""
        def failing_func():
            raise ContractViolationError("Test violation")

        decorated = enforce_error_contract(failing_func)

        with patch('sys.exit') as mock_exit:
            decorated()
            mock_exit.assert_called_once_with(1)

    def test_decorator_catches_unexpected_error(self):
        """Test that decorator catches unexpected errors and exits."""
        def failing_func():
            raise ValueError("Unexpected error")

        decorated = enforce_error_contract(failing_func)

        with patch('sys.exit') as mock_exit:
            decorated()
            mock_exit.assert_called_once_with(1)
