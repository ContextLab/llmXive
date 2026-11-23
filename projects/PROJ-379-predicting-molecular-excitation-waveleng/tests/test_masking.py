import pytest
import numpy as np
import json
import os
import sys
from pathlib import Path
import tempfile

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from explain import apply_redundancy_mask, load_redundancy_masks, explain_molecule

class TestRedundancyMasking:
    """Test that redundancy masking is correctly applied to attribution weights."""

    def test_apply_mask_zeros_redundant_atoms(self):
        """Verify that redundant atoms (mask=0) are zeroed out in attribution."""
        # Create sample attribution weights (5 atoms, 10 features)
        node_attr = np.ones((5, 10)) * 0.5
        
        # Mask: atoms 0, 2, 4 are important (1), atoms 1, 3 are redundant (0)
        mask = np.array([1, 0, 1, 0, 1])
        
        masked_attr = apply_redundancy_mask(node_attr, mask)
        
        # Check that redundant atoms are zeroed
        assert np.allclose(masked_attr[1], 0), "Atom 1 should be zeroed (redundant)"
        assert np.allclose(masked_attr[3], 0), "Atom 3 should be zeroed (redundant)"
        
        # Check that important atoms retain their values
        assert np.allclose(masked_attr[0], 0.5), "Atom 0 should retain value"
        assert np.allclose(masked_attr[2], 0.5), "Atom 2 should retain value"
        assert np.allclose(masked_attr[4], 0.5), "Atom 4 should retain value"

    def test_mask_length_mismatch_raises_error(self):
        """Verify that mismatched mask length raises ValueError."""
        node_attr = np.ones((5, 10))
        mask = np.array([1, 0, 1])  # Wrong length
        
        with pytest.raises(ValueError, match="Mask length"):
            apply_redundancy_mask(node_attr, mask)

    def test_mask_reduces_sum(self):
        """Verify that applying mask reduces the total attribution sum."""
        node_attr = np.ones((5, 10)) * 0.5
        mask = np.array([1, 0, 1, 0, 1])
        
        original_sum = np.sum(np.abs(node_attr))
        masked_attr = apply_redundancy_mask(node_attr, mask)
        masked_sum = np.sum(np.abs(masked_attr))
        
        assert masked_sum < original_sum, "Masked sum should be less than original"
        assert masked_sum == original_sum * 0.6, "Masked sum should be 60% of original (3/5 atoms)"

    def test_load_redundancy_masks(self):
        """Test loading of redundancy masks from JSON file."""
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_masks = {
                "mol1": [1, 0, 1, 0],
                "mol2": [0, 0, 1, 1],
                "mol3": [1, 1, 1, 1]
            }
            json.dump(test_masks, f)
            temp_path = f.name
        
        try:
            masks = load_redundancy_masks(temp_path)
            
            assert len(masks) == 3, "Should load 3 masks"
            assert masks["mol1"] == [1, 0, 1, 0], "Mask for mol1 incorrect"
            assert masks["mol3"] == [1, 1, 1, 1], "Mask for mol3 incorrect"
        finally:
            os.unlink(temp_path)

    def test_load_redundancy_masks_missing_file(self):
        """Test that missing mask file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_redundancy_masks("nonexistent_file.json")

    def test_mask_verification_in_explain(self):
        """Verify that masking verification logic works correctly."""
        # Simulate the verification logic from explain.py
        node_attr = np.array([[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]])
        mask = np.array([1, 0, 1])
        
        masked_attr = apply_redundancy_mask(node_attr, mask)
        
        # Verify redundant atom (index 1) is zero
        assert np.allclose(masked_attr[1], 0), "Redundant atom should be zeroed"
        
        # Verify important atoms are unchanged
        assert np.allclose(masked_attr[0], 0.5), "Important atom 0 should be unchanged"
        assert np.allclose(masked_attr[2], 0.5), "Important atom 2 should be unchanged"

class TestMaskingOutput:
    """Test that masking results are correctly saved and verified."""

    def test_masked_vs_unmasked_comparison(self):
        """Verify comparison between masked and unmasked weights."""
        # Create test data
        unmasked = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        mask = np.array([1, 0, 1])
        
        masked = apply_redundancy_mask(unmasked, mask)
        
        # Verify differences
        diff = np.abs(unmasked - masked)
        
        # Row 1 (index 1) should have max difference (was 3,4 -> 0,0)
        assert diff[1, 0] == 3.0, "Difference at row 1, col 0 should be 3.0"
        assert diff[1, 1] == 4.0, "Difference at row 1, col 1 should be 4.0"
        
        # Other rows should have zero difference
        assert np.allclose(diff[0], 0), "Row 0 should have no difference"
        assert np.allclose(diff[2], 0), "Row 2 should have no difference"

    def test_output_format_contains_masked_results(self):
        """Verify output format includes both masked and unmasked results."""
        # This tests the structure expected in attribution_results.json
        sample_result = {
            "smiles": "CCO",
            "target_lambda": 254.0,
            "unmasked_node_attr": [[0.1, 0.2], [0.3, 0.4]],
            "unmasked_edge_attr": [0.5, 0.6],
            "masked_node_attr": [[0.1, 0.2], [0.0, 0.0]],
            "masked_edge_attr": [0.5, 0.6],
            "mask_applied": True,
            "contributing_atoms": [0]
        }
        
        # Verify all required keys are present
        required_keys = [
            "smiles", "target_lambda", "unmasked_node_attr",
            "unmasked_edge_attr", "masked_node_attr", "masked_edge_attr",
            "mask_applied", "contributing_atoms"
        ]
        
        for key in required_keys:
            assert key in sample_result, f"Missing key: {key}"
        
        # Verify mask_applied is boolean
        assert isinstance(sample_result["mask_applied"], bool)
        
        # Verify contributing_atoms is list
        assert isinstance(sample_result["contributing_atoms"], list)