import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import torch
import torch.nn as nn
import math
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.model import validate_modification_distinctness, apply_architectural_modification
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
        # Case 1: New is same type as first, similar mag -> False
        proposal_fail = ModificationProposal("layer_add", 10.5, "New", 100)
        self.assertFalse(validate_modification_distinctness(proposal_fail, history))

        # Case 2: New is same type as first, diff mag; same type as second, diff mag; diff type from third -> True
        proposal_pass = ModificationProposal("layer_add", 50.0, "New", 100)
        self.assertTrue(validate_modification_distinctness(proposal_pass, history))

class TestArchitecturalModification(unittest.TestCase):
    
    def _create_dummy_model(self, n_embd=768, n_head=12, n_layer=2):
        """Creates a minimal GPT-like model for testing."""
        class DummyBlock(nn.Module):
            def __init__(self, n_embd, n_head):
                super().__init__()
                self.n_embd = n_embd
                self.n_head = n_head
                self.head_dim = n_embd // n_head
                self.ln_1 = nn.LayerNorm(n_embd)
                self.c_attn = nn.Linear(n_embd, 3 * n_embd)
                self.c_proj = nn.Linear(n_embd, n_embd)
                self.ln_2 = nn.LayerNorm(n_embd)
                self.c_fc = nn.Linear(n_embd, 4 * n_embd)
                self.c_proj_mlp = nn.Linear(4 * n_embd, n_embd)

            def forward(self, x):
                return x + self.c_proj(self.c_attn(x)) # Simplified

        class DummyGPT(nn.Module):
            def __init__(self, n_embd, n_head, n_layer):
                super().__init__()
                self.n_embd = n_embd
                self.n_head = n_head
                self.n_layer = n_layer
                self.wte = nn.Embedding(100, n_embd)
                self.wpe = nn.Embedding(10, n_embd)
                self.h = nn.ModuleList([DummyBlock(n_embd, n_head) for _ in range(n_layer)])
                self.ln_f = nn.LayerNorm(n_embd)
                self.lm_head = nn.Linear(n_embd, 100)
            
            def forward(self, x):
                return self.lm_head(x)

        model = DummyGPT(n_embd, n_head, n_layer)
        # Add config attribute for the apply function to read
        model.config = {'n_embd': n_embd, 'n_head': n_head, 'n_layer': n_layer}
        return model

    def test_layer_add_increases_param_count(self):
        """Adding layers should increase parameter count."""
        base = self._create_dummy_model(n_embd=64, n_head=4, n_layer=2)
        base_count = sum(p.numel() for p in base.parameters())
        
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Add one layer",
            estimated_param_count=100
        )
        
        new_model = apply_architectural_modification(base, proposal)
        new_count = sum(p.numel() for p in new_model.parameters())
        
        self.assertEqual(new_model.config['n_layer'], 3)
        self.assertGreater(new_count, base_count)

    def test_head_count_change_updates_structure(self):
        """Changing head count should update model structure."""
        base = self._create_dummy_model(n_embd=64, n_head=4, n_layer=2)
        
        proposal = ModificationProposal(
            modification_type="head_count_change",
            magnitude=2, # Increase to 6
            rationale="More heads",
            estimated_param_count=100
        )
        
        new_model = apply_architectural_modification(base, proposal)
        
        self.assertEqual(new_model.config['n_head'], 6)
        self.assertEqual(new_model.config['n_layer'], 2)
        
        # Verify weights are initialized (Xavier) and not all zeros
        for name, param in new_model.named_parameters():
            if 'weight' in name:
                self.assertNotEqual(param.abs().sum().item(), 0.0, f"Weight {name} is all zeros")

    def test_state_dict_mapping_preserves_values(self):
        """Existing weights should be preserved in the new model."""
        base = self._create_dummy_model(n_embd=64, n_head=4, n_layer=2)
        # Set a known value in a weight
        base.h[0].c_attn.weight.data.fill_(1.0)
        
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=1,
            rationale="Add layer",
            estimated_param_count=100
        )
        
        new_model = apply_architectural_modification(base, proposal)
        
        # Check that the first layer's weight is preserved (should be 1.0)
        # Note: The mapping logic in apply_architectural_modification tries to match keys.
        # In our dummy model, keys are h.0.c_attn.weight
        # In the new model, keys are h.0.c_attn.weight
        # So it should map.
        old_val = base.h[0].c_attn.weight.data[0, 0].item()
        new_val = new_model.h[0].c_attn.weight.data[0, 0].item()
        
        self.assertAlmostEqual(old_val, new_val, places=5)

    def test_invalid_modification_type_raises_error(self):
        """Should raise ValueError for unsupported modification type."""
        base = self._create_dummy_model()
        proposal = ModificationProposal(
            modification_type="invalid_type",
            magnitude=1,
            rationale="Test",
            estimated_param_count=100
        )
        with self.assertRaises(ValueError):
            apply_architectural_modification(base, proposal)

    def test_zero_magnitude_layer_add_raises_error(self):
        """Should raise ValueError for zero magnitude in layer_add."""
        base = self._create_dummy_model()
        proposal = ModificationProposal(
            modification_type="layer_add",
            magnitude=0,
            rationale="Test",
            estimated_param_count=100
        )
        with self.assertRaises(ValueError):
            apply_architectural_modification(base, proposal)

    def test_head_count_change_to_zero_raises_error(self):
        """Should raise ValueError if head count becomes zero or negative."""
        base = self._create_dummy_model(n_head=2)
        proposal = ModificationProposal(
            modification_type="head_count_change",
            magnitude=-2,
            rationale="Test",
            estimated_param_count=100
        )
        with self.assertRaises(ValueError):
            apply_architectural_modification(base, proposal)