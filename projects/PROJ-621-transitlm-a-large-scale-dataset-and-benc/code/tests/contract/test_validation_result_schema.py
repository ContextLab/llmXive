"""
Contract tests for the ValidationResult schema.

Verifies that the Pydantic model correctly enforces:
- Required fields
- Score range (0.0 to 1.0)
- Valid status enum values
"""
import pytest
from pydantic import ValidationError
from src.contracts.models import ValidationResult, ValidationStatus


class TestValidationResultSchema:
    """Tests for the ValidationResult Pydantic model."""

    def test_valid_result(self):
        """Test that a valid result is accepted."""
        data = {
            "route_id": "route_001",
            "status": "valid",
            "exact_match": True,
            "connectivity_valid": True,
            "score": 1.0
        }
        result = ValidationResult(**data)
        assert result.status == ValidationStatus.VALID
        assert result.score == 1.0

    def test_invalid_score_range_high(self):
        """Test that a score > 1.0 raises ValidationError."""
        data = {
            "route_id": "route_001",
            "status": "valid",
            "exact_match": True,
            "connectivity_valid": True,
            "score": 1.5
        }
        with pytest.raises(ValidationError) as exc_info:
            ValidationResult(**data)
        
        assert "Score must be between 0.0 and 1.0" in str(exc_info.value)

    def test_invalid_score_range_low(self):
        """Test that a score < 0.0 raises ValidationError."""
        data = {
            "route_id": "route_001",
            "status": "valid",
            "exact_match": False,
            "connectivity_valid": False,
            "score": -0.1
        }
        with pytest.raises(ValidationError) as exc_info:
            ValidationResult(**data)
        
        assert "Score must be between 0.0 and 1.0" in str(exc_info.value)

    def test_invalid_status_enum(self):
        """Test that an invalid status string raises ValidationError."""
        data = {
            "route_id": "route_001",
            "status": "unknown_status",
            "exact_match": False,
            "connectivity_valid": False,
            "score": 0.5
        }
        with pytest.raises(ValidationError):
            ValidationResult(**data)

    def test_partial_status(self):
        """Test that 'partial' status is valid."""
        data = {
            "route_id": "route_001",
            "status": "partial",
            "exact_match": False,
            "connectivity_valid": True,
            "score": 0.5
        }
        result = ValidationResult(**data)
        assert result.status == ValidationStatus.PARTIAL
