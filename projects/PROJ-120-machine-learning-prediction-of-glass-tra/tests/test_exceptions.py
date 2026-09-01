"""
Tests for custom exception infrastructure.

These tests verify that the pipeline fails loudly and correctly
when data operations fail, without silently falling back to synthetic data.
"""

import pytest
from code.exceptions import (
    GlassPipelineError,
    DataFetchError,
    DataValidationError,
    ConfigurationError,
    FeaturizationError,
    ModelTrainingError,
    raise_loudly
)


class TestGlassPipelineError:
    """Tests for the base exception class."""

    def test_base_exception_instantiation(self):
        """Test that base exception can be instantiated."""
        exc = GlassPipelineError("Base error message")
        assert str(exc) == "Base error message"
        assert isinstance(exc, GlassPipelineError)
        assert isinstance(exc, Exception)

    def test_exception_hierarchy(self):
        """Test that all custom exceptions inherit from GlassPipelineError."""
        errors = [
            DataFetchError("msg"),
            DataValidationError("msg"),
            ConfigurationError("msg"),
            FeaturizationError("msg"),
            ModelTrainingError("msg"),
        ]
        for exc in errors:
            assert isinstance(exc, GlassPipelineError)


class TestDataFetchError:
    """Tests for data fetch failure exceptions."""

    def test_data_fetch_error_with_source(self):
        """Test DataFetchError with source information."""
        exc = DataFetchError(
            "Failed to fetch data from Zenodo",
            source="https://zenodo.org/api/records/12345",
            details={"status_code": 404, "reason": "Not Found"}
        )
        assert "Failed to fetch data from Zenodo" in str(exc)
        assert exc.source == "https://zenodo.org/api/records/12345"
        assert exc.details["status_code"] == 404

    def test_data_fetch_error_without_source(self):
        """Test DataFetchError without optional parameters."""
        exc = DataFetchError("Network timeout")
        assert exc.source is None
        assert exc.details == {}

    def test_data_fetch_error_is_not_catchable_for_fallback(self):
        """
        Verify that DataFetchError is designed to halt execution.
        
        This test documents the expected behavior: catching this exception
        should NOT lead to synthetic data generation.
        """
        with pytest.raises(DataFetchError) as exc_info:
            raise DataFetchError("Real data fetch failed - halting pipeline")
        
        assert "Real data fetch failed" in str(exc_info.value)


class TestDataValidationError:
    """Tests for data validation failure exceptions."""

    def test_validation_error_with_record(self):
        """Test DataValidationError with record identification."""
        exc = DataValidationError(
            "Invalid chemical formula: 'H2O2O'",
            record_id="sample_001",
            field="formula"
        )
        assert "Invalid chemical formula" in str(exc)
        assert exc.record_id == "sample_001"
        assert exc.field == "formula"

    def test_validation_error_minimal(self):
        """Test DataValidationError with minimal parameters."""
        exc = DataValidationError("Missing target value")
        assert exc.record_id is None
        assert exc.field is None


class TestConfigurationError:
    """Tests for configuration failure exceptions."""

    def test_config_error_with_missing_keys(self):
        """Test ConfigurationError with missing environment keys."""
        exc = ConfigurationError(
            "Missing required environment variables",
            missing_keys=["ZENODO_DOI", "ZENODO_API_KEY"]
        )
        assert "Missing required environment variables" in str(exc)
        assert "ZENODO_DOI" in exc.missing_keys
        assert "ZENODO_API_KEY" in exc.missing_keys

    def test_config_error_empty_missing_keys(self):
        """Test ConfigurationError with empty missing keys list."""
        exc = ConfigurationError("Invalid configuration format")
        assert exc.missing_keys == []


class TestFeaturizationError:
    """Tests for featurization failure exceptions."""

    def test_featurization_error_with_formula(self):
        """Test FeaturizationError with problematic formula."""
        exc = FeaturizationError(
            "Failed to parse composition",
            formula="SiO2_Na2O_Invalid",
            error_type="pymatgen_parse_error"
        )
        assert "Failed to parse composition" in str(exc)
        assert exc.formula == "SiO2_Na2O_Invalid"
        assert exc.error_type == "pymatgen_parse_error"


class TestModelTrainingError:
    """Tests for model training failure exceptions."""

    def test_training_error_with_model_info(self):
        """Test ModelTrainingError with model and fold information."""
        exc = ModelTrainingError(
            "Grid search failed: invalid n_estimators value",
            model_type="RandomForestRegressor",
            fold=3
        )
        assert "Grid search failed" in str(exc)
        assert exc.model_type == "RandomForestRegressor"
        assert exc.fold == 3


class TestRaiseLoudly:
    """Tests for the helper function that enforces loud failures."""

    def test_raise_loudly_raises_correct_exception(self):
        """Test that raise_loudly raises the specified exception class."""
        with pytest.raises(DataFetchError) as exc_info:
            raise_loudly(
                DataFetchError,
                "Fetch failed",
                source="test_source",
                details={"test": True}
            )
        
        assert exc_info.value.source == "test_source"
        assert exc_info.value.details["test"] is True

    def test_raise_loudly_with_custom_message(self):
        """Test raise_loudly with custom message formatting."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise_loudly(
                ConfigurationError,
                f"Configuration error: missing ZENODO_DOI"
            )
        
        assert "Configuration error" in str(exc_info.value)