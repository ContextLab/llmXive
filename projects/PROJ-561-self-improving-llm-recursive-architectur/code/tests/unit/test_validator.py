"""
Unit tests for pipeline/validator.py (T059a).
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from schemas.modification_proposal import ModificationProposal
from pipeline.validator import validate_proposal_oracle, check_parameter_constraint, execute_distinctness_check


class TestValidatorOracleCheck(unittest.TestCase):

    def setUp(self):
        self.valid_proposal = ModificationProposal(
            modification_type='layer_add',
            magnitude=2,
            rationale='Adding layers to improve depth',
            estimated_param_count=150000000
        )
        self.invalid_type_proposal = ModificationProposal(
            modification_type='invalid_type',
            magnitude=2,
            rationale='Test',
            estimated_param_count=100
        )
        self.invalid_magnitude_proposal = ModificationProposal(
            modification_type='layer_add',
            magnitude=0,
            rationale='Test',
            estimated_param_count=100
        )
        self.empty_rationale_proposal = ModificationProposal(
            modification_type='layer_add',
            magnitude=2,
            rationale='',
            estimated_param_count=100
        )

    @patch('pipeline.validator.get_config')
    def test_validate_proposal_oracle_valid(self, mock_get_config):
        """Test that a valid proposal returns True."""
        mock_config = MagicMock()
        mock_config.safety_constraints.max_param_increase_percent = 0.30
        mock_get_config.return_value = mock_config

        result = validate_proposal_oracle(self.valid_proposal)
        self.assertTrue(result)

    @patch('pipeline.validator.get_config')
    def test_validate_proposal_oracle_invalid_type(self, mock_get_config):
        """Test that an invalid modification type returns False."""
        mock_config = MagicMock()
        mock_config.safety_constraints.max_param_increase_percent = 0.30
        mock_get_config.return_value = mock_config

        result = validate_proposal_oracle(self.invalid_type_proposal)
        self.assertFalse(result)

    @patch('pipeline.validator.get_config')
    def test_validate_proposal_oracle_invalid_magnitude(self, mock_get_config):
        """Test that a zero/negative magnitude returns False."""
        mock_config = MagicMock()
        mock_config.safety_constraints.max_param_increase_percent = 0.30
        mock_get_config.return_value = mock_config

        result = validate_proposal_oracle(self.invalid_magnitude_proposal)
        self.assertFalse(result)

    @patch('pipeline.validator.get_config')
    def test_validate_proposal_oracle_empty_rationale(self, mock_get_config):
        """Test that an empty rationale returns False."""
        mock_config = MagicMock()
        mock_config.safety_constraints.max_param_increase_percent = 0.30
        mock_get_config.return_value = mock_config

        result = validate_proposal_oracle(self.empty_rationale_proposal)
        self.assertFalse(result)

    @patch('pipeline.validator.get_config')
    def test_validate_proposal_oracle_invalid_config_limit(self, mock_get_config):
        """Test that an invalid config limit (<=0) returns False."""
        mock_config = MagicMock()
        mock_config.safety_constraints.max_param_increase_percent = -1.0
        mock_get_config.return_value = mock_config

        result = validate_proposal_oracle(self.valid_proposal)
        self.assertFalse(result)

    def test_check_parameter_constraint_within_limit(self):
        """Test parameter constraint check when within limit."""
        proposal = ModificationProposal(
            modification_type='layer_add',
            magnitude=1,
            rationale='Test',
            estimated_param_count=103000000
        )
        baseline = 100000000
        limit = 0.30  # 30%

        result = check_parameter_constraint(proposal, baseline, limit)
        self.assertTrue(result)

    def test_check_parameter_constraint_exceeds_limit(self):
        """Test parameter constraint check when exceeding limit."""
        proposal = ModificationProposal(
            modification_type='layer_add',
            magnitude=1,
            rationale='Test',
            estimated_param_count=140000000
        )
        baseline = 100000000
        limit = 0.30  # 30% -> max 130M

        result = check_parameter_constraint(proposal, baseline, limit)
        self.assertFalse(result)

    def test_check_parameter_constraint_no_estimate(self):
        """Test parameter constraint check when estimated_param_count is None."""
        proposal = ModificationProposal(
            modification_type='layer_add',
            magnitude=1,
            rationale='Test',
            estimated_param_count=None
        )
        baseline = 100000000
        limit = 0.30

        result = check_parameter_constraint(proposal, baseline, limit)
        self.assertFalse(result)

    def test_execute_distinctness_check_distinct(self):
        """Test distinctness check with a distinct proposal."""
        from schemas.modification_proposal import ModificationProposal
        proposal = ModificationProposal(
            modification_type='layer_add',
            magnitude=5,
            rationale='New distinct proposal',
            estimated_param_count=100
        )
        history = [
            ModificationProposal('layer_add', 2, 'Old', 100),
            ModificationProposal('head_count_change', 1, 'Old', 100)
        ]
        # We mock the internal call to pipeline.model.validate_modification_distinctness
        # because we don't have a full model to run it against, but we test the wrapper.
        with patch('pipeline.validator.validate_modification_distinctness', return_value=True):
            result = execute_distinctness_check(proposal, history)
            self.assertTrue(result)

    def test_execute_distinctness_check_not_distinct(self):
        """Test distinctness check with a non-distinct proposal."""
        proposal = ModificationProposal(
            modification_type='layer_add',
            magnitude=2,
            rationale='Duplicate',
            estimated_param_count=100
        )
        history = [
            ModificationProposal('layer_add', 2, 'Old', 100)
        ]
        with patch('pipeline.validator.validate_modification_distinctness', return_value=False):
            result = execute_distinctness_check(proposal, history)
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()