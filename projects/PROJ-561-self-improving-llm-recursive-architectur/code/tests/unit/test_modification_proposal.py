"""
Unit tests for the ModificationProposal schema (T013).

These tests verify that the Pydantic model correctly accepts valid inputs
and rejects invalid JSON inputs as required by the task specification.
"""
import unittest
import json
from pydantic import ValidationError
from schemas.modification_proposal import ModificationProposal, validate_modification_json


class TestModificationProposalSchema(unittest.TestCase):
    """Test cases for the ModificationProposal Pydantic model."""

    def test_valid_layer_add_proposal(self):
        """Test a valid proposal for adding layers."""
        valid_json = {
            "modification_type": "layer_add",
            "magnitude": 2,
            "rationale": "Adding two layers to increase model depth and capacity for complex reasoning tasks.",
            "estimated_param_count": 15.5
        }
        proposal = ModificationProposal(**valid_json)
        self.assertEqual(proposal.modification_type, "layer_add")
        self.assertEqual(proposal.magnitude, 2)
        self.assertGreater(proposal.estimated_param_count, 0)

    def test_valid_head_count_change_proposal(self):
        """Test a valid proposal for changing head count."""
        valid_json = {
            "modification_type": "head_count_change",
            "magnitude": -4,
            "rationale": "Reducing attention heads to decrease computational overhead while maintaining performance.",
            "estimated_param_count": -5.2
        }
        proposal = ModificationProposal(**valid_json)
        self.assertEqual(proposal.modification_type, "head_count_change")
        self.assertEqual(proposal.magnitude, -4)

    def test_invalid_modification_type(self):
        """Test that an invalid modification_type is rejected."""
        invalid_json = {
            "modification_type": "unknown_type",
            "magnitude": 2,
            "rationale": "This type does not exist.",
            "estimated_param_count": 10.0
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**invalid_json)

    def test_invalid_magnitude_type(self):
        """Test that a non-integer magnitude is rejected."""
        invalid_json = {
            "modification_type": "layer_add",
            "magnitude": "two",
            "rationale": "Magnitude should be an integer.",
            "estimated_param_count": 10.0
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**invalid_json)

    def test_missing_required_field(self):
        """Test that missing required fields are rejected."""
        invalid_json = {
            "modification_type": "layer_add",
            "magnitude": 2
            # Missing rationale and estimated_param_count
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**invalid_json)

    def test_rationale_too_short(self):
        """Test that a rationale shorter than 10 chars is rejected."""
        invalid_json = {
            "modification_type": "layer_add",
            "magnitude": 2,
            "rationale": "Too short",
            "estimated_param_count": 10.0
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**invalid_json)

    def test_validate_modification_json_with_valid_input(self):
        """Test the validation helper with valid JSON string."""
        valid_json_str = json.dumps({
            "modification_type": "layer_add",
            "magnitude": 1,
            "rationale": "Valid rationale for testing the validation function.",
            "estimated_param_count": 5.0
        })
        self.assertTrue(validate_modification_json(valid_json_str))

    def test_validate_modification_json_with_invalid_json_syntax(self):
        """Test that malformed JSON syntax raises ValueError."""
        invalid_json_str = '{"modification_type": "layer_add", magnitude: 2}' # Missing quotes on key
        with self.assertRaises(ValueError):
            validate_modification_json(invalid_json_str)

    def test_validate_modification_json_with_invalid_schema(self):
        """Test that valid JSON but invalid schema raises ValueError."""
        invalid_schema_str = json.dumps({
            "modification_type": "invalid_type",
            "magnitude": 2,
            "rationale": "Valid rationale length.",
            "estimated_param_count": 5.0
        })
        with self.assertRaises(ValueError):
            validate_modification_json(invalid_schema_str)

    def test_from_json_string_malformed(self):
        """Test from_json_string with completely broken JSON."""
        broken_json = "not json at all"
        with self.assertRaises(ValueError):
            ModificationProposal.from_json_string(broken_json)

    def test_from_json_string_valid(self):
        """Test from_json_string with valid JSON string."""
        valid_json_str = json.dumps({
            "modification_type": "dim_change",
            "magnitude": 16,
            "rationale": "Increasing hidden dimension to capture more features.",
            "estimated_param_count": 20.0
        })
        proposal = ModificationProposal.from_json_string(valid_json_str)
        self.assertIsInstance(proposal, ModificationProposal)
        self.assertEqual(proposal.modification_type, "dim_change")


if __name__ == '__main__':
    unittest.main()