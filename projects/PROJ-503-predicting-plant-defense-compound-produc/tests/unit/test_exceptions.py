"""
Unit tests for the custom exception classes and error handler.
"""

import pytest
import sys
from io import StringIO

# Import the modules under test
# Assuming the tests are run with PYTHONPATH set to the project root
# or using the full relative path structure if running from root.
# Based on the prompt, we assume imports work as:
from exceptions import PipelineError, E_DATASET, E_PAIRING, E_TIMEOUT, E_POWER
from error_handler import handle_error, raise_dataset_error, raise_pairing_error, raise_timeout_error, raise_power_error

class TestPipelineError:
    def test_base_exception_attributes(self):
        error = PipelineError("Test message", "E-TEST", {"key": "value"})
        assert error.message == "Test message"
        assert error.error_code == "E-TEST"
        assert error.details == {"key": "value"}
    
    def test_base_exception_str(self):
        error = PipelineError("Test message", "E-TEST")
        assert str(error) == "Test message"

class TestE_DATASET:
    def test_default_message(self):
        with pytest.raises(E_DATASET) as exc_info:
            raise_dataset_error()
        assert exc_info.value.error_code == "E-DATASET"
        assert "Dataset" in exc_info.value.message

    def test_custom_message(self):
        with pytest.raises(E_DATASET) as exc_info:
            raise_dataset_error("Custom dataset error", {"id": "GEO123"})
        assert exc_info.value.message == "Custom dataset error"
        assert exc_info.value.details == {"id": "GEO123"}

class TestE_PAIRING:
    def test_default_message(self):
        with pytest.raises(E_PAIRING) as exc_info:
            raise_pairing_error()
        assert exc_info.value.error_code == "E-PAIRING"
        assert "pairing" in exc_info.value.message.lower()

    def test_custom_message(self):
        with pytest.raises(E_PAIRING) as exc_info:
            raise_pairing_error("Custom pairing error", {"rate": 0.80})
        assert exc_info.value.message == "Custom pairing error"
        assert exc_info.value.details == {"rate": 0.80}

class TestE_TIMEOUT:
    def test_default_message(self):
        with pytest.raises(E_TIMEOUT) as exc_info:
            raise_timeout_error()
        assert exc_info.value.error_code == "E-TIMEOUT"
        assert "budget" in exc_info.value.message.lower() or "limit" in exc_info.value.message.lower()

    def test_custom_message(self):
        with pytest.raises(E_TIMEOUT) as exc_info:
            raise_timeout_error("Custom timeout", {"elapsed": 14401})
        assert exc_info.value.message == "Custom timeout"
        assert exc_info.value.details == {"elapsed": 14401}

class TestE_POWER:
    def test_default_message(self):
        with pytest.raises(E_POWER) as exc_info:
            raise_power_error()
        assert exc_info.value.error_code == "E-POWER"
        assert "Power analysis" in exc_info.value.message

    def test_custom_message(self):
        with pytest.raises(E_POWER) as exc_info:
            raise_power_error("Custom power error", {"required_n": 15, "available_n": 10})
        assert exc_info.value.message == "Custom power error"
        assert exc_info.value.details == {"required_n": 15, "available_n": 10}

class TestHandleError:
    def test_handle_error_calls_exit(self, capsys):
        error = E_DATASET("Test error", {"info": "test"})
        # We expect sys.exit to be called, so we catch SystemExit
        with pytest.raises(SystemExit) as exc_info:
            handle_error(error)
        assert exc_info.value.code == 1