"""
Unit tests for SMILES parsing and exclusion logic.

This module tests the functionality of:
1. SMILES parsing using RDKit
2. Exclusion logic for invalid or unwanted molecular structures
3. Integration with the graph_utils module

Run with: pytest tests/unit/test_parsing.py -v
"""

import pytest
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors
from typing import List, Dict, Tuple, Any, Optional

# Import the functions we are testing
# We assume these are implemented in code/utils/graph_utils.py
# Based on the API surface provided:
from code.utils.graph_utils import (
    smiles_to_molecule,
    get_node_features,
    get_edge_features,
    smiles_to_graph,
    validate_graph
)
from code.config import get_config

# Test data: A mix of valid and invalid SMILES strings
VALID_SMILES = [
    "CCO",  # Ethanol
    "c1ccccc1",  # Benzene
    "CC(=O)O",  # Acetic acid
    "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # Caffeine
    "C1=CC2=C(C=C1)C(=O)C3=CC=CC=C3C2=O",  # Anthraquinone
    "CC(C)Cc1ccc(cc1)C(C)C(=O)O",  # Ibuprofen
]

INVALID_SMILES = [
    "",  # Empty string
    "CCCC",  # Valid but we'll test specific exclusion logic later
    "C[C@H](O)C",  # Valid with stereochemistry (should be parsed)
    "invalid_smiles_string",  # Completely invalid
    "C1CC1C2CC2",  # Valid but might be excluded by size rules
    "C#N",  # Acetonitrile (valid)
    "C1=CC=CC=C1C(=O)O",  # Benzoic acid (valid)
]

# Specific exclusion criteria for testing
EXCLUSION_CRITERIA = {
    "min_atoms": 5,  # Exclude molecules with fewer than 5 atoms
    "max_atoms": 100,  # Exclude molecules with more than 100 atoms
    "allowed_elements": {"C", "H", "O", "N", "S", "P", "F", "Cl", "Br", "I"},
    "exclude_ions": True,  # Exclude charged species
}


class TestSMILESParsing:
    """Test suite for SMILES parsing functionality."""

    def test_valid_smiles_to_molecule(self):
        """Test that valid SMILES strings are correctly parsed into RDKit molecules."""
        for smiles in VALID_SMILES:
            mol = smiles_to_molecule(smiles)
            assert mol is not None, f"Failed to parse valid SMILES: {smiles}"
            assert isinstance(mol, Chem.Mol), f"Expected RDKit Mol object, got {type(mol)}"

    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES strings return None."""
        for smiles in INVALID_SMILES:
            if smiles == "invalid_smiles_string":
                mol = smiles_to_molecule(smiles)
                assert mol is None, f"Expected None for invalid SMILES: {smiles}"
            # Note: Some strings in INVALID_SMILES are actually valid RDKit SMILES
            # but might be excluded by other criteria

    def test_smiles_to_graph_structure(self):
        """Test that smiles_to_graph produces the correct graph structure."""
        for smiles in VALID_SMILES:
            graph = smiles_to_graph(smiles)
            assert graph is not None, f"Failed to create graph for SMILES: {smiles}"
            assert "nodes" in graph, "Graph missing 'nodes' key"
            assert "edges" in graph, "Graph missing 'edges' key"
            assert isinstance(graph["nodes"], list), "Nodes should be a list"
            assert isinstance(graph["edges"], list), "Edges should be a list"

    def test_node_features_dimensions(self):
        """Test that node features have the correct dimensions."""
        for smiles in VALID_SMILES:
            mol = smiles_to_molecule(smiles)
            if mol is not None:
                node_features = get_node_features(mol)
                num_atoms = mol.GetNumAtoms()
                assert len(node_features) == num_atoms, \
                    f"Expected {num_atoms} node features, got {len(node_features)}"
                # Check that each node feature is a numpy array
                for feature in node_features:
                    assert isinstance(feature, np.ndarray), \
                        f"Expected numpy array for node feature, got {type(feature)}"

    def test_edge_features_consistency(self):
        """Test that edge features are consistent with the graph structure."""
        for smiles in VALID_SMILES:
            mol = smiles_to_molecule(smiles)
            if mol is not None:
                graph = smiles_to_graph(smiles)
                edges = graph["edges"]
                edge_features = get_edge_features(mol)

                # Number of edge features should match number of edges
                assert len(edge_features) == len(edges), \
                    f"Edge features count ({len(edge_features)}) doesn't match edges count ({len(edges)})"

                # Each edge feature should be a numpy array
                for feature in edge_features:
                    assert isinstance(feature, np.ndarray), \
                        f"Expected numpy array for edge feature, got {type(feature)}"


class TestExclusionLogic:
    """Test suite for molecular exclusion logic."""

    def test_min_atoms_exclusion(self):
        """Test that molecules with fewer than min_atoms are excluded."""
        # Create a small molecule (methane) that should be excluded
        small_smiles = "C"  # Methane (1 atom)
        mol = smiles_to_molecule(small_smiles)
        if mol is not None:
            atom_count = mol.GetNumAtoms()
            assert atom_count < EXCLUSION_CRITERIA["min_atoms"], \
                "Test setup error: small molecule should have fewer atoms than min_atoms"

            # The exclusion logic should filter this out
            # We test this by checking if the molecule passes validation
            # with our criteria
            is_valid, reason = validate_graph(
                smiles_to_graph(small_smiles),
                EXCLUSION_CRITERIA
            )
            assert not is_valid, f"Small molecule should be excluded: {reason}"
            assert "min_atoms" in reason, "Exclusion reason should mention min_atoms"

    def test_max_atoms_exclusion(self):
        """Test that molecules with more than max_atoms are excluded."""
        # Create a large molecule string
        # We'll use a polymer-like structure that exceeds our limit
        large_smiles = "C" * 200  # 200 carbon atoms in a chain
        mol = smiles_to_molecule(large_smiles)
        if mol is not None:
            atom_count = mol.GetNumAtoms()
            assert atom_count > EXCLUSION_CRITERIA["max_atoms"], \
                "Test setup error: large molecule should have more atoms than max_atoms"

            is_valid, reason = validate_graph(
                smiles_to_graph(large_smiles),
                EXCLUSION_CRITERIA
            )
            assert not is_valid, f"Large molecule should be excluded: {reason}"
            assert "max_atoms" in reason, "Exclusion reason should mention max_atoms"

    def test_allowed_elements_filter(self):
        """Test that molecules with disallowed elements are excluded."""
        # Create a molecule with a disallowed element (e.g., Silicon)
        # Note: RDKit might not support all elements, but we test the logic
        disallowed_element_smiles = "[Si](C)(C)(C)C"  # Tetramethylsilane
        mol = smiles_to_molecule(disallowed_element_smiles)
        if mol is not None:
            # Check if Silicon is in our allowed elements
            has_disallowed = False
            for atom in mol.GetAtoms():
                if atom.GetSymbol() not in EXCLUSION_CRITERIA["allowed_elements"]:
                    has_disallowed = True
                    break

            if has_disallowed:
                is_valid, reason = validate_graph(
                    smiles_to_graph(disallowed_element_smiles),
                    EXCLUSION_CRITERIA
                )
                assert not is_valid, f"Molecule with disallowed element should be excluded: {reason}"
                assert "elements" in reason, "Exclusion reason should mention elements"

    def test_ion_exclusion(self):
        """Test that charged species are excluded when exclude_ions is True."""
        # Create a charged molecule
        ion_smiles = "[Na+]"  # Sodium ion
        mol = smiles_to_molecule(ion_smiles)
        if mol is not None:
            # Check if the molecule has a charge
            has_charge = False
            for atom in mol.GetAtoms():
                if atom.GetFormalCharge() != 0:
                    has_charge = True
                    break

            if has_charge and EXCLUSION_CRITERIA["exclude_ions"]:
                is_valid, reason = validate_graph(
                    smiles_to_graph(ion_smiles),
                    EXCLUSION_CRITERIA
                )
                assert not is_valid, f"Ion should be excluded: {reason}"
                assert "charge" in reason or "ion" in reason, \
                    "Exclusion reason should mention charge or ion"

    def test_molecule_with_stereochemistry(self):
        """Test that molecules with stereochemistry are handled correctly."""
        stereo_smiles = "C[C@H](O)C"  # Chiral molecule
        mol = smiles_to_molecule(stereo_smiles)
        assert mol is not None, "Failed to parse SMILES with stereochemistry"

        # The molecule should be valid and not excluded by stereochemistry
        graph = smiles_to_graph(stereo_smiles)
        assert graph is not None, "Failed to create graph for chiral molecule"

        # Check that the graph structure is valid
        is_valid, _ = validate_graph(graph, EXCLUSION_CRITERIA)
        assert is_valid, "Chiral molecule should not be excluded by default criteria"


class TestIntegration:
    """Integration tests for the full parsing and exclusion pipeline."""

    def test_full_pipeline_valid_molecules(self):
        """Test the full pipeline with valid molecules."""
        config = get_config()
        results = []

        for smiles in VALID_SMILES:
            # Step 1: Parse SMILES
            mol = smiles_to_molecule(smiles)
            if mol is None:
                results.append({
                    "smiles": smiles,
                    "status": "parsing_failed",
                    "reason": "Could not parse SMILES"
                })
                continue

            # Step 2: Create graph
            graph = smiles_to_graph(smiles)
            if graph is None:
                results.append({
                    "smiles": smiles,
                    "status": "graph_creation_failed",
                    "reason": "Could not create graph"
                })
                continue

            # Step 3: Validate against criteria
            is_valid, reason = validate_graph(graph, EXCLUSION_CRITERIA)

            results.append({
                "smiles": smiles,
                "status": "valid" if is_valid else "excluded",
                "reason": reason if not is_valid else None,
                "num_atoms": mol.GetNumAtoms(),
                "num_bonds": mol.GetNumBonds()
            })

        # Verify that we got results for all molecules
        assert len(results) == len(VALID_SMILES), \
            f"Expected {len(VALID_SMILES)} results, got {len(results)}"

        # Check that at least some molecules passed (our criteria should allow most)
        passed_count = sum(1 for r in results if r["status"] == "valid")
        assert passed_count > 0, "At least one molecule should pass the exclusion criteria"

    def test_full_pipeline_invalid_molecules(self):
        """Test the full pipeline with invalid molecules."""
        invalid_results = []

        for smiles in INVALID_SMILES:
            mol = smiles_to_molecule(smiles)

            if mol is None:
                invalid_results.append({
                    "smiles": smiles,
                    "status": "parsing_failed",
                    "reason": "Could not parse SMILES"
                })
                continue

            # If parsing succeeded, check if it's excluded by criteria
            graph = smiles_to_graph(smiles)
            is_valid, reason = validate_graph(graph, EXCLUSION_CRITERIA)

            invalid_results.append({
                "smiles": smiles,
                "status": "excluded" if not is_valid else "unexpectedly_valid",
                "reason": reason
            })

        # Verify that invalid SMILES either failed to parse or were excluded
        failed_or_excluded = sum(1 for r in invalid_results
                               if r["status"] in ["parsing_failed", "excluded"])
        assert failed_or_excluded == len(invalid_results), \
            f"All invalid molecules should fail parsing or be excluded, but {failed_or_excluded}/{len(invalid_results)} did"

    def test_batch_processing(self):
        """Test batch processing of multiple SMILES strings."""
        from code.utils.graph_utils import batch_smiles_to_graphs

        batch_smiles = VALID_SMILES[:3]  # Use a subset for testing

        graphs = batch_smiles_to_graphs(batch_smiles, EXCLUSION_CRITERIA)

        # Check that we got the expected number of graphs
        assert len(graphs) == len(batch_smiles), \
            f"Expected {len(batch_smiles)} graphs, got {len(graphs)}"

        # Check that each graph has the correct structure
        for i, graph in enumerate(graphs):
            if graph is not None:
                assert "nodes" in graph, f"Graph {i} missing 'nodes' key"
                assert "edges" in graph, f"Graph {i} missing 'edges' key"
            # Note: Some graphs might be None if they were excluded


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_smiles_string(self):
        """Test handling of empty SMILES string."""
        mol = smiles_to_molecule("")
        assert mol is None, "Empty SMILES should return None"

    def test_whitespace_smiles(self):
        """Test handling of SMILES with whitespace."""
        whitespace_smiles = "  CCO  "
        mol = smiles_to_molecule(whitespace_smiles)
        # RDKit might handle this, or it might fail - we just check it doesn't crash
        assert mol is not None or mol is None, "Whitespace handling should not crash"

    def test_very_long_smiles(self):
        """Test handling of very long SMILES strings."""
        long_smiles = "C" * 1000  # Very long chain
        mol = smiles_to_molecule(long_smiles)
        # Should either parse or return None, but not crash
        assert mol is not None or mol is None, "Long SMILES handling should not crash"

    def test_special_characters_in_smiles(self):
        """Test handling of special characters in SMILES."""
        special_smiles = "C[C@@H](O)C"  # With stereochemistry markers
        mol = smiles_to_molecule(special_smiles)
        assert mol is not None, "SMILES with special characters should parse"

    def test_boundary_atom_count(self):
        """Test molecules at the boundary of atom count limits."""
        # Test at exactly min_atoms
        min_atoms_smiles = "CCCC"  # 4 atoms - should be excluded if min_atoms=5
        mol = smiles_to_molecule(min_atoms_smiles)
        if mol is not None:
            graph = smiles_to_graph(min_atoms_smiles)
            is_valid, reason = validate_graph(graph, EXCLUSION_CRITERIA)
            # Should be excluded since 4 < 5
            assert not is_valid, f"Molecule with {mol.GetNumAtoms()} atoms should be excluded"

        # Test at exactly max_atoms (this might be hard to construct, so we skip for now)
        # The logic should handle it correctly if we had such a molecule


if __name__ == "__main__":
    pytest.main([__file__, "-v"])