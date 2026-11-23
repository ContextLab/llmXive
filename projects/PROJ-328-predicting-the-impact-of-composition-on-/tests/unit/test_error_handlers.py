"""
Unit tests for error handling infrastructure.
"""
import pytest
from utils.error_handlers import (
    SolderPipelineError,
    DataValidationError,
    IngestionError,
    ModelTrainingError,
    ConfigurationError
)


class TestSolderPipelineError:
    def test_base_exception(self):
        error = SolderPipelineError("Base error message")
        assert str(error) == "Base error message"
        assert error.context == {}

    def test_base_exception_with_context(self):
        ctx = {"param": "value"}
        error = SolderPipelineError("Base error message", context=ctx)
        assert error.context == ctx


class TestDataValidationError:
    def test_inheritance(self):
        error = DataValidationError("Validation failed")
        assert isinstance(error, SolderPipelineError)


class TestIngestionError:
    def test_inheritance(self):
        error = IngestionError("Source failed")
        assert isinstance(error, SolderPipelineError)


class TestModelTrainingError:
    def test_inheritance(self):
        error = ModelTrainingError("Training crashed")
        assert isinstance(error, SolderPipelineError)


class TestConfigurationError:
    def test_inheritance(self):
        error = ConfigurationError("Config missing")
        assert isinstance(error, SolderPipelineError)
