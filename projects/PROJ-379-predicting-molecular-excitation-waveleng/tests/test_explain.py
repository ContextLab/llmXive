import pytest
import os
import json
import tempfile
import pandas as pd
import torch
from pathlib import Path

# Mock the necessary imports if they are not available in the test environment
# or assume the code is in the PYTHONPATH
from explain import explain_molecule, load_redundancy_masks, get_substructure_from_mask
from model import build_gnn_model

class TestExplainModule:
    
    @pytest.fixture
    def mock_model(self):
        """Create a dummy model for testing."""
        model = build_gnn_model()
        # Initialize with random weights
        for param in model.parameters():
            param.data = torch.randn(param.shape)
        return model

    @pytest.fixture
    def sample_smiles(self):
        return "CCO" # Ethanol

    @pytest.fixture
    def sample_redundancy_mask(self):
        # A simple list of 0s and 1s
        return [1, 0, 0, 0, 0, 0, 0, 0, 0, 0] # First feature is redundant

    def test_load_redundancy_masks_file_not_found(self):
        """Test that load_redundancy_masks returns empty dict if file not found."""
        result = load_redundancy_masks("non_existent_path.json")
        assert result == {}

    def test_load_redundancy_masks_success(self):
        """Test loading valid redundancy masks."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"mol_1": [1, 0, 1]}, f)
            temp_path = f.name
        
        try:
            result = load_redundancy_masks(temp_path)
            assert "mol_1" in result
            assert result["mol_1"] == [1, 0, 1]
        finally:
            os.remove(temp_path)

    def test_explain_molecule_invalid_smiles(self, mock_model):
        """Test explanation fails gracefully on invalid SMILES."""
        result = explain_molecule("INVALID_SMILES", mock_model, torch.device('cpu'))
        assert "error" in result
        assert "Invalid SMILES" in result["error"]

    def test_explain_molecule_valid_output(self, mock_model, sample_smiles):
        """Test that explain_molecule returns a valid dictionary structure."""
        result = explain_molecule(sample_smiles, mock_model, torch.device('cpu'))
        
        assert "smiles" in result
        assert result["smiles"] == sample_smiles
        assert "important_atom_indices" in result
        assert "important_atom_scores" in result
        assert "all_atom_scores" in result
        assert isinstance(result["important_atom_indices"], list)
        assert isinstance(result["all_atom_scores"], list)

    def test_explain_molecule_masking_applied(self, mock_model, sample_smiles, sample_redundancy_mask):
        """Test that masking is applied and reflected in output."""
        # We assume the mask logic zeroes out specific features.
        # Since we can't easily verify the internal float values without a real model,
        # we verify the 'mask_applied' flag.
        result = explain_molecule(sample_smiles, mock_model, torch.device('cpu'), redundancy_mask=sample_redundancy_mask)
        
        assert result.get("mask_applied") is True
        assert "all_atom_scores" in result

    def test_get_substructure_from_mask(self):
        """Test identifying important atoms from a mask."""
        smiles = "CCO"
        # Create a mock mask where only the first atom is important
        mock_scores = [10.0, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]
        
        # This function usually takes the mask (which might be the scores here in context of the helper)
        # But the signature in code is (smiles, mask, threshold). 
        # Let's assume 'mask' here refers to the attribution scores for this specific helper.
        important = get_substructure_from_mask(smiles, mock_scores, threshold=0.5)
        
        assert isinstance(important, list)
        assert 0 in important # First atom is important

    def test_integration_explain_with_redundancy_mask(self, mock_model, sample_smiles):
        """Integration test: explain a molecule with a redundancy mask and verify structure."""
        mask = [1 if i == 0 else 0 for i in range(10)] # Make first feature redundant
        result = explain_molecule(sample_smiles, mock_model, torch.device('cpu'), redundancy_mask=mask)
        
        assert result["mask_applied"] is True
        # Verify no error occurred
        assert "error" not in result
        
        # Verify the output can be serialized to JSON (contract test)
        try:
            json.dumps(result)
        except TypeError as e:
            pytest.fail(f"Result is not JSON serializable: {e}")
