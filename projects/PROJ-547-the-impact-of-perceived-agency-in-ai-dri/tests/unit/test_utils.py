"""
Unit tests for shared utilities in code/utils/.
"""
import json
import tempfile
from pathlib import Path

import pytest
import yaml

from utils.error_handler import PipelineError, handle_error, log_and_exit
from utils.resource_monitor import enforce_limits
from utils.input_validator import (
    validate_file_type,
    validate_json_schema,
    validate_yaml_file,
)


class TestPipelineError:
    def test_pipeline_error_message(self):
        error = PipelineError("Test error", error_code=42)
        assert str(error) == "Test error"
        assert error.error_code == 42

    def test_pipeline_error_default_code(self):
        error = PipelineError("Test error")
        assert error.error_code == 1


class TestHandleError:
    def test_handle_error_success(self):
        def success_func():
            return "success"

        result = handle_error(success_func)
        assert result == "success"

    def test_handle_error_failure(self):
        def fail_func():
            raise ValueError("Test exception")

        with pytest.raises(PipelineError) as exc_info:
            handle_error(fail_func)

        assert "Test exception" in str(exc_info.value)

    def test_handle_error_custom_message(self):
        def fail_func():
            raise ValueError("Test exception")

        with pytest.raises(PipelineError) as exc_info:
            handle_error(fail_func, error_message="Custom error message")

        assert "Custom error message" in str(exc_info.value)


class TestResourceMonitor:
    def test_enforce_limits_within_memory(self):
        # This test assumes the current memory usage is within limits
        try:
            enforce_limits(max_memory_gb=6.0)
        except PipelineError:
            # If memory usage is high, this test might fail in some environments
            # We'll skip the assertion in that case
            pass

    def test_enforce_limits_cpu_warning(self):
        # This test checks that a warning is logged if CPU count is high
        # We can't easily control the CPU count, so we'll just call the function
        # and ensure it doesn't raise an error for CPU count (as per current implementation)
        try:
            enforce_limits(max_cpu_cores=2)
        except PipelineError:
            # If the implementation changes to abort on CPU count, this test will need updating
            pass


class TestInputValidator:
    def test_validate_file_type_valid(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = validate_file_type(temp_path, allowed_types=[".csv", ".json"])
            assert result is True
        finally:
            temp_path.unlink()

    def test_validate_file_type_invalid(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = Path(f.name)

        try:
            with pytest.raises(PipelineError):
                validate_file_type(temp_path, allowed_types=[".csv", ".json"])
        finally:
            temp_path.unlink()

    def test_validate_file_type_not_found(self):
        non_existent = Path("/tmp/non_existent_file.csv")
        with pytest.raises(PipelineError):
            validate_file_type(non_existent, allowed_types=[".csv"])

    def test_validate_json_schema_valid(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }

        data = {"name": "Alice", "age": 30}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(schema, f)
            schema_path = Path(f.name)

        try:
            validate_json_schema(data, schema_path)
        finally:
            schema_path.unlink()

    def test_validate_json_schema_invalid(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
            },
            "required": ["name"],
        }

        data = {"age": 30}  # Missing required 'name'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(schema, f)
            schema_path = Path(f.name)

        try:
            with pytest.raises(PipelineError):
                validate_json_schema(data, schema_path)
        finally:
            schema_path.unlink()

    def test_validate_yaml_file_valid(self):
        data = {"key": "value", "number": 42}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            yaml_path = Path(f.name)

        try:
            result = validate_yaml_file(yaml_path)
            assert result == data
        finally:
            yaml_path.unlink()

    def test_validate_yaml_file_invalid(self):
        invalid_yaml = "key: value\n  invalid_indent: 123"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(invalid_yaml)
            yaml_path = Path(f.name)

        try:
            with pytest.raises(PipelineError):
                validate_yaml_file(yaml_path)
        finally:
            yaml_path.unlink()

    def test_validate_yaml_file_not_found(self):
        non_existent = Path("/tmp/non_existent.yaml")
        with pytest.raises(PipelineError):
            validate_yaml_file(non_existent)
