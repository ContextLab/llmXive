import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import torch
import torch.nn as nn
import math
import sys
import os

# Add code directory to path if not already present
if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from schemas.modification_proposal import ModificationProposal
from pipeline.model import validate_modification_distinctness

class TestDistinctnessValidation(unittest.TestCase):
    """Unit tests for the validate_modification_distinctness function."""

    def test_empty_history_returns_true(self):
        """A proposal is distinct if the history is empty."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Add a layer",
            estimated_param_count=1000
        )
        self.assertTrue(validate_modification_distinctness(proposal, []))

    def test_distinct_type_returns_true(self):
        """A proposal with a different type is distinct."""
        history = [
            ModificationProposal(
                modification_type="head_count_change",
                magnitude=2,
                rationale="Change heads",
                estimated_param_count=500
            )
        ]
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=2,
            rationale="Add a layer",
            estimated_param_count=1000
        )
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_distinct_magnitude_returns_true(self):
        """A proposal with the same type but different magnitude is distinct."""
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=1,
                rationale="Add 1 layer",
                estimated_param_count=1000
            )
        ]
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=2,
            rationale="Add 2 layers",
            estimated_param_count=2000
        )
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_same_type_and_magnitude_returns_false(self):
        """A proposal with same type and magnitude as history is NOT distinct."""
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=2,
                rationale="Add 2 layers",
                estimated_param_count=2000
            )
        ]
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=2,
            rationale="Add 2 layers again",
            estimated_param_count=2000
        )
        self.assertFalse(validate_modification_distinctness(proposal, history))

    def test_multiple_history_entries(self):
        """Check distinctness against multiple history entries."""
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=1,
                rationale="First add",
                estimated_param_count=1000
            ),
            ModificationProposal(
                modification_type="head_count_change",
                magnitude=4,
                rationale="First head change",
                estimated_param_count=500
            )
        ]
        
        # Distinct from both
        proposal_distinct = ModificationProposal(
            modification_type="layer_add",
            magnitude=3,
            rationale="Third add",
            estimated_param_count=3000
        )
        self.assertTrue(validate_modification_distinctness(proposal_distinct, history))

        # Matches first entry (type and magnitude)
        proposal_match_1 = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Duplicate first",
            estimated_param_count=1000
        )
        self.assertFalse(validate_modification_distinctness(proposal_match_1, history))

        # Matches second entry (type and magnitude)
        proposal_match_2 = ModificationProposal(
            modification_type="head_count_change",
            magnitude=4,
            rationale="Duplicate second",
            estimated_param_count=500
        )
        self.assertFalse(validate_modification_distinctness(proposal_match_2, history))

if __name__ == '__main__':
    unittest.main()