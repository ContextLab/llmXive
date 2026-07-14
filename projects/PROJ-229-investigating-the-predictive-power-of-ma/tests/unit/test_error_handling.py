import pytest
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.error_handling import (
    PipelineError,
    DataFetchError,
    DataProcessingError,
    ModelTrainingError,
    ConfigError,
    handle_error,
    validate_not_null,
    validate_positive
)
from code.utils.logger import setup_logger

class TestExceptionHierarchy:
    def test_pipeline_error_is_exception(self):
        assert issubclass(PipelineError, Exception)

    def test_data_fetch_error_is_pipeline_error(self):
        assert issubclass(DataFetchError, PipelineError)

    def test_data_processing_error_is_pipeline_error(self):
        assert issubclass(DataProcessingError, PipelineError)

    def test_model_training_error_is_pipeline_error(self):
        assert issubclass(ModelTrainingError, PipelineError)

    def test_config_error_is_pipeline_error(self):
        assert issubclass(ConfigError, PipelineError)

class TestHandleError:
    def test_handle_error_custom_logger(self):
        logger = setup_logger(name="test_handle", level=logging.DEBUG)
        error = ValueError("Test")
        
        # Should not raise since reraise defaults to True, but we catch it
        with pytest.raises(ValueError):
            handle_error(error, context="Unit Test", logger=logger)

    def test_handle_error_default_logger(self):
        # This will use the global logger if available, or setup a fallback
        error = ValueError("Test")
        with pytest.raises(ValueError):
            handle_error(error, context="Unit Test", reraise=True)

class TestValidations:
    def test_validate_not_null_none(self):
        logger = setup_logger(name="test_val_null", level=logging.ERROR)
        with pytest.raises(DataProcessingError):
            validate_not_null(None, "test_var", logger=logger)

    def test_validate_not_null_valid(self):
        logger = setup_logger(name="test_val_valid", level=logging.ERROR)
        # Should pass silently
        validate_not_null("data", "test_var", logger=logger)

    def test_validate_positive_zero(self):
        logger = setup_logger(name="test_pos_zero", level=logging.ERROR)
        with pytest.raises(DataProcessingError):
            validate_positive(0, "test_var", logger=logger)

    def test_validate_positive_negative(self):
        logger = setup_logger(name="test_pos_neg", level=logging.ERROR)
        with pytest.raises(DataProcessingError):
            validate_positive(-1, "test_var", logger=logger)

    def test_validate_positive_positive(self):
        logger = setup_logger(name="test_pos_ok", level=logging.ERROR)
        # Should pass
        validate_positive(1, "test_var", logger=logger)
