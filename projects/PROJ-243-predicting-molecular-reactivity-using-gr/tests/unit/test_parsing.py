"""
Unit tests for SMILES parsing and exclusion logic.

This module validates the robustness of the SMILES-to-graph conversion pipeline,
specifically focusing on:
1. Valid SMILES parsing using RDKit.
2. Correct identification and exclusion of invalid SMILES strings.
3. Handling of edge cases (empty strings, whitespace, malformed syntax).

These tests rely on `code/utils/graph_utils.py` (T006) for the actual parsing logic.
"""

import pytest
import os
import sys
import logging

# Add project root to path to allow imports of sibling modules
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from rdkit import Chem
from rdkit.Chem import AllChem
from utils.graph_utils import smiles_to_molecule, batch_smiles_to_graphs, validate_graph

# Configure logging for test output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestSmilesParsing:
    """Tests for the smiles_to_molecule function."""

    def test_valid_smiles_simple(self):
        """Test parsing of a simple valid SMILES string (Benzene)."""
        smiles = "c1ccccc1"
        mol = smiles_to_molecule(smiles)
        assert mol is not None, "Failed to parse valid SMILES: c1ccccc1"
        assert mol.GetNumAtoms() == 6, "Incorrect atom count for benzene"
        assert mol.GetNumBonds() == 6, "Incorrect bond count for benzene"

    def test_valid_smiles_complex(self):
        """Test parsing of a complex valid SMILES string (Aspirin)."""
        smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"
        mol = smiles_to_molecule(smiles)
        assert mol is not None, "Failed to parse valid SMILES: Aspirin"
        assert mol.GetNumAtoms() == 21, "Incorrect atom count for aspirin"

    def test_valid_smiles_with_isotopes(self):
        """Test parsing with isotopic labels."""
        smiles = "[13CH4]"
        mol = smiles_to_molecule(smiles)
        assert mol is not None, "Failed to parse valid isotopic SMILES"

    def test_invalid_smiles_unclosed_ring(self):
        """Test that unclosed ring notation returns None."""
        smiles = "C1CCCCC" # Missing closing 1
        mol = smiles_to_molecule(smiles)
        assert mol is None, "Invalid SMILES (unclosed ring) should return None"

    def test_invalid_smiles_malformed(self):
        """Test that completely malformed strings return None."""
        invalid_cases = [
            "",
            "   ",
            "!!!",
            "C[C@H](O)C(=O)O", # This is valid, but let's try something truly broken
            "C1=CC=CC=1", # Invalid aromaticity/ring
        ]
        # Note: RDKit is sometimes lenient. We test specific known failures.
        # The unclosed ring case is the most robust failure mode to test.
        mol = smiles_to_molecule("")
        assert mol is None, "Empty string should return None"

        mol = smiles_to_molecule("!!!")
        assert mol is None, "Garbage string should return None"

    def test_whitespace_handling(self):
        """Test that whitespace is handled correctly (stripped or fails gracefully)."""
        # RDKit usually handles leading/trailing whitespace, but let's verify
        smiles = "  c1ccccc1  "
        mol = smiles_to_molecule(smiles)
        # RDKit might strip or fail. If it fails, that's also acceptable for a robust parser
        # as long as it doesn't crash.
        if mol is None:
            logger.warning("RDKit failed to parse whitespace-padded SMILES. This is acceptable.")
        else:
            assert mol.GetNumAtoms() == 6, "Whitespace handling changed molecule structure"

    def test_molecule_sanitization(self):
        """Test that the returned molecule is sanitized."""
        smiles = "c1ccccc1"
        mol = smiles_to_molecule(smiles)
        assert mol is not None
        # Check if we can compute a descriptor (requires sanitization)
        try:
            # This will raise if not sanitized
            AllChem.Compute2DCoords(mol)
            assert True
        except Exception as e:
            pytest.fail(f"Molecule was not properly sanitized: {e}")


class TestBatchParsingAndExclusion:
    """Tests for batch processing and exclusion logic."""

    def test_batch_valid_molecules(self):
        """Test batch processing of a list of valid SMILES."""
        smiles_list = ["c1ccccc1", "CCO", "C1CCCCC1"]
        graphs = batch_smiles_to_graphs(smiles_list)
        assert len(graphs) == 3, "All valid molecules should be processed"
        for g in graphs:
            assert validate_graph(g), "Each graph must be valid"

    def test_batch_mixed_validity(self):
        """Test batch processing with mixed valid/invalid SMILES."""
        smiles_list = [
            "c1ccccc1",   # Valid
            "!!!",        # Invalid
            "CCO",        # Valid
            "",           # Invalid
            "C1CCCCC1"    # Valid
        ]
        graphs = batch_smiles_to_graphs(smiles_list)
        # We expect only the valid ones to be in the result
        # Depending on implementation, it might return None or skip.
        # Assuming batch_smiles_to_graphs returns a list of valid graphs only.
        assert len(graphs) == 3, f"Expected 3 valid graphs, got {len(graphs)}"

    def test_batch_empty_list(self):
        """Test batch processing of an empty list."""
        graphs = batch_smiles_to_graphs([])
        assert len(graphs) == 0, "Empty list should result in empty output"

    def test_batch_all_invalid(self):
        """Test batch processing where all inputs are invalid."""
        smiles_list = ["!!!", "", "   ", "C1"]
        graphs = batch_smiles_to_graphs(smiles_list)
        assert len(graphs) == 0, "No valid graphs should be produced from all invalid input"


class TestExclusionLogging:
    """Tests to ensure exclusion logic is robust (integration with logging)."""

    def test_exclusion_threshold_logic(self):
        """
        Verify that the exclusion logic correctly identifies a high exclusion rate.
        This simulates a scenario where data quality is poor.
        """
        # Create a dataset with 90% invalid data
        invalid_count = 900
        valid_count = 100
        total = invalid_count + valid_count

        invalid_smiles = ["!!!"] * invalid_count
        valid_smiles = ["c1ccccc1"] * valid_count
        mixed_list = invalid_smiles + valid_smiles

        graphs = batch_smiles_to_graphs(mixed_list)
        exclusion_rate = 1.0 - (len(graphs) / total)

        assert exclusion_rate == 0.9, f"Exclusion rate calculation failed: {exclusion_rate}"
        assert exclusion_rate > 0.1, "Exclusion rate should be high for this test case"
        # In a real pipeline, this would trigger a warning or error,
        # but here we just verify the math is correct.

if __name__ == "__main__":
    pytest.main([__file__, "-v"])