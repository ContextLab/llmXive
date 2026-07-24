import unittest
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.model import validate_modification_distinctness
from schemas.modification_proposal import ModificationProposal

class TestDistinctnessValidation(unittest.TestCase):
    """
    Unit tests for validate_modification_distinctness in pipeline/model.py.
    This task (T014b) verifies that proposed architectural modifications
    are distinct from previous modifications in the history to prevent
    redundant self-improvement cycles.
    """

    def test_empty_history_is_always_distinct(self):
        """A proposal is distinct if there is no history."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Adding a layer to increase depth",
            estimated_param_count=1200000
        )
        history = []
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_same_type_different_magnitude_is_distinct(self):
        """Same type but different magnitude should be distinct."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=2,
            rationale="Adding 2 layers",
            estimated_param_count=2400000
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=1,
                rationale="Adding 1 layer",
                estimated_param_count=1200000
            )
        ]
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_different_type_same_magnitude_is_distinct(self):
        """Different type but same magnitude should be distinct."""
        proposal = ModificationProposal(
            modification_type="head_count_change",
            magnitude=2,
            rationale="Increasing heads",
            estimated_param_count=100000
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=2,
                rationale="Adding 2 layers",
                estimated_param_count=2400000
            )
        ]
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_exact_duplicate_is_not_distinct(self):
        """Exact duplicate (same type and magnitude) is NOT distinct."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Adding 1 layer",
            estimated_param_count=1200000
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=1,
                rationale="Adding 1 layer previously",
                estimated_param_count=1200000
            )
        ]
        self.assertFalse(validate_modification_distinctness(proposal, history))

    def test_magnitude_only_must_differ_for_same_type(self):
        """If type is same, magnitude must differ to be distinct."""
        proposal = ModificationProposal(
            modification_type="head_count_change",
            magnitude=4,
            rationale="Increase heads by 4",
            estimated_param_count=500000
        )
        history = [
            ModificationProposal(
                modification_type="head_count_change",
                magnitude=4,
                rationale="Previous attempt",
                estimated_param_count=500000
            )
        ]
        self.assertFalse(validate_modification_distinctness(proposal, history))

    def test_multiple_history_items(self):
        """Should be distinct if it doesn't match ANY item in history."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=5,
            rationale="Adding 5 layers",
            estimated_param_count=6000000
        )
        history = [
            ModificationProposal(modification_type="layer_add", magnitude=1, rationale="r1", estimated_param_count=100),
            ModificationProposal(modification_type="layer_add", magnitude=2, rationale="r2", estimated_param_count=200),
            ModificationProposal(modification_type="layer_add", magnitude=3, rationale="r3", estimated_param_count=300),
        ]
        # Magnitude 5 is distinct from 1, 2, 3
        self.assertTrue(validate_modification_distinctness(proposal, history))

    def test_duplicate_in_multi_item_history(self):
        """Should fail if it matches any item in a multi-item history."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=2,
            rationale="Adding 2 layers",
            estimated_param_count=2400000
        )
        history = [
            ModificationProposal(modification_type="layer_add", magnitude=1, rationale="r1", estimated_param_count=100),
            ModificationProposal(modification_type="layer_add", magnitude=2, rationale="r2", estimated_param_count=200), # Match here
            ModificationProposal(modification_type="layer_add", magnitude=3, rationale="r3", estimated_param_count=300),
        ]
        self.assertFalse(validate_modification_distinctness(proposal, history))

    def test_rationale_ignored_for_distinctness(self):
        """Distinctness is based on type and magnitude, not rationale text."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Completely different reason",
            estimated_param_count=1200000
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=1,
                rationale="Original reason",
                estimated_param_count=1200000
            )
        ]
        # Same type and magnitude -> not distinct, regardless of rationale
        self.assertFalse(validate_modification_distinctness(proposal, history))

if __name__ == "__main__":
    unittest.main()