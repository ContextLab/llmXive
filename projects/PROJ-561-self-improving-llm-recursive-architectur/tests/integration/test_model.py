import unittest
import json
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, PropertyMock

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.model import generate_modification_proposal, validate_proposal_param_count, inspect_model_structure
from schemas.modification_proposal import ModificationProposal
from config import get_config

class TestModelModificationProposal(unittest.TestCase):
    """Integration tests for T015: Proposal generation and validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = get_config()
        self.mock_model = MagicMock()
        self.mock_model.config = MagicMock()
        self.mock_model.config.n_layer = 12
        self.mock_model.config.n_embd = 768
        self.mock_model.config.n_head = 12
        self.mock_model.config.vocab_size = 50257

    def test_generate_proposal_valid_json(self):
        """
        Verify that generate_modification_proposal returns a valid JSON object
        with required keys: modification_type, magnitude, rationale.
        This satisfies the T015 verification requirement.
        """
        # Generate proposal
        proposal = generate_modification_proposal(self.mock_model, attempt=1)

        # Assert it is a ModificationProposal object
        self.assertIsInstance(proposal, ModificationProposal)

        # Assert required fields exist and are valid types
        self.assertIn(proposal.modification_type, ['layer_add', 'head_count_change'])
        self.assertIsInstance(proposal.magnitude, int)
        self.assertIsInstance(proposal.rationale, str)
        self.assertGreater(len(proposal.rationale), 0)

        # Verify it can be serialized to JSON
        json_str = proposal.model_dump_json()
        parsed = json.loads(json_str)
        self.assertIn('modification_type', parsed)
        self.assertIn('magnitude', parsed)
        self.assertIn('rationale', parsed)

    def test_validate_param_count_within_limit(self):
        """Test that valid proposals (<=130% params) are accepted."""
        baseline_params = 100_000_000  # 100M
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Test proposal"
        )
        # Estimated increase ~10M, total 110M <= 130M (130%)
        self.assertTrue(validate_proposal_param_count(proposal, baseline_params))

    def test_validate_param_count_exceeds_limit(self):
        """Test that invalid proposals (>130% params) are rejected."""
        baseline_params = 100_000_000  # 100M
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=5,  # Estimated 50M increase -> 150M > 130M
            rationale="Test proposal"
        )
        self.assertFalse(validate_proposal_param_count(proposal, baseline_params))

    def test_proposal_attempt_limit(self):
        """Test that proposal generation respects attempt limits (T090)."""
        # This test verifies that the attempt tracker is integrated
        # We expect AttemptLimitExceeded to be raised if attempt > 3
        from pipeline.attempt_tracker import AttemptLimitExceeded

        with self.assertRaises(AttemptLimitExceeded):
            generate_modification_proposal(self.mock_model, attempt=4)

    def test_template_rendering_mock(self):
        """
        Verify that the prompt template renders valid JSON for a mock input.
        This is a direct verification of the T015 requirement regarding templates.
        """
        # Create a mock template file
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = os.path.join(tmpdir, 'modification_proposal.j2')
            template_content = """You are an AI architect. Propose ONE architectural modification (type: layer_add/head_count_change, magnitude: int) to improve performance on training loss. DO NOT use benchmark scores. Return JSON: {modification_type, magnitude, rationale}."""
            with open(template_path, 'w') as f:
                f.write(template_content)

            # Patch the template path in the function
            with patch('pipeline.model.os.path.join') as mock_join:
                mock_join.return_value = template_path
                proposal = generate_modification_proposal(self.mock_model, attempt=1)

                # Assert proposal is valid
                self.assertIsNotNone(proposal)
                self.assertIsInstance(proposal, ModificationProposal)
                json.loads(proposal.model_dump_json())  # Should not raise

if __name__ == '__main__':
    unittest.main()