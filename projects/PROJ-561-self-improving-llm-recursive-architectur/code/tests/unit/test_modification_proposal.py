import unittest
import json
from pydantic import ValidationError
from schemas.modification_proposal import ModificationProposal, validate_modification_json


class TestModificationProposalSchema(unittest.TestCase):
    
    def test_valid_layer_add_proposal(self):
        """Test a valid proposal to add a layer."""
        data = {
            "proposal_id": "prop-001",
            "description": "Add a new transformer block",
            "modification_type": "layer_add",
            "layer_index": 10,
            "add_layer": True
        }
        proposal = ModificationProposal(**data)
        self.assertEqual(proposal.proposal_id, "prop-001")
        self.assertEqual(proposal.modification_type, "layer_add")
        self.assertTrue(proposal.add_layer)

    def test_valid_hidden_size_change(self):
        """Test a valid proposal to change hidden size."""
        data = {
            "proposal_id": "prop-002",
            "description": "Increase hidden size by 64",
            "modification_type": "hidden_size_change",
            "hidden_size_change": 64
        }
        proposal = ModificationProposal(**data)
        self.assertEqual(proposal.hidden_size_change, 64)
        self.assertIsNone(proposal.layer_index)

    def test_valid_activation_change(self):
        """Test a valid proposal to change activation function."""
        data = {
            "proposal_id": "prop-003",
            "description": "Switch to Swish activation",
            "modification_type": "activation_change",
            "new_activation": "swish"
        }
        proposal = ModificationProposal(**data)
        self.assertEqual(proposal.new_activation, "swish")

    def test_invalid_layer_index_negative(self):
        """Test that negative layer_index raises error."""
        data = {
            "proposal_id": "prop-004",
            "description": "Invalid layer index",
            "modification_type": "layer_remove",
            "layer_index": -1
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**data)

    def test_invalid_hidden_size_change_zero(self):
        """Test that zero hidden_size_change raises error."""
        data = {
            "proposal_id": "prop-005",
            "description": "Zero change",
            "modification_type": "hidden_size_change",
            "hidden_size_change": 0
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**data)

    def test_invalid_modification_type(self):
        """Test that an invalid modification_type raises error."""
        data = {
            "proposal_id": "prop-006",
            "description": "Invalid type",
            "modification_type": "invalid_type"
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**data)

    def test_validate_modification_json_valid(self):
        """Test the JSON validation helper function."""
        json_str = json.dumps({
            "proposal_id": "prop-007",
            "description": "Test JSON",
            "modification_type": "layer_add",
            "add_layer": True
        })
        proposal = validate_modification_json(json_str)
        self.assertIsInstance(proposal, ModificationProposal)
        self.assertEqual(proposal.proposal_id, "prop-007")

    def test_validate_modification_json_invalid_json(self):
        """Test the JSON validation helper with bad JSON."""
        json_str = "not valid json {"
        with self.assertRaises(ValidationError):
            validate_modification_json(json_str)

    def test_validate_modification_json_invalid_schema(self):
        """Test the JSON validation helper with valid JSON but bad schema."""
        json_str = json.dumps({
            "proposal_id": "prop-008",
            "description": "Bad schema",
            "modification_type": "non_existent_type"
        })
        with self.assertRaises(ValidationError):
            validate_modification_json(json_str)

    def test_required_fields_missing(self):
        """Test that missing required fields raise error."""
        data = {
            "description": "Missing proposal_id"
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**data)

    def test_optional_fields_can_be_none(self):
        """Test that optional fields can be omitted."""
        data = {
            "proposal_id": "prop-009",
            "description": "Minimal proposal",
            "modification_type": "layer_add"
        }
        proposal = ModificationProposal(**data)
        self.assertIsNone(proposal.layer_index)
        self.assertIsNone(proposal.hidden_size_change)
        self.assertIsNone(proposal.num_heads_change)
        self.assertIsNone(proposal.new_activation)