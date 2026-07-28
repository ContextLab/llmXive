import unittest
from unittest.mock import patch, MagicMock
from pipeline.model import validate_modification_distinctness
from schemas.modification_proposal import ModificationProposal

class TestDistinctnessValidation(unittest.TestCase):

    def test_empty_history(self):
        """Test that a proposal is distinct when history is empty."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1.0,
            rationale="Test",
            estimated_param_count=100
        )
        history = []
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_different_type(self):
        """Test that a proposal with a different type is distinct."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1.0,
            rationale="Test",
            estimated_param_count=100
        )
        history = [
            ModificationProposal(
                modification_type="head_count_change",
                magnitude=2.0,
                rationale="Old",
                estimated_param_count=200
            )
        ]
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_same_type_different_magnitude_large_diff(self):
        """Test that same type with large magnitude difference is distinct."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=10.0,
            rationale="Test",
            estimated_param_count=100
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=1.0,
                rationale="Old",
                estimated_param_count=100
            )
        ]
        # 10.0 vs 1.0 is > 10% diff
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_same_type_similar_magnitude(self):
        """Test that same type with similar magnitude (within 10%) is NOT distinct."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1.05, # 5% diff from 1.0
            rationale="Test",
            estimated_param_count=100
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=1.0,
                rationale="Old",
                estimated_param_count=100
            )
        ]
        self.assertFalse(validate_modification_distinctness(proposal, history))

    def test_same_type_same_magnitude(self):
        """Test that same type and same magnitude is NOT distinct."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1.0,
            rationale="Test",
            estimated_param_count=100
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=1.0,
                rationale="Old",
                estimated_param_count=100
            )
        ]
        self.assertFalse(validate_modification_distinctness(proposal, history))

    def test_zero_magnitude_nonzero_proposal(self):
        """Test distinctness when history has 0 magnitude."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1.0,
            rationale="Test",
            estimated_param_count=100
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=0.0,
                rationale="Old",
                estimated_param_count=100
            )
        ]
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_both_zero_magnitude(self):
        """Test distinctness when both are 0 magnitude."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=0.0,
            rationale="Test",
            estimated_param_count=100
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=0.0,
                rationale="Old",
                estimated_param_count=100
            )
        ]
        self.assertFalse(validate_modification_distinctness(proposal, history))

if __name__ == "__main__":
    unittest.main()
