import unittest
from unittest.mock import patch, MagicMock
from pipeline.model import validate_modification_distinctness
from schemas.modification_proposal import ModificationProposal

class TestDistinctnessValidation(unittest.TestCase):

    def test_empty_history_returns_true(self):
        """If history is empty, any proposal should be distinct."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1.0,
            rationale="Test",
            estimated_param_count=100
        )
        self.assertTrue(validate_modification_distinctness(proposal, []))

    def test_different_type_is_distinct(self):
        """If type is different, it should be distinct regardless of magnitude."""
        history = [
            ModificationProposal(
                modification_type="head_count_change",
                magnitude=2.0,
                rationale="Old",
                estimated_param_count=100
            )
        ]
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=2.0, # Same magnitude, different type
            rationale="New",
            estimated_param_count=100
        )
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_same_type_different_magnitude_is_distinct(self):
        """If type is same but magnitude is >10% different, it should be distinct."""
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=10.0,
                rationale="Old",
                estimated_param_count=100
            )
        ]
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=15.0, # 50% difference
            rationale="New",
            estimated_param_count=100
        )
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_same_type_similar_magnitude_is_not_distinct(self):
        """If type is same and magnitude is <=10% different, it should NOT be distinct."""
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=10.0,
                rationale="Old",
                estimated_param_count=100
            )
        ]
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=10.5, # 5% difference
            rationale="New",
            estimated_param_count=100
        )
        self.assertFalse(validate_modification_distinctness(proposal, history))

    def test_same_type_same_magnitude_is_not_distinct(self):
        """If type and magnitude are identical, it should NOT be distinct."""
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=10.0,
                rationale="Old",
                estimated_param_count=100
            )
        ]
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=10.0,
            rationale="New",
            estimated_param_count=100
        )
        self.assertFalse(validate_modification_distinctness(proposal, history))

    def test_zero_magnitude_edge_case(self):
        """Test edge case where past magnitude is 0."""
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=0.0,
                rationale="Old",
                estimated_param_count=100
            )
        ]
        # New proposal with non-zero magnitude should be distinct
        proposal_distinct = ModificationProposal(
            modification_type="layer_add",
            magnitude=1.0,
            rationale="New",
            estimated_param_count=100
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
        # Should be distinct because type is different from one of them?
        # No, logic is: distinct if different from ALL in type OR magnitude.
        # My implementation: iterates, if ANY is same type and similar mag -> return False.
        # If loop completes -> True.
        
        # Case 1: New is same type as first, similar mag -> False
        proposal_fail = ModificationProposal("layer_add", 10.5, "New", 100)
        self.assertFalse(validate_modification_distinctness(proposal_fail, history))

        # Case 2: New is same type as first, diff mag; same type as second, diff mag; diff type from third -> True
        proposal_pass = ModificationProposal("layer_add", 50.0, "New", 100)
        self.assertTrue(validate_modification_distinctness(proposal_pass, history))
