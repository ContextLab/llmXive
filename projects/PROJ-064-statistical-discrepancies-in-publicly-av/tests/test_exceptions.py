"""
Unit tests for custom exception classes.
"""
import pytest
from exceptions import (
    DiscrepancyError,
    DataAcquisitionError,
    MissingDataError,
    ValidationFailureError,
    StatisticalModelError,
    ConfigurationError,
    ReproducibilityError
)

class TestDiscrepancyError:
    """Tests for base DiscrepancyError class."""
    
    def test_basic_initialization(self):
        """Test basic error initialization."""
        error = DiscrepancyError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.code is None
        assert error.context == {}
    
    def test_with_code(self):
        """Test error with code."""
        error = DiscrepancyError("Error with code", code="TEST_001")
        
        assert str(error) == "[TEST_001] Error with code"
        assert error.code == "TEST_001"
    
    def test_with_context(self):
        """Test error with context."""
        context = {"key1": "value1", "key2": 123}
        error = DiscrepancyError("Error with context", context=context)
        
        assert error.context == context
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        error = DiscrepancyError(
            "Test error",
            code="TEST_001",
            context={"field": "value"}
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["type"] == "DiscrepancyError"
        assert error_dict["message"] == "Test error"
        assert error_dict["code"] == "TEST_001"
        assert error_dict["context"] == {"field": "value"}

class TestDataAcquisitionError:
    """Tests for DataAcquisitionError class."""
    
    def test_basic_initialization(self):
        """Test basic initialization."""
        error = DataAcquisitionError("Download failed")
        
        assert "Download failed" in str(error)
        assert error.source is None
        assert error.reason is None
    
    def test_with_source(self):
        """Test with source information."""
        error = DataAcquisitionError("Download failed", source="https://example.com")
        
        assert "Source: https://example.com" in str(error)
        assert error.source == "https://example.com"
    
    def test_with_reason(self):
        """Test with reason information."""
        error = DataAcquisitionError("Download failed", reason="Connection timeout")
        
        assert "Reason: Connection timeout" in str(error)
        assert error.reason == "Connection timeout"
    
    def test_with_source_and_reason(self):
        """Test with both source and reason."""
        error = DataAcquisitionError(
            "Download failed",
            source="https://example.com",
            reason="Connection timeout"
        )
        
        assert "Source: https://example.com" in str(error)
        assert "Reason: Connection timeout" in str(error)
    
    def test_custom_code(self):
        """Test with custom error code."""
        error = DataAcquisitionError("Error", code="CUSTOM_001")
        
        assert error.code == "CUSTOM_001"

class TestMissingDataError:
    """Tests for MissingDataError class."""
    
    def test_basic_initialization(self):
        """Test basic initialization."""
        error = MissingDataError("Data is missing")
        
        assert "Data is missing" in str(error)
        assert error.missing_fields == []
    
    def test_with_missing_fields(self):
        """Test with missing fields."""
        error = MissingDataError(
            "Data is missing",
            missing_fields=["field1", "field2"]
        )
        
        assert "Missing fields: field1, field2" in str(error)
        assert error.missing_fields == ["field1", "field2"]
    
    def test_with_counts(self):
        """Test with expected and actual counts."""
        error = MissingDataError(
            "Data is missing",
            expected_count=100,
            actual_count=50
        )
        
        assert "Expected 100, got 50" in str(error)
    
    def test_full_initialization(self):
        """Test with all parameters."""
        error = MissingDataError(
            "Data is missing",
            missing_fields=["field1"],
            expected_count=100,
            actual_count=50
        )
        
        assert "Missing fields: field1" in str(error)
        assert "Expected 100, got 50" in str(error)

class TestValidationFailureError:
    """Tests for ValidationFailureError class."""
    
    def test_basic_initialization(self):
        """Test basic initialization."""
        error = ValidationFailureError("Validation failed")
        
        assert "Validation failed" in str(error)
        assert error.validation_type is None
        assert error.failed_rules == []
    
    def test_with_validation_type(self):
        """Test with validation type."""
        error = ValidationFailureError(
            "Validation failed",
            validation_type="schema"
        )
        
        assert "Validation failed" in str(error)
        assert error.validation_type == "schema"
    
    def test_with_failed_rules(self):
        """Test with failed rules."""
        error = ValidationFailureError(
            "Validation failed",
            failed_rules=["rule1", "rule2"]
        )
        
        assert "Failed rules: rule1, rule2" in str(error)
        assert error.failed_rules == ["rule1", "rule2"]

class TestStatisticalModelError:
    """Tests for StatisticalModelError class."""
    
    def test_basic_initialization(self):
        """Test basic initialization."""
        error = StatisticalModelError("Model fit failed")
        
        assert "Model fit failed" in str(error)
        assert error.model_name is None
        assert error.fit_status is None
        assert error.parameters == {}
    
    def test_with_model_name(self):
        """Test with model name."""
        error = StatisticalModelError(
            "Model fit failed",
            model_name="NegativeBinomial"
        )
        
        assert "Model: NegativeBinomial" in str(error)
        assert error.model_name == "NegativeBinomial"
    
    def test_with_fit_status(self):
        """Test with fit status."""
        error = StatisticalModelError(
            "Model fit failed",
            fit_status="convergence_error"
        )
        
        assert "Status: convergence_error" in str(error)
        assert error.fit_status == "convergence_error"
    
    def test_with_parameters(self):
        """Test with parameters."""
        error = StatisticalModelError(
            "Model fit failed",
            parameters={"alpha": 0.5, "beta": 0.3}
        )
        
        assert error.parameters == {"alpha": 0.5, "beta": 0.3}

class TestConfigurationError:
    """Tests for ConfigurationError class."""
    
    def test_basic_initialization(self):
        """Test basic initialization."""
        error = ConfigurationError("Config is invalid")
        
        assert "Config is invalid" in str(error)
        assert error.config_key is None
        assert error.expected_type is None
    
    def test_with_config_key(self):
        """Test with config key."""
        error = ConfigurationError(
            "Config is invalid",
            config_key="threshold"
        )
        
        assert "Key: threshold" in str(error)
        assert error.config_key == "threshold"
    
    def test_with_expected_type(self):
        """Test with expected type."""
        error = ConfigurationError(
            "Config is invalid",
            expected_type="float"
        )
        
        assert "Expected: float" in str(error)
        assert error.expected_type == "float"

class TestReproducibilityError:
    """Tests for ReproducibilityError class."""
    
    def test_basic_initialization(self):
        """Test basic initialization."""
        error = ReproducibilityError("Reproducibility check failed")
        
        assert "Reproducibility check failed" in str(error)
        assert error.artifact_path is None
        assert error.expected_hash is None
        assert error.actual_hash is None
    
    def test_with_artifact_path(self):
        """Test with artifact path."""
        error = ReproducibilityError(
            "Reproducibility check failed",
            artifact_path="data/processed/output.csv"
        )
        
        assert "Artifact: data/processed/output.csv" in str(error)
        assert error.artifact_path == "data/processed/output.csv"
    
    def test_with_hash_mismatch(self):
        """Test with hash mismatch information."""
        error = ReproducibilityError(
            "Reproducibility check failed",
            expected_hash="abc123def456",
            actual_hash="xyz789uvw012"
        )
        
        assert "Hash mismatch" in str(error)
        assert "abc123def456" in str(error)
        assert "xyz789uvw012" in str(error)
    
    def test_full_initialization(self):
        """Test with all parameters."""
        error = ReproducibilityError(
            "Reproducibility check failed",
            artifact_path="data/processed/output.csv",
            expected_hash="abc123def456",
            actual_hash="xyz789uvw012"
        )
        
        assert "Artifact: data/processed/output.csv" in str(error)
        assert "Hash mismatch" in str(error)
