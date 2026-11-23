"""
Unit tests for the ModificationProposal schema (T013).
"""
import unittest
import json
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from schemas.modification_proposal import ModificationProposal
from pydantic import ValidationError


class TestModificationProposalSchema(unittest.TestCase):
    """Tests for the ModificationProposal Pydantic model."""

    def test_valid_proposal(self):
        """Test that a valid JSON input is accepted."""
        valid_data = {
            "modification_type": "layer_add",
            "magnitude": 2,
            "rationale": "Adding two layers to increase depth and capture more complex patterns.",
            "estimated_param_count": 15000000
        }
        proposal = ModificationProposal(**valid_data)
        self.assertEqual(proposal.modification_type, "layer_add")
        self.assertEqual(proposal.magnitude, 2)
        self.assertIn("depth", proposal.rationale.lower())
        self.assertEqual(proposal.estimated_param_count, 15000000)

    def test_invalid_modification_type(self):
        """Test that an invalid modification_type is rejected."""
        invalid_data = {
            "modification_type": "unknown_type",
            "magnitude": 2,
            "rationale": "Testing invalid type.",
            "estimated_param_count": 1000
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**invalid_data)

    def test_negative_magnitude(self):
        """Test that a negative magnitude is rejected."""
        invalid_data = {
            "modification_type": "layer_add",
            "magnitude": -5,
            "rationale": "Testing negative magnitude.",
            "estimated_param_count": 1000
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**invalid_data)

    def test_zero_magnitude(self):
        """Test that a zero magnitude is rejected (ge=1)."""
        invalid_data = {
            "modification_type": "layer_add",
            "magnitude": 0,
            "rationale": "Testing zero magnitude.",
            "estimated_param_count": 1000
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**invalid_data)

    def test_short_rationale(self):
        """Test that a rationale shorter than 10 characters is rejected."""
        invalid_data = {
            "modification_type": "layer_add",
            "magnitude": 2,
            "rationale": "Too short",
            "estimated_param_count": 1000
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**invalid_data)

    def test_negative_param_count(self):
        """Test that a negative estimated_param_count is rejected."""
        invalid_data = {
            "modification_type": "layer_add",
            "magnitude": 2,
            "rationale": "Testing negative param count.",
            "estimated_param_count": -100
        }
        with self.assertRaises(ValidationError):
            ModificationProposal(**invalid_data)

    def test_from_json_string_valid(self):
        """Test parsing from a valid JSON string."""
        json_str = json.dumps({
            "modification_type": "head_count_change",
            "magnitude": 4,
            "rationale": "Increasing attention heads to improve parallel processing capability.",
            "estimated_param_count": 2000000
        })
        proposal = ModificationProposal.from_json_string(json_str)
        self.assertEqual(proposal.modification_type, "head_count_change")
        self.assertEqual(proposal.magnitude, 4)

    def test_from_json_string_invalid_json(self):
        """Test that invalid JSON string raises JSONDecodeError."""
        invalid_json_str = "{ invalid json }"
        with self.assertRaises(json.JSONDecodeError):
            ModificationProposal.from_json_string(invalid_json_str)

    def test_from_json_string_missing_fields(self):
        """Test that missing required fields raise ValidationError."""
        json_str = json.dumps({
            "modification_type": "layer_add"
            # Missing magnitude, rationale, estimated_param_count
        })
        with self.assertRaises(ValidationError):
            ModificationProposal.from_json_string(json_str)

    def test_to_json_string(self):
        """Test serialization to JSON string."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Adding one layer for deeper representation.",
            estimated_param_count=5000000
        )
        json_str = proposal.to_json_string()
        data = json.loads(json_str)
        self.assertEqual(data["modification_type"], "layer_add")
        self.assertEqual(data["magnitude"], 1)
        self.assertEqual(data["estimated_param_count"], 5000000)


if __name__ == '__main__':
    unittest.main()