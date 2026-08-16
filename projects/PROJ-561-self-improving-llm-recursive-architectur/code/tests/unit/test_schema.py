"""
Unit tests for the ModificationProposal schema (T013).
"""
import pytest
import json
from pydantic import ValidationError
from schemas.modification_proposal import ModificationProposal, validate_modification_json

class TestModificationProposalSchema:
    """Tests for the ModificationProposal Pydantic model."""

    def test_valid_proposal(self):
        """Test that a valid proposal is accepted."""
        data = {
            "modification_type": "layer_add",
            "magnitude": 2,
            "rationale": "Adding layers to increase depth",
            "estimated_param_count": 150000000
        }
        proposal = ModificationProposal(**data)
        assert proposal.modification_type == "layer_add"
        assert proposal.magnitude == 2
        assert proposal.estimated_param_count == 150000000

    def test_valid_head_count_change(self):
        """Test a valid head_count_change proposal."""
        data = {
            "modification_type": "head_count_change",
            "magnitude": 16,
            "rationale": "Increasing attention heads",
            "estimated_param_count": 130000000
        }
        proposal = ModificationProposal(**data)
        assert proposal.modification_type == "head_count_change"
        assert proposal.magnitude == 16

    def test_valid_hidden_size_change(self):
        """Test a valid hidden_size_change proposal."""
        data = {
            "modification_type": "hidden_size_change",
            "magnitude": 800,
            "rationale": "Increasing hidden dimension",
            "estimated_param_count": 200000000
        }
        proposal = ModificationProposal(**data)
        assert proposal.modification_type == "hidden_size_change"
        assert proposal.magnitude == 800

    def test_valid_activation_change(self):
        """Test a valid activation_change proposal."""
        data = {
            "modification_type": "activation_change",
            "magnitude": 1,
            "rationale": "Switching activation function",
            "estimated_param_count": 124000000
        }
        proposal = ModificationProposal(**data)
        assert proposal.modification_type == "activation_change"

    def test_missing_magnitude_raises_error(self):
        """
        Verification: Assert ValidationError is raised specifically for a missing `magnitude` field.
        """
        data = {
            "modification_type": "layer_add",
            "rationale": "Missing magnitude field",
            "estimated_param_count": 130000000
        }
        with pytest.raises(ValidationError) as exc_info:
            ModificationProposal(**data)
        
        # Check that the error is specifically about the 'magnitude' field
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]['loc'] == ('magnitude',)
        assert 'missing' in errors[0]['msg'].lower() or 'required' in errors[0]['msg'].lower()

    def test_missing_modification_type_raises_error(self):
        """Test that missing modification_type raises error."""
        data = {
            "magnitude": 2,
            "rationale": "Missing type",
            "estimated_param_count": 130000000
        }
        with pytest.raises(ValidationError):
            ModificationProposal(**data)

    def test_invalid_modification_type_raises_error(self):
        """Test that invalid modification_type raises error."""
        data = {
            "modification_type": "invalid_type",
            "magnitude": 2,
            "rationale": "Bad type",
            "estimated_param_count": 130000000
        }
        with pytest.raises(ValidationError):
            ModificationProposal(**data)

    def test_magnitude_must_be_positive(self):
        """Test that magnitude must be positive."""
        data = {
            "modification_type": "layer_add",
            "magnitude": 0,
            "rationale": "Zero magnitude",
            "estimated_param_count": 130000000
        }
        with pytest.raises(ValidationError):
            ModificationProposal(**data)
        
        data['magnitude'] = -5
        with pytest.raises(ValidationError):
            ModificationProposal(**data)

    def test_validate_modification_json_valid(self):
        """Test the JSON validation helper function."""
        json_str = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 1,
            "rationale": "Test",
            "estimated_param_count": 125000000
        })
        proposal = validate_modification_json(json_str)
        assert proposal.magnitude == 1

    def test_validate_modification_json_invalid_missing_magnitude(self):
        """Test JSON validation fails for missing magnitude."""
        json_str = json.dumps({
            "modification_type": "layer_add",
            "rationale": "No magnitude",
            "estimated_param_count": 125000000
        })
        with pytest.raises(ValidationError):
            validate_modification_json(json_str)