import pytest
import json
from pydantic import ValidationError
from schemas.modification_proposal import ModificationProposal, validate_modification_json


class TestModificationProposalSchema:
    """Unit tests for the ModificationProposal JSON schema validation."""

    def test_valid_layer_add_proposal(self):
        """Test that a valid layer_add proposal passes validation."""
        valid_data = {
            "modification_type": "layer_add",
            "magnitude": 2,
            "rationale": "Adding layers to increase depth for better feature extraction.",
            "estimated_param_count": 15000000
        }
        proposal = ModificationProposal(**valid_data)
        assert proposal.modification_type == "layer_add"
        assert proposal.magnitude == 2
        assert proposal.rationale is not None
        assert proposal.estimated_param_count > 0

    def test_valid_head_count_change_proposal(self):
        """Test that a valid head_count_change proposal passes validation."""
        valid_data = {
            "modification_type": "head_count_change",
            "magnitude": 4,
            "rationale": "Increasing attention heads to improve parallel processing.",
            "estimated_param_count": 20000000
        }
        proposal = ModificationProposal(**valid_data)
        assert proposal.modification_type == "head_count_change"
        assert proposal.magnitude == 4

    def test_invalid_modification_type(self):
        """Test that an invalid modification_type raises ValidationError."""
        invalid_data = {
            "modification_type": "invalid_type",
            "magnitude": 2,
            "rationale": "Testing invalid type.",
            "estimated_param_count": 1000000
        }
        with pytest.raises(ValidationError) as exc_info:
            ModificationProposal(**invalid_data)
        assert "invalid_type" in str(exc_info.value)
        assert "modification_type" in str(exc_info.value)

    def test_missing_magnitude(self):
        """Test that missing magnitude raises ValidationError."""
        invalid_data = {
            "modification_type": "layer_add",
            "rationale": "Missing magnitude.",
            "estimated_param_count": 1000000
        }
        with pytest.raises(ValidationError) as exc_info:
            ModificationProposal(**invalid_data)
        assert "magnitude" in str(exc_info.value)

    def test_invalid_magnitude_type(self):
        """Test that non-integer magnitude raises ValidationError."""
        invalid_data = {
            "modification_type": "layer_add",
            "magnitude": "not_an_int",
            "rationale": "Invalid magnitude type.",
            "estimated_param_count": 1000000
        }
        with pytest.raises(ValidationError) as exc_info:
            ModificationProposal(**invalid_data)
        assert "magnitude" in str(exc_info.value)

    def test_missing_rationale(self):
        """Test that missing rationale raises ValidationError."""
        invalid_data = {
            "modification_type": "layer_add",
            "magnitude": 2,
            "estimated_param_count": 1000000
        }
        with pytest.raises(ValidationError) as exc_info:
            ModificationProposal(**invalid_data)
        assert "rationale" in str(exc_info.value)

    def test_negative_magnitude(self):
        """Test that negative magnitude raises ValidationError."""
        invalid_data = {
            "modification_type": "layer_add",
            "magnitude": -1,
            "rationale": "Negative magnitude test.",
            "estimated_param_count": 1000000
        }
        with pytest.raises(ValidationError) as exc_info:
            ModificationProposal(**invalid_data)
        assert "magnitude" in str(exc_info.value)

    def test_validate_modification_json_valid(self):
        """Test validate_modification_json with valid JSON string."""
        valid_json_str = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 1,
            "rationale": "Valid JSON string test.",
            "estimated_param_count": 1000000
        })
        result = validate_modification_json(valid_json_str)
        assert result is not None
        assert result.modification_type == "layer_add"

    def test_validate_modification_json_invalid_type(self):
        """Test validate_modification_json with invalid modification_type in JSON."""
        invalid_json_str = json.dumps({
            "modification_type": "bad_type",
            "magnitude": 1,
            "rationale": "Invalid type in JSON.",
            "estimated_param_count": 1000000
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json_str)

    def test_validate_modification_json_malformed(self):
        """Test validate_modification_json with malformed JSON string."""
        malformed_json_str = '{"modification_type": "layer_add", "magnitude": }'
        with pytest.raises(json.JSONDecodeError):
            validate_modification_json(malformed_json_str)

    def test_validate_modification_json_missing_field(self):
        """Test validate_modification_json with missing required field."""
        missing_field_json_str = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 1,
            "estimated_param_count": 1000000
        })
        with pytest.raises(ValidationError):
            validate_modification_json(missing_field_json_str)