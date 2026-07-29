"""
Unit tests for the ModificationProposal schema (T013).
"""
import pytest
import json
from pydantic import ValidationError
from schemas.modification_proposal import ModificationProposal, validate_modification_json


class TestModificationProposalSchema:
    """Tests for T013: Define modification proposal JSON schema"""

    def test_valid_proposal(self):
        """Test that a valid JSON proposal parses correctly"""
        valid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 2.0,
            "rationale": "Adding layers to increase model capacity for better reasoning",
            "estimated_param_count": 150000000
        })
        proposal = validate_modification_json(valid_json)
        
        assert proposal.modification_type == "layer_add"
        assert proposal.magnitude == 2.0
        assert "increase model capacity" in proposal.rationale
        assert proposal.estimated_param_count == 150000000

    def test_valid_all_modification_types(self):
        """Test that all allowed modification types are accepted"""
        types = [
            "layer_add", "layer_remove", "head_count_change",
            "hidden_dim_change", "dropout_change", "activation_change"
        ]
        for mod_type in types:
            json_str = json.dumps({
                "modification_type": mod_type,
                "magnitude": 1.0,
                "rationale": f"Testing {mod_type}",
                "estimated_param_count": 120000000
            })
            proposal = validate_modification_json(json_str)
            assert proposal.modification_type == mod_type

    def test_invalid_modification_type(self):
        """Test that invalid modification types raise ValidationError"""
        invalid_json = json.dumps({
            "modification_type": "invalid_type_xyz",
            "magnitude": 1.0,
            "rationale": "Testing invalid type",
            "estimated_param_count": 120000000
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json)

    def test_missing_required_field(self):
        """Test that missing required fields raise ValidationError"""
        # Missing 'rationale'
        invalid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 1.0,
            "estimated_param_count": 120000000
        })
        with pytest.raises(ValidationError) as exc_info:
            validate_modification_json(invalid_json)
        assert "rationale" in str(exc_info.value).lower()

    def test_invalid_json_syntax(self):
        """Test that malformed JSON raises JSONDecodeError"""
        malformed_json = '{"modification_type": "layer_add", "magnitude": }'
        with pytest.raises(json.JSONDecodeError):
            validate_modification_json(malformed_json)

    def test_magnitude_must_be_positive(self):
        """Test that negative magnitude raises ValidationError"""
        invalid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": -1.0,
            "rationale": "Testing negative magnitude",
            "estimated_param_count": 120000000
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json)

    def test_rationale_must_not_be_empty(self):
        """Test that empty rationale raises ValidationError"""
        invalid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 1.0,
            "rationale": "   ",
            "estimated_param_count": 120000000
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json)

    def test_param_count_must_be_positive(self):
        """Test that negative param count raises ValidationError"""
        invalid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 1.0,
            "rationale": "Testing negative param count",
            "estimated_param_count": -100
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json)

    def test_param_count_too_small(self):
        """Test that param count below minimum raises ValidationError"""
        invalid_json = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 1.0,
            "rationale": "Testing small param count",
            "estimated_param_count": 500
        })
        with pytest.raises(ValidationError):
            validate_modification_json(invalid_json)

    def test_direct_model_instantiation(self):
        """Test creating model directly with dict"""
        proposal = ModificationProposal(
            modification_type="head_count_change",
            magnitude=4.0,
            rationale="Increasing attention heads for better parallelism",
            estimated_param_count=130000000
        )
        assert proposal.modification_type == "head_count_change"
        assert proposal.magnitude == 4.0

    def test_serialization_round_trip(self):
        """Test that model can be serialized and deserialized"""
        original = ModificationProposal(
            modification_type="dropout_change",
            magnitude=0.1,
            rationale="Adjusting dropout for regularization",
            estimated_param_count=125000000
        )
        
        # Serialize to dict then JSON
        json_str = original.model_dump_json()
        
        # Deserialize
        recovered = ModificationProposal.model_validate_json(json_str)
        
        assert recovered.modification_type == original.modification_type
        assert recovered.magnitude == original.magnitude
        assert recovered.rationale == original.rationale
        assert recovered.estimated_param_count == original.estimated_param_count