import pytest
import sys
import os

# Ensure code/ is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ingest import validate_smiles, smiles_to_molecular_graph

class TestIngestValidation:
    def test_smiles_validation_rejects_invalid(self):
        """
        Unit test for SMILES validation rejecting invalid strings.
        Ensures that the validator correctly identifies non-chemical strings.
        """
        invalid_smiles_list = [
            "",
            None,
            "This is not a valid SMILES string",
            "C1CC1C1CC1C1CC1C1CC1C1CC1C1CC1", # Highly unlikely to be valid ring structure in this context
            "12345",
            "!@#$%"
        ]
        
        for smiles in invalid_smiles_list:
            assert validate_smiles(smiles) is False, f"Expected {smiles} to be rejected"

    def test_smiles_validation_accepts_valid(self):
        """
        Unit test for SMILES validation accepting valid strings.
        """
        valid_smiles_list = [
            "CCO",
            "c1ccccc1",
            "CC(=O)O",
            "CC1=CC=CC=C1",
            "C[C@H](O)C(=O)O"
        ]
        
        for smiles in valid_smiles_list:
            assert validate_smiles(smiles) is True, f"Expected {smiles} to be accepted"

    def test_graph_conversion_from_valid_smiles(self):
        """
        Unit test for RDKit graph conversion from valid SMILES.
        """
        smiles = "CCO"
        graph = smiles_to_molecular_graph(smiles)
        
        assert graph is not None
        assert graph.smiles == smiles
        assert graph.num_atoms == 3 # C-C-O
        assert graph.num_bonds == 2 # C-C, C-O
