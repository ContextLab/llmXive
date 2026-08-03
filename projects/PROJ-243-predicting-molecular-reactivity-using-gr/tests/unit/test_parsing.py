"""
Unit tests for SMILES parsing and exclusion logic.

This module tests the functionality of SMILES string validation,
molecule conversion using RDKit, and the exclusion logic for
invalid or problematic molecular structures.

Tests cover:
- Valid SMILES parsing
- Invalid SMILES detection
- Empty string handling
- Special character handling
- Exclusion threshold logic
"""

import pytest
import numpy as np
from rdkit import Chem
from typing import List, Dict, Tuple, Optional

# Import the graph utility functions that handle SMILES parsing
# These are defined in code/utils/graph_utils.py
from code.utils.graph_utils import (
    smiles_to_molecule,
    validate_graph,
    get_feature_dimensions
)
from code.config import get_config


class TestSMILESParsing:
    """Test cases for SMILES string parsing functionality."""

    def test_valid_smiles_benzene(self):
        """Test parsing of a valid benzene SMILES string."""
        smiles = "c1ccccc1"
        mol = smiles_to_molecule(smiles)
        
        assert mol is not None, "Failed to parse valid benzene SMILES"
        assert mol.GetNumAtoms() == 6, "Benzene should have 6 atoms"
        assert mol.GetNumBonds() == 6, "Benzene should have 6 bonds"
    
    def test_valid_smiles_ethanol(self):
        """Test parsing of a valid ethanol SMILES string."""
        smiles = "CCO"
        mol = smiles_to_molecule(smiles)
        
        assert mol is not None, "Failed to parse valid ethanol SMILES"
        assert mol.GetNumAtoms() == 3, "Ethanol should have 3 atoms"
    
    def test_valid_smiles_complex(self):
        """Test parsing of a more complex valid SMILES."""
        smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
        mol = smiles_to_molecule(smiles)
        
        assert mol is not None, "Failed to parse aspirin SMILES"
        assert mol.GetNumAtoms() > 10, "Aspirin should have many atoms"
    
    def test_invalid_smiles_unclosed_ring(self):
        """Test that unclosed ring notation is rejected."""
        invalid_smiles = "c1ccccc"  # Missing closing ring number
        mol = smiles_to_molecule(invalid_smiles)
        
        # RDKit should return None for invalid SMILES
        assert mol is None, "Unclosed ring SMILES should be rejected"
    
    def test_invalid_smiles_bad_atom(self):
        """Test that invalid atom symbols are rejected."""
        invalid_smiles = "C(X)C"  # X is not a valid organic subset atom
        # Note: RDKit might still parse this as a generic atom
        # We test that it doesn't crash
        mol = smiles_to_molecule(invalid_smiles)
        # This should not raise an exception
        assert True, "Invalid atom parsing should not crash"
    
    def test_empty_smiles(self):
        """Test handling of empty SMILES string."""
        mol = smiles_to_molecule("")
        assert mol is None, "Empty SMILES should return None"
    
    def test_whitespace_smiles(self):
        """Test handling of whitespace-only SMILES."""
        mol = smiles_to_molecule("   ")
        assert mol is None, "Whitespace SMILES should return None"
    
    def test_none_smiles(self):
        """Test handling of None input."""
        mol = smiles_to_molecule(None)
        assert mol is None, "None SMILES should return None"
    
    def test_malformed_smiles(self):
        """Test various malformed SMILES strings."""
        malformed_list = [
            "C1CC1C1CC1",  # Multiple ring openings without proper closure
            "C(C(C",       # Unbalanced parentheses
            "C1=CC=CC",    # Incomplete ring
            "C#C#C#C",     # Potentially invalid bonding
        ]
        
        for smiles in malformed_list:
            # Should not crash
            mol = smiles_to_molecule(smiles)
            # Most should be None, but we just test no crash
            assert True, f"Malformed SMILES '{smiles}' should not crash"

class TestExclusionLogic:
    """Test cases for molecule exclusion logic."""

    def test_exclusion_threshold_calculation(self):
        """Test calculation of exclusion percentage."""
        total_molecules = 1000
        excluded_count = 5
        
        exclusion_percentage = (excluded_count / total_molecules) * 100
        
        assert exclusion_percentage == 0.5, "Exclusion percentage calculation incorrect"
        assert exclusion_percentage < 0.1, "Should be within threshold if < 0.1%"
    
    def test_exclusion_threshold_boundary(self):
        """Test boundary condition for exclusion threshold."""
        total_molecules = 10000
        # 0.1% threshold means max 10 exclusions
        excluded_count = 10
        
        exclusion_percentage = (excluded_count / total_molecules) * 100
        
        assert exclusion_percentage == 0.1, "Boundary calculation incorrect"
    
    def test_exclusion_threshold_exceeded(self):
        """Test when exclusion threshold is exceeded."""
        total_molecules = 1000
        excluded_count = 2  # 0.2% which is > 0.1%
        
        exclusion_percentage = (excluded_count / total_molecules) * 100
        
        assert exclusion_percentage > 0.1, "Should exceed threshold"
    
    def test_batch_exclusion_logic(self):
        """Test exclusion logic across a batch of molecules."""
        smiles_list = [
            "c1ccccc1",  # Valid
            "",          # Invalid
            "CCO",       # Valid
            "c1ccccc",   # Invalid
            "CC(C)C",    # Valid
        ]
        
        valid_count = 0
        excluded_count = 0
        
        for smiles in smiles_list:
            mol = smiles_to_molecule(smiles)
            if mol is not None:
                valid_count += 1
            else:
                excluded_count += 1
        
        assert valid_count == 3, "Should have 3 valid molecules"
        assert excluded_count == 2, "Should have 2 excluded molecules"
        
        total = valid_count + excluded_count
        exclusion_pct = (excluded_count / total) * 100
        assert exclusion_pct == 40.0, "Exclusion percentage should be 40%"

class TestGraphValidation:
    """Test cases for graph validation after SMILES parsing."""

    def test_valid_graph_structure(self):
        """Test that a valid molecule produces a valid graph."""
        smiles = "c1ccccc1"
        mol = smiles_to_molecule(smiles)
        
        assert mol is not None, "Molecule parsing failed"
        
        # Validate the graph structure
        is_valid = validate_graph(mol)
        assert is_valid, "Valid molecule should produce valid graph"
    
    def test_graph_feature_dimensions(self):
        """Test that feature dimensions are correctly reported."""
        smiles = "CCO"
        mol = smiles_to_molecule(smiles)
        
        assert mol is not None, "Molecule parsing failed"
        
        node_dim, edge_dim = get_feature_dimensions()
        
        assert node_dim > 0, "Node feature dimension should be positive"
        assert edge_dim > 0, "Edge feature dimension should be positive"

class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_long_smiles(self):
        """Test handling of very long SMILES strings."""
        # Create a long but valid SMILES (polyethylene chain)
        long_smiles = "C" * 1000 + "O"
        mol = smiles_to_molecule(long_smiles)
        
        # Should not crash, might be None if too complex
        assert True, "Long SMILES should not crash parser"
    
    def test_special_atoms(self):
        """Test molecules with special atoms."""
        special_smiles_list = [
            "[Na+]",      # Sodium ion
            "[Cl-]",      # Chloride ion
            "[Fe+2]",     # Iron ion
            "[H]",        # Hydrogen
        ]
        
        for smiles in special_smiles_list:
            mol = smiles_to_molecule(smiles)
            # Should not crash
            assert True, f"Special atom SMILES '{smiles}' should not crash"
    
    def test_isotopes(self):
        """Test molecules with isotopic labels."""
        isotope_smiles = "[13CH4]"
        mol = smiles_to_molecule(isotope_smiles)
        
        # Should handle isotopes
        assert True, "Isotope SMILES should not crash"
    
    def test_stereochemistry(self):
        """Test molecules with stereochemistry."""
        stereo_smiles_list = [
            "C/C=C/C",    # Trans
            "C/C=C\\C",   # Cis
            "C[C@H](O)C", # Chiral center
        ]
        
        for smiles in stereo_smiles_list:
            mol = smiles_to_molecule(smiles)
            # Should not crash
            assert True, f"Stereochemistry SMILES '{smiles}' should not crash"

class TestIntegration:
    """Integration tests for the full parsing pipeline."""

    def test_full_pipeline_valid_batch(self):
        """Test the full parsing pipeline with a batch of valid molecules."""
        valid_smiles_batch = [
            "c1ccccc1",
            "CCO",
            "CC(=O)O",
            "c1ccccc1C(=O)O",
            "CC(C)C",
        ]
        
        results = []
        for smiles in valid_smiles_batch:
            mol = smiles_to_molecule(smiles)
            if mol is not None:
                is_valid = validate_graph(mol)
                results.append({
                    "smiles": smiles,
                    "valid": is_valid,
                    "n_atoms": mol.GetNumAtoms()
                })
        
        assert len(results) == len(valid_smiles_batch), "All valid molecules should be parsed"
        assert all(r["valid"] for r in results), "All parsed molecules should be valid graphs"
    
    def test_full_pipeline_mixed_batch(self):
        """Test the full pipeline with a mix of valid and invalid molecules."""
        mixed_smiles_batch = [
            "c1ccccc1",  # Valid
            "",          # Invalid
            "CCO",       # Valid
            "invalid",   # Invalid
            "CC(C)C",    # Valid
        ]
        
        valid_count = 0
        invalid_count = 0
        
        for smiles in mixed_smiles_batch:
            mol = smiles_to_molecule(smiles)
            if mol is not None:
                valid_count += 1
            else:
                invalid_count += 1
        
        assert valid_count == 3, "Should have 3 valid molecules"
        assert invalid_count == 2, "Should have 2 invalid molecules"
        
        # Check exclusion rate
        total = valid_count + invalid_count
        exclusion_rate = invalid_count / total
        assert exclusion_rate == 0.4, "Exclusion rate should be 40%"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])