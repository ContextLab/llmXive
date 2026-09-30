import pytest
from rdkit import Chem
from code.descriptors import TopologicalDescriptorCalculator, calculate_descriptors_for_smiles, is_connected

class TestDisconnectedGraphHandling:
    """
    Tests for T023: Logic to flag "invalid topology" for disconnected graphs.
    """

    def test_is_connected_true(self):
        """Test that connected molecules return True."""
        benzene = Chem.MolFromSmiles("c1ccccc1")
        assert is_connected(benzene) is True
        
        ethane = Chem.MolFromSmiles("CC")
        assert is_connected(ethane) is True

    def test_is_connected_false(self):
        """Test that disconnected molecules return False."""
        # Two separate benzene rings without a bond
        disconnected = Chem.MolFromSmiles("c1ccccc1.c2ccccc2")
        assert is_connected(disconnected) is False
        
        # Methane and Ethane separate
        disconnected2 = Chem.MolFromSmiles("C.CC")
        assert is_connected(disconnected2) is False

    def test_calculate_wiener_disconnected(self):
        """Test that Wiener index returns None for disconnected graphs."""
        calculator = TopologicalDescriptorCalculator()
        disconnected = Chem.MolFromSmiles("c1ccccc1.c2ccccc2")
        
        result = calculator.calculate_wiener(disconnected)
        assert result is None

    def test_calculate_balaban_disconnected(self):
        """Test that Balaban index returns None for disconnected graphs."""
        calculator = TopologicalDescriptorCalculator()
        disconnected = Chem.MolFromSmiles("c1ccccc1.c2ccccc2")
        
        result = calculator.calculate_balaban(disconnected)
        assert result is None

    def test_calculate_zagreb_disconnected(self):
        """Test that Zagreb indices return None for disconnected graphs."""
        calculator = TopologicalDescriptorCalculator()
        disconnected = Chem.MolFromSmiles("c1ccccc1.c2ccccc2")
        
        result = calculator.calculate_zagreb(disconnected)
        assert result is None

    def test_calculate_descriptors_disconnected_flag(self):
        """Test that full descriptor calculation flags invalid topology."""
        calculator = TopologicalDescriptorCalculator()
        disconnected = Chem.MolFromSmiles("c1ccccc1.c2ccccc2")
        
        result = calculator.calculate_descriptors(disconnected, name="disconnected_test")
        
        assert result["valid_topology"] is False
        assert "Disconnected" in result.get("error", "")
        assert result["wiener"] is None
        assert result["balaban"] is None
        assert result["zagreb_m1"] is None
        assert result["zagreb_m2"] is None

    def test_calculate_descriptors_connected(self):
        """Test that valid molecules still calculate correctly."""
        calculator = TopologicalDescriptorCalculator()
        benzene = Chem.MolFromSmiles("c1ccccc1")
        
        result = calculator.calculate_descriptors(benzene, name="benzene")
        
        assert result["valid_topology"] is True
        assert result["wiener"] is not None
        assert result["balaban"] is not None
        assert result["zagreb_m1"] is not None
        assert result["zagreb_m2"] is not None

    def test_calculate_descriptors_for_smiles_disconnected(self):
        """Test the convenience function with disconnected SMILES."""
        result = calculate_descriptors_for_smiles("c1ccccc1.c2ccccc2", "test_disconnected")
        
        assert result["valid_topology"] is False
        assert result["error"] == "Disconnected graph (Invalid Topology)"

    def test_invalid_smiles_handling(self):
        """Test that invalid SMILES are handled gracefully."""
        result = calculate_descriptors_for_smiles("not_a_molecule", "bad")
        
        assert result["valid_topology"] is False
        assert result["error"] == "Invalid SMILES"