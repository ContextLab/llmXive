import unittest
from typing import List
from schemas.modification_proposal import ModificationProposal
from pipeline.model import validate_modification_distinctness

class TestDistinctnessValidation(unittest.TestCase):
    
    def test_empty_history(self):
        """Test that any proposal is distinct when history is empty."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Test",
            estimated_param_count=100
        )
        history: List[ModificationProposal] = []
        self.assertTrue(validate_modification_distinctness(proposal, history))
    
    def test_different_type(self):
        """Test that different modification types are distinct."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Test",
            estimated_param_count=100
        )
        history = [
            ModificationProposal(
                modification_type="head_count_change",
                magnitude=1,
                rationale="History",
                estimated_param_count=100
            )
        ]
        self.assertTrue(validate_modification_distinctness(proposal, history))
    
    def test_same_type_different_magnitude(self):
        """Test that same type with different magnitude is distinct."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=2,
            rationale="Test",
            estimated_param_count=100
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=1,
                rationale="History",
                estimated_param_count=100
            )
        ]
        self.assertTrue(validate_modification_distinctness(proposal, history))
    
    def test_same_type_same_magnitude(self):
        """Test that same type and magnitude returns False."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Test",
            estimated_param_count=100
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=1,
                rationale="History",
                estimated_param_count=100
            )
        ]
        self.assertFalse(validate_modification_distinctness(proposal, history))
    
    def test_multiple_history_items(self):
        """Test validation against multiple history items."""
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=3,
            rationale="Test",
            estimated_param_count=100
        )
        history = [
            ModificationProposal(
                modification_type="layer_add",
                magnitude=1,
                rationale="History1",
                estimated_param_count=100
            ),
            ModificationProposal(
                modification_type="head_count_change",
                magnitude=2,
                rationale="History2",
                estimated_param_count=100
            ),
            ModificationProposal(
                modification_type="layer_add",
                magnitude=2,
                rationale="History3",
                estimated_param_count=100
            )
        ]
        self.assertTrue(validate_modification_distinctness(proposal, history))
    
    def test_float_magnitude_tolerance(self):
        """Test float magnitude comparison with tolerance."""
        proposal = ModificationProposal(
            modification_type="head_count_change",
            magnitude=1.5,
            rationale="Test",
            estimated_param_count=100
        )
        # This should be considered same due to tolerance
        history = [
            ModificationProposal(
                modification_type="head_count_change",
                magnitude=1.505,
                rationale="History",
                estimated_param_count=100
            )
        ]
        self.assertFalse(validate_modification_distinctness(proposal, history))
    
    def test_float_magnitude_distinct(self):
        """Test float magnitude comparison when clearly distinct."""
        proposal = ModificationProposal(
            modification_type="head_count_change",
            magnitude=1.5,
            rationale="Test",
            estimated_param_count=100
        )
        history = [
            ModificationProposal(
                modification_type="head_count_change",
                magnitude=2.0,
                rationale="History",
                estimated_param_count=100
            )
        ]
        self.assertTrue(validate_modification_distinctness(proposal, history))