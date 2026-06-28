"""Unit tests for schema validation utilities."""

import pytest
from pathlib import Path

from code.src.contracts.validation import (
    SchemaValidator,
    get_ab_summary_validator,
    get_audit_record_validator,
    validate_ab_summary,
    validate_audit_record,
)


class TestSchemaValidator:
    """Tests for the SchemaValidator class."""

    def test_validator_loads_schema(self):
        """Test that validator loads schema without errors."""
        validator = SchemaValidator(
            Path("contracts/extracted_summary.schema.yaml"),
            "extracted_summary"
        )
        assert validator.schema is not None
        assert isinstance(validator.schema, dict)

    def test_validator_validates_correct_data(self):
        """Test that validator accepts valid data."""
        validator = SchemaValidator(
            Path("contracts/extracted_summary.schema.yaml"),
            "extracted_summary"
        )
        valid_data = {
            "url": "https://example.com/test",
            "domain": "example.com",
            "sample_size": 1000,
            "p_value": 0.03,
            "effect_size": 0.05,
            "test_type": "z-test",
            "outcome_type": "binary",
        }
        is_valid, errors = validator.validate(valid_data)
        assert is_valid is True
        assert len(errors) == 0

    def test_validator_rejects_invalid_data(self):
        """Test that validator rejects invalid data."""
        validator = SchemaValidator(
            Path("contracts/extracted_summary.schema.yaml"),
            "extracted_summary"
        )
        # Missing required fields should fail validation
        invalid_data = {}
        is_valid, errors = validator.validate(invalid_data)
        assert is_valid is False
        assert len(errors) > 0


class TestGetValidators:
    """Tests for validator factory functions."""

    def test_get_ab_summary_validator_returns_validator(self):
        """Test that get_ab_summary_validator returns a valid validator."""
        validator = get_ab_summary_validator()
        assert validator is not None
        assert isinstance(validator, SchemaValidator)
        assert validator.schema_name == "extracted_summary"

    def test_get_audit_record_validator_returns_validator(self):
        """Test that get_audit_record_validator returns a valid validator."""
        validator = get_audit_record_validator()
        assert validator is not None
        assert isinstance(validator, SchemaValidator)
        assert validator.schema_name == "audit_record"


class TestValidateAbSummary:
    """Tests for validate_ab_summary function."""

    def test_validate_ab_summary_with_valid_data(self):
        """Test validation with valid AB summary data."""
        valid_data = {
            "url": "https://example.com/test",
            "domain": "example.com",
            "sample_size": 1000,
            "p_value": 0.03,
            "effect_size": 0.05,
            "test_type": "z-test",
            "outcome_type": "binary",
        }
        is_valid, errors = validate_ab_summary(valid_data)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_ab_summary_with_invalid_data(self):
        """Test validation with invalid AB summary data."""
        invalid_data = {}
        is_valid, errors = validate_ab_summary(invalid_data)
        assert is_valid is False
        assert len(errors) > 0


class TestValidateAuditRecord:
    """Tests for validate_audit_record function."""

    def test_validate_audit_record_with_valid_data(self):
        """Test validation with valid audit record data."""
        valid_data = {
            "summary_id": "test-123",
            "url": "https://example.com/test",
            "is_consistent": True,
            "p_value_difference": 0.01,
            "effect_size_difference": 0.02,
        }
        is_valid, errors = validate_audit_record(valid_data)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_audit_record_with_invalid_data(self):
        """Test validation with invalid audit record data."""
        invalid_data = {}
        is_valid, errors = validate_audit_record(invalid_data)
        assert is_valid is False
        assert len(errors) > 0
