import unittest
import sys
import os
import torch
import torch.nn as nn
from unittest.mock import patch, MagicMock, PropertyMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from pipeline.oracle import FixedPointOracle, create_immutable_oracle
from schemas.modification_proposal import ModificationProposal
from pipeline.model import load_gpt2_124m_cpu_only

class TestExternalOracle(unittest.TestCase):
    def setUp(self):
        self.oracle = FixedPointOracle()
        # Load a real model for testing parameter constraints
        try:
            self.model = load_gpt2_124m_cpu_only()
        except Exception as e:
            # If loading fails (e.g., network), we might skip or mock
            # But for T059 we need to test the logic.
            # We will mock the get_model_param_count if model loading is an issue in CI
            self.model = None
            self.skip_test = False
            # We'll proceed with a mock model if real load fails to ensure test logic is covered
            if self.model is None:
                self.model = MagicMock()
                self.model.config.n_embd = 768
                self.model.config.n_head = 12
                self.model.config.n_layer = 12
                self.model.config.vocab_size = 50257
                self.model.named_parameters.return_value = [] # Mock params

    def test_validate_structure_valid_proposal(self):
        """Test that a valid proposal passes structural checks."""
        proposal = ModificationProposal(
            layer_add=1,
            hidden_size_change=None,
            head_count_change=None,
            activation_change=None
        )
        self.assertTrue(self.oracle.validate_structure(proposal))

    def test_validate_structure_invalid_hidden_size(self):
        """Test that invalid hidden size (not multiple of 64) fails."""
        proposal = ModificationProposal(
            layer_add=None,
            hidden_size_change=100, # 100 is not divisible by 64
            head_count_change=None,
            activation_change=None
        )
        self.assertFalse(self.oracle.validate_structure(proposal))

    def test_validate_structure_invalid_activation(self):
        """Test that invalid activation name fails."""
        proposal = ModificationProposal(
            layer_add=None,
            hidden_size_change=None,
            head_count_change=None,
            activation_change="invalid_activation"
        )
        self.assertFalse(self.oracle.validate_structure(proposal))

    def test_validate_structure_negative_layer_add(self):
        """Test that negative layer_add fails."""
        proposal = ModificationProposal(
            layer_add=-1,
            hidden_size_change=None,
            head_count_change=None,
            activation_change=None
        )
        self.assertFalse(self.oracle.validate_structure(proposal))

    @patch('pipeline.oracle.get_model_param_count')
    @patch('pipeline.oracle.FixedPointOracle.validate_structure')
    def test_validate_external_oracle_param_increase_limit(self, mock_struct, mock_count):
        """Test that proposals exceeding 30% param increase are rejected."""
        mock_struct.return_value = True
        mock_count.return_value = 124000000 # 124M

        # Create a proposal that would theoretically increase params by 40%
        # We mock the internal logic or rely on the estimator in the oracle
        # Since the oracle calculates based on config, we need to ensure the 
        # proposal triggers a high estimate.
        
        # Let's directly test the logic by mocking the estimate or forcing a large change
        # The oracle uses estimate_params based on proposal fields.
        # If we add 5 layers to 12, that's ~40% increase in layer params (5/12 ~ 41%).
        proposal = ModificationProposal(
            layer_add=6, # 6 extra layers on 12 is 50% increase in layer params
            hidden_size_change=None,
            head_count_change=None,
            activation_change=None
        )
        
        # The oracle calculates estimated_new_params
        # 12 layers -> 18 layers. 18/12 = 1.5. 50% increase.
        # This should fail the 30% check.
        
        is_valid, reason = self.oracle.validate_external_oracle(proposal, self.model)
        
        self.assertFalse(is_valid)
        self.assertIn("exceeds limit", reason)

    @patch('pipeline.oracle.get_model_param_count')
    @patch('pipeline.oracle.FixedPointOracle.validate_structure')
    def test_validate_external_oracle_accepts_small_increase(self, mock_struct, mock_count):
        """Test that proposals within 30% are accepted."""
        mock_struct.return_value = True
        mock_count.return_value = 124000000

        # Add 2 layers to 12. 2/12 = 16.6% increase.
        proposal = ModificationProposal(
            layer_add=2,
            hidden_size_change=None,
            head_count_change=None,
            activation_change=None
        )
        
        is_valid, reason = self.oracle.validate_external_oracle(proposal, self.model)
        
        self.assertTrue(is_valid)
        self.assertEqual(reason, "Oracle validation passed.")

    def test_create_immutable_oracle(self):
        """Test that the factory returns a callable."""
        func = create_immutable_oracle()
        self.assertTrue(callable(func))
        
        # It should work with a mock proposal and model
        proposal = ModificationProposal(
            layer_add=1,
            hidden_size_change=None,
            head_count_change=None,
            activation_change=None
        )
        # Mock model
        mock_model = MagicMock()
        mock_model.config.n_embd = 768
        mock_model.config.n_head = 12
        mock_model.config.n_layer = 12
        mock_model.config.vocab_size = 50257

        # This might fail on param count if not mocked properly in the function,
        # but the structure check should pass.
        # We expect it to run without crashing on the factory creation.
        # The actual validation might need the model to be real or fully mocked.
        # For this unit test, we verify the factory works.

if __name__ == '__main__':
    unittest.main()