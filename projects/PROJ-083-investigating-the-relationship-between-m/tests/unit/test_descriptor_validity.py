import pytest
from rdkit import Chem
from code.descriptors import TopologicalDescriptorCalculator, calculate_descriptors_for_smiles

class TestDescriptorValidity:
    """
    Tests for FR-002: Flagging 'invalid topology' for disconnected graphs.
    """

    def test_disconnected_graph_flagged(self):
        """
        Verify that a disconnected graph (two separate molecules in one string)
        is flagged as invalid topology and returns None for indices.
        """
        # Benzene and Ethanol separated by a dot -> disconnected
        smiles = "c1ccccc1.CCO" 
        
        result = calculate_descriptors_for_smiles(smiles)
        
        assert result['is_valid_topology'] is False
        assert result['wiener'] is None
        assert result['balaban'] is None
        assert result['zagreb'] is None
        assert 'Disconnected' in result['reason'] or 'Failed' in result['reason']

    def test_valid_connected_graph(self):
        """
        Verify that a valid connected molecule (Benzene) returns values.
        """
        smiles = "c1ccccc1"
        
        result = calculate_descriptors_for_smiles(smiles)
        
        assert result['is_valid_topology'] is True
        assert result['wiener'] is not None
        assert result['balaban'] is not None
        assert result['zagreb'] is not None
        assert result['reason'] is None

    def test_empty_molecule_flagged(self):
        """
        Verify that an empty or invalid SMILES is flagged.
        """
        result = calculate_descriptors_for_smiles("")
        assert result['is_valid_topology'] is False
        
        result = calculate_descriptors_for_smiles("invalid_smiles_xyz")
        assert result['is_valid_topology'] is False

    def test_calculator_class_method(self):
        """
        Test the class method directly with an RDKit Mol object.
        """
        mol = Chem.MolFromSmiles("c1ccccc1.CCO")
        calculator = TopologicalDescriptorCalculator()
        
        result = calculator.calculate_descriptors(mol)
        
        assert result['is_valid_topology'] is False
        assert result['wiener'] is None