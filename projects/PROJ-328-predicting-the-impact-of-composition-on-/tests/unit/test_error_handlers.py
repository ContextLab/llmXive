"""
Unit tests for the error handling infrastructure.
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
    def test_base_exception_creation(self):
        """Test basic exception creation."""
        exc = SolderPipelineError("Base error message")
        assert str(exc) == "Base error message"
    
    def test_exception_with_context(self):
        """Test exception creation with context."""
        context = {"key": "value", "number": 42}
        exc = SolderPipelineError("Error with context", context)
        assert "key=value" in str(exc)
        assert "number=42" in str(exc)


class TestDataValidationError:
    def test_inheritance(self):
        """Test that DataValidationError inherits from SolderPipelineError."""
        exc = DataValidationError("Validation failed")
        assert isinstance(exc, SolderPipelineError)
        assert isinstance(exc, DataValidationError)


class TestIngestionError:
    def test_inheritance(self):
        """Test that IngestionError inherits from SolderPipelineError."""
        exc = IngestionError("Ingestion failed")
        assert isinstance(exc, SolderPipelineError)
        assert isinstance(exc, IngestionError)


class TestModelTrainingError:
    def test_inheritance(self):
        """Test that ModelTrainingError inherits from SolderPipelineError."""
        exc = ModelTrainingError("Training failed")
        assert isinstance(exc, SolderPipelineError)
        assert isinstance(exc, ModelTrainingError)


class TestConfigurationError:
    def test_inheritance(self):
        """Test that ConfigurationError inherits from SolderPipelineError."""
        exc = ConfigurationError("Config failed")
        assert isinstance(exc, SolderPipelineError)
        assert isinstance(exc, ConfigurationError)
