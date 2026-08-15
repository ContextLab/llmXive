"""
Unit tests for the modification proposal schema (T013).
"""
import pytest
import json
from pydantic import ValidationError
from schemas.modification_proposal import ModificationProposal, validate_modification_json

class TestModificationProposalSchema:
    """Tests for ModificationProposal Pydantic model."""

    def test_valid_proposal_layer_add(self):
        """Test a valid layer_add proposal."""
        data = {
            "modification_type": "layer_add",
            "magnitude": 2,
            "rationale": "Adding layers to increase depth",
            "estimated_param_count": 1000000
        }
        proposal = ModificationProposal(**data)
        assert proposal.modification_type == "layer_add"
        assert proposal.magnitude == 2
        assert proposal.estimated_param_count == 1000000

    def test_valid_proposal_head_count_change(self):
        """Test a valid head_count_change proposal."""
        data = {
            "modification_type": "head_count_change",
            "magnitude": 4,
            "rationale": "Increasing attention heads",
            "estimated_param_count": 500000
        }
        proposal = ModificationProposal(**data)
        assert proposal.modification_type == "head_count_change"
        assert proposal.magnitude == 4
        assert proposal.estimated_param_count == 500000

    def test_invalid_json_format(self):
        """Test that invalid JSON string raises json.JSONDecodeError."""
        invalid_json = "{ invalid json }"
        with pytest.raises(json.JSONDecodeError):
            validate_modification_json(invalid_json)

    def test_missing_required_field(self):
        """Test that missing a required field raises ValidationError."""
        invalid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 2
            # Missing 'rationale' and 'estimated_param_count'
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json)

    def test_missing_magnitude_field_raises_validation_error(self):
        """
        Verification: Assert ValidationError is raised specifically for a missing magnitude field.
        """
        data = {
            "modification_type": "layer_add",
            "rationale": "Missing magnitude test",
            "estimated_param_count": 1000
        }
        with pytest.raises(ValidationError) as exc_info:
            ModificationProposal(**data)
        
        # Verify the error is specifically about the missing 'magnitude' field
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]['loc'] == ('magnitude',)
        assert 'field required' in errors[0]['msg'].lower() or 'missing' in errors[0]['msg'].lower()

    def test_missing_modification_type_raises_validation_error(self):
        """Test that missing modification_type raises ValidationError."""
        data = {
            "magnitude": 2,
            "rationale": "Missing type test",
            "estimated_param_count": 1000
        }
        with pytest.raises(ValidationError):
            ModificationProposal(**data)

    def test_invalid_magnitude_zero_raises_error(self):
        """Test that magnitude=0 raises ValidationError."""
        data = {
            "modification_type": "layer_add",
            "magnitude": 0,
            "rationale": "Zero magnitude test",
            "estimated_param_count": 1000
        }
        with pytest.raises(ValidationError):
            ModificationProposal(**data)

    def test_invalid_magnitude_negative_raises_error(self):
        """Test that negative magnitude raises ValidationError."""
        data = {
            "modification_type": "head_count_change",
            "magnitude": -1,
            "rationale": "Negative magnitude test",
            "estimated_param_count": 1000
        }
        with pytest.raises(ValidationError):
            ModificationProposal(**data)

    def test_invalid_modification_type_raises_error(self):
        """Test that invalid modification_type raises ValidationError."""
        data = {
            "modification_type": "invalid_type",
            "magnitude": 2,
            "rationale": "Invalid type test",
            "estimated_param_count": 1000
        }
        with pytest.raises(ValidationError):
            ModificationProposal(**data)

    def test_validate_modification_json_valid(self):
        """Test the validate_modification_json helper function with valid input."""
        json_str = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 3,
            "rationale": "JSON validation test",
            "estimated_param_count": 2000000
        })
        proposal = validate_modification_json(json_str)
        assert proposal.magnitude == 3

    def test_validate_modification_json_missing_magnitude(self):
        """Test the validate_modification_json helper function with missing magnitude."""
        json_str = json.dumps({
            "modification_type": "layer_add",
            "rationale": "Missing magnitude in JSON",
            "estimated_param_count": 1000
        })
        with pytest.raises(ValidationError):
            validate_modification_json(json_str)

    def test_validate_modification_json_invalid_json(self):
        """Test the validate_modification_json helper function with invalid JSON string."""
        with pytest.raises(json.JSONDecodeError):
            validate_modification_json("not valid json")