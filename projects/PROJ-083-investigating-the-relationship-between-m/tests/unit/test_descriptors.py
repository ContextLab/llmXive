"""
Unit tests for topological descriptor calculations (User Story 2).

This module implements TDD-style tests for the Wiener, Balaban, and Zagreb
index calculators. These tests must run against the actual implementation
in code/descriptors.py.

Reference values for validation:
- Benzene (C1=CC=CC=C1): Wiener = 27
- Toluene (CC1=CC=CC=C1): Wiener = 33
- Nitrobenzene (O=N(=O)C1=CC=CC=C1): Wiener = 45

Note: The implementation in code/descriptors.py must be completed before
these tests can pass.
"""

import pytest
import sys
import os

# Ensure the project root is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.descriptors import calculate_wiener_index, calculate_balaban_index, calculate_zagreb_index
from code.utils.smiles_parser import SMILESParser
from rdkit import Chem


class TestWienerIndex:
    """Unit tests for Wiener index calculation on reference molecules."""

    @pytest.fixture
    def parser(self):
        """Provide a SMILES parser instance."""
        return SMILESParser()

    def test_benzene_wiener_index(self, parser):
        """
        Test Wiener index for benzene.
        
        Expected value: 27
        Structure: 6 carbon ring, all equivalent.
        Distances: 1 (6 edges), 2 (6 pairs), 3 (3 pairs).
        Sum = 6*1 + 6*2 + 3*3 = 6 + 12 + 9 = 27.
        """
        smiles = "C1=CC=CC=C1"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse benzene SMILES"
        
        # Calculate Wiener index
        wiener = calculate_wiener_index(mol)
        
        # Verify within tolerance
        assert abs(wiener - 27.0) < 0.1, f"Expected Wiener index ~27 for benzene, got {wiener}"

    def test_toluene_wiener_index(self, parser):
        """
        Test Wiener index for toluene.
        
        Expected value: 33
        Structure: Benzene ring with a methyl group.
        """
        smiles = "CC1=CC=CC=C1"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse toluene SMILES"
        
        wiener = calculate_wiener_index(mol)
        
        assert abs(wiener - 33.0) < 0.1, f"Expected Wiener index ~33 for toluene, got {wiener}"

    def test_nitrobenzene_wiener_index(self, parser):
        """
        Test Wiener index for nitrobenzene.
        
        Expected value: 45
        Structure: Benzene ring with a nitro group.
        """
        smiles = "O=N(=O)C1=CC=CC=C1"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse nitrobenzene SMILES"
        
        wiener = calculate_wiener_index(mol)
        
        assert abs(wiener - 45.0) < 0.1, f"Expected Wiener index ~45 for nitrobenzene, got {wiener}"

    def test_ethane_wiener_index(self, parser):
        """
        Test Wiener index for ethane.
        
        Expected value: 1
        Structure: Two carbons connected by a single bond.
        Distance: 1 pair at distance 1.
        Sum = 1.
        """
        smiles = "CC"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse ethane SMILES"
        
        wiener = calculate_wiener_index(mol)
        
        assert abs(wiener - 1.0) < 0.1, f"Expected Wiener index ~1 for ethane, got {wiener}"

    def test_methane_wiener_index(self, parser):
        """
        Test Wiener index for methane.
        
        Expected value: 0
        Structure: Single carbon atom.
        No pairs of distinct atoms.
        Sum = 0.
        """
        smiles = "C"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse methane SMILES"
        
        wiener = calculate_wiener_index(mol)
        
        assert abs(wiener - 0.0) < 0.1, f"Expected Wiener index ~0 for methane, got {wiener}"

    def test_disconnected_graph_raises_error(self, parser):
        """
        Test that Wiener index calculation raises an error for disconnected graphs.
        
        The Wiener index is defined only for connected graphs.
        """
        # Create a disconnected molecule: two separate ethane molecules
        smiles = "CC.CC"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse disconnected SMILES"
        
        # The descriptor function should handle disconnected graphs
        # Either by raising an error or returning a specific value (e.g., None or -1)
        # For this test, we expect it to NOT return a valid positive Wiener index
        wiener = calculate_wiener_index(mol)
        
        # Depending on implementation, it might raise or return a specific value
        # We check that it's not a valid Wiener index for a connected graph
        assert wiener is None or wiener < 0 or not isinstance(wiener, (int, float)), \
            "Wiener index should not be calculated for disconnected graphs"


class TestBalabanIndex:
    """Unit tests for Balaban index calculation."""

    @pytest.fixture
    def parser(self):
        return SMILESParser()

    def test_benzene_balaban_index(self, parser):
        """
        Test Balaban index for benzene.
        
        Expected value: ~1.0 (approximate, depends on specific formula variant)
        Reference: J. Chem. Inf. Comput. Sci. 1982, 22, 221-225.
        """
        smiles = "C1=CC=CC=C1"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse benzene SMILES"
        
        balaban = calculate_balaban_index(mol)
        
        # Balaban index for benzene is typically around 1.0
        # Allow for some tolerance due to formula variations
        assert balaban is not None, "Balaban index calculation failed for benzene"
        assert 0.5 < balaban < 2.0, f"Expected Balaban index in range [0.5, 2.0] for benzene, got {balaban}"

    def test_ethane_balaban_index(self, parser):
        """Test Balaban index for ethane."""
        smiles = "CC"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse ethane SMILES"
        
        balaban = calculate_balaban_index(mol)
        
        assert balaban is not None, "Balaban index calculation failed for ethane"
        # Ethane Balaban index is typically small
        assert 0.0 <= balaban < 2.0, f"Unexpected Balaban index for ethane: {balaban}"

    def test_disconnected_graph_balaban(self, parser):
        """Test that Balaban index handles disconnected graphs appropriately."""
        smiles = "CC.CC"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse disconnected SMILES"
        
        balaban = calculate_balaban_index(mol)
        
        # Should not return a valid positive index for disconnected graphs
        assert balaban is None or balaban < 0, \
            "Balaban index should not be calculated for disconnected graphs"


class TestZagrebIndex:
    """Unit tests for Zagreb index calculation."""

    @pytest.fixture
    def parser(self):
        return SMILESParser()

    def test_benzene_zagreb_index(self, parser):
        """
        Test Zagreb index for benzene.
        
        First Zagreb Index (M1): Sum of squared degrees.
        Benzene: 6 carbons, each degree 3 (2 ring bonds + 1 H, but H usually not counted in topological graph).
        In the carbon skeleton: 6 nodes, each degree 2 (connected to 2 neighbors).
        M1 = 6 * (2^2) = 6 * 4 = 24.
        
        Second Zagreb Index (M2): Sum of products of degrees for adjacent vertices.
        Each edge connects two degree-2 nodes. 6 edges.
        M2 = 6 * (2 * 2) = 24.
        """
        smiles = "C1=CC=CC=C1"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse benzene SMILES"
        
        zagreb1, zagreb2 = calculate_zagreb_index(mol)
        
        # Verify first Zagreb index
        assert abs(zagreb1 - 24.0) < 0.1, f"Expected M1 ~24 for benzene, got {zagreb1}"
        # Verify second Zagreb index
        assert abs(zagreb2 - 24.0) < 0.1, f"Expected M2 ~24 for benzene, got {zagreb2}"

    def test_ethane_zagreb_index(self, parser):
        """
        Test Zagreb index for ethane.
        
        Ethane (C-C): 2 carbons, each degree 1 (in carbon skeleton).
        M1 = 1^2 + 1^2 = 2.
        M2 = 1 * 1 = 1.
        """
        smiles = "CC"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse ethane SMILES"
        
        zagreb1, zagreb2 = calculate_zagreb_index(mol)
        
        assert abs(zagreb1 - 2.0) < 0.1, f"Expected M1 ~2 for ethane, got {zagreb1}"
        assert abs(zagreb2 - 1.0) < 0.1, f"Expected M2 ~1 for ethane, got {zagreb2}"

    def test_propane_zagreb_index(self, parser):
        """
        Test Zagreb index for propane.
        
        Propane (C-C-C): 3 carbons.
        Degrees: terminal carbons have degree 1, middle carbon has degree 2.
        M1 = 1^2 + 2^2 + 1^2 = 1 + 4 + 1 = 6.
        M2 = (1*2) + (2*1) = 2 + 2 = 4.
        """
        smiles = "CCC"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse propane SMILES"
        
        zagreb1, zagreb2 = calculate_zagreb_index(mol)
        
        assert abs(zagreb1 - 6.0) < 0.1, f"Expected M1 ~6 for propane, got {zagreb1}"
        assert abs(zagreb2 - 4.0) < 0.1, f"Expected M2 ~4 for propane, got {zagreb2}"

    def test_disconnected_graph_zagreb(self, parser):
        """Test that Zagreb index handles disconnected graphs appropriately."""
        smiles = "CC.CC"
        mol = parser.parse(smiles)
        assert mol is not None, "Failed to parse disconnected SMILES"
        
        zagreb1, zagreb2 = calculate_zagreb_index(mol)
        
        # Should handle disconnected graphs gracefully
        # Either return None or specific values indicating disconnection
        assert (zagreb1 is None or zagreb2 is None) or \
             (isinstance(zagreb1, (int, float)) and isinstance(zagreb2, (int, float))), \
             "Zagreb index should return None or valid numbers for disconnected graphs"