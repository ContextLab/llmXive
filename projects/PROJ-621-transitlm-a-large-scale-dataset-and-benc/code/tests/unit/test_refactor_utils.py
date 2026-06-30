"""
Unit tests for refactoring utilities.
"""
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import logging
import time

from src.lib.refactor_utils import (
    log_execution_time,
    validate_path_exists,
    sanitize_string,
    safe_get,
    normalize_whitespace,
    chunk_list,
    format_duration,
    ConfigValidator
)

@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestLogExecutionTime:
    def test_successful_execution_logs_time(self, caplog):
        caplog.set_level(logging.INFO)
        logger = logging.getLogger(__name__)
        
        @log_execution_time(logger)
        def test_func():
            time.sleep(0.1)
            return "success"
        
        result = test_func()
        assert result == "success"
        assert any("completed in" in record.message for record in caplog.records)

    def test_failed_execution_logs_error(self, caplog):
        caplog.set_level(logging.ERROR)
        logger = logging.getLogger(__name__)
        
        @log_execution_time(logger)
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_func()
        
        assert any("failed" in record.message for record in caplog.records)

class TestValidatePathExists:
    def test_existing_file(self, temp_dir):
        file_path = temp_dir / "test.txt"
        file_path.touch()
        validate_path_exists(file_path, must_be_file=True)

    def test_existing_dir(self, temp_dir):
        validate_path_exists(temp_dir, must_be_dir=True)

    def test_nonexistent_path(self, temp_dir):
        with pytest.raises(FileNotFoundError):
            validate_path_exists(temp_dir / "nonexistent.txt")

    def test_file_instead_of_dir(self, temp_dir):
        file_path = temp_dir / "test.txt"
        file_path.touch()
        with pytest.raises(ValueError):
            validate_path_exists(file_path, must_be_dir=True)

class TestSanitizeString:
    def test_default_allowed_chars(self):
        assert sanitize_string("Hello World!") == "Hello_World_"
        assert sanitize_string("test-case_123") == "test-case_123"

    def test_custom_allowed_chars(self):
        assert sanitize_string("abc123xyz", allowed_chars="abc123") == "abc123"
        assert sanitize_string("abc-123", allowed_chars="abc123-") == "abc-123"

    def test_collapse_multiple_underscores(self):
        assert sanitize_string("a__b___c") == "a_b_c"

    def test_strip_leading_trailing_underscores(self):
        assert sanitize_string("__test__") == "test"

class TestSafeGet:
    def test_simple_key(self):
        data = {"key": "value"}
        assert safe_get(data, "key") == "value"

    def test_nested_key(self):
        data = {"level1": {"level2": "value"}}
        assert safe_get(data, "level1.level2") == "value"

    def test_missing_key(self):
        data = {"key": "value"}
        assert safe_get(data, "missing") is None

    def test_missing_key_with_default(self):
        data = {"key": "value"}
        assert safe_get(data, "missing", "default") == "default"

    def test_empty_key(self):
        data = {"key": "value"}
        assert safe_get(data, "") is None

class TestNormalizeWhitespace:
    def test_multiple_spaces(self):
        assert normalize_whitespace("Hello   World") == "Hello World"

    def test_newlines_and_tabs(self):
        assert normalize_whitespace("Hello\n\nWorld\t\tTest") == "Hello World Test"

    def test_already_normalized(self):
        assert normalize_whitespace("Hello World") == "Hello World"

class TestChunkList:
    def test_basic_chunking(self):
        assert chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

    def test_exact_chunks(self):
        assert chunk_list([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]

    def test_single_chunk(self):
        assert chunk_list([1, 2, 3], 10) == [[1, 2, 3]]

    def test_invalid_chunk_size(self):
        with pytest.raises(ValueError):
            chunk_list([1, 2, 3], 0)

class TestFormatDuration:
    def test_seconds(self):
        assert format_duration(30.5) == "30.50s"

    def test_minutes(self):
        assert format_duration(90.5) == "1m 30.5s"

    def test_hours(self):
        assert format_duration(3661.5) == "1h 1m 1.5s"

class TestConfigValidator:
    def test_valid_config(self):
        config = {"key1": "value", "key2": 123}
        validator = ConfigValidator(config)
        validator.require("key1").require("key2", int)
        assert validator.validate()
        assert validator.get_errors() == []

    def test_missing_required_key(self):
        config = {"key1": "value"}
        validator = ConfigValidator(config)
        validator.require("missing_key")
        assert not validator.validate()
        assert "Missing required configuration key: missing_key" in validator.get_errors()

    def test_wrong_type(self):
        config = {"key1": "value"}
        validator = ConfigValidator(config)
        validator.require("key1", int)
        assert not validator.validate()
        assert any("must be of type int" in err for err in validator.get_errors())

    def test_optional_key_with_default(self):
        config = {}
        validator = ConfigValidator(config)
        validator.optional("missing_key", str, "default")
        assert validator.validate()

    def test_raise_if_invalid(self):
        config = {"key1": "value"}
        validator = ConfigValidator(config)
        validator.require("missing_key")
        with pytest.raises(ValueError, match="Configuration validation failed"):
            validator.raise_if_invalid()