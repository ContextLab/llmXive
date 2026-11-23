import unittest
from unittest.mock import patch, MagicMock
from pipeline.model import validate_modification_distinctness
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

        # New proposal with zero magnitude should NOT be distinct
        proposal_same = ModificationProposal(
            modification_type="layer_add",
            magnitude=0.0,
            rationale="New",
            estimated_param_count=100
        )
        self.assertFalse(validate_modification_distinctness(proposal_same, history))

    def test_multiple_history_items(self):
        """Test against multiple history items, should be distinct if different from ALL."""
        history = [
            ModificationProposal("layer_add", 10.0, "Old1", 100),
            ModificationProposal("layer_add", 20.0, "Old2", 100),
            ModificationProposal("head_count_change", 5.0, "Old3", 100)
        ]
        # Case 1: New is same type as first, similar mag -> False
        proposal_fail = ModificationProposal("layer_add", 10.5, "New", 100)
        self.assertFalse(validate_modification_distinctness(proposal_fail, history))

        # Case 2: New is same type as first, diff mag; same type as second, diff mag; diff type from third -> True
        proposal_pass = ModificationProposal("layer_add", 50.0, "New", 100)
        self.assertTrue(validate_modification_distinctness(proposal_pass, history))