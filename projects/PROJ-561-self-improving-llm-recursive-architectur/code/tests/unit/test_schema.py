import pytest
import json
from pydantic import ValidationError
from schemas.modification_proposal import ModificationProposal, validate_modification_json


class TestModificationProposalSchema:
    """Unit tests for the ModificationProposal schema and validation logic."""

    def test_valid_proposal_layer_add(self):
        """Test that a valid layer_add proposal is accepted."""
        valid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 2,
            "rationale": "Adding layers to increase depth and capacity.",
            "estimated_param_count": 1000000
        })
        proposal = validate_modification_json(valid_json)
        assert proposal.modification_type == "layer_add"
        assert proposal.magnitude == 2
        assert "increase" in proposal.rationale.lower()
        assert proposal.estimated_param_count == 1000000

    def test_valid_proposal_head_count_change(self):
        """Test that a valid head_count_change proposal is accepted."""
        valid_json = json.dumps({
            "modification_type": "head_count_change",
            "magnitude": 4,
            "rationale": "Increasing attention heads for better parallelism.",
            "estimated_param_count": 500000
        })
        proposal = validate_modification_json(valid_json)
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

    def test_invalid_modification_type(self):
        """Test that an invalid modification_type raises ValidationError."""
        invalid_json = json.dumps({
            "modification_type": "invalid_type",
            "magnitude": 2,
            "rationale": "Testing invalid type.",
            "estimated_param_count": 100
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json)

    def test_negative_magnitude(self):
        """Test that negative magnitude raises ValidationError."""
        invalid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": -5,
            "rationale": "Testing negative magnitude.",
            "estimated_param_count": 100
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json)

    def test_zero_magnitude(self):
        """Test that zero magnitude raises ValidationError (must be > 0)."""
        invalid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 0,
            "rationale": "Testing zero magnitude.",
            "estimated_param_count": 100
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json)

    def test_empty_rationale(self):
        """Test that empty rationale raises ValidationError."""
        invalid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 2,
            "rationale": "",
            "estimated_param_count": 100
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json)

    def test_whitespace_only_rationale(self):
        """Test that whitespace-only rationale raises ValidationError."""
        invalid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 2,
            "rationale": "   ",
            "estimated_param_count": 100
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json)

    def test_direct_model_instantiation(self):
        """Test direct instantiation of ModificationProposal model."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=3,
            rationale="Direct instantiation test",
            estimated_param_count=200000
        )
        assert proposal.modification_type == "layer_add"
        assert proposal.magnitude == 3