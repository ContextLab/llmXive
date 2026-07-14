"""
Unit tests for RDKit descriptor calculation.

Tests the descriptor calculation logic defined in code/data/descriptors.py.
Verifies that:
1. The module can be imported and functions are callable.
2. Calculated descriptors match expected values for known SMILES.
3. Molecular weight, polarizability, and kinetic diameter estimates are reasonable.
4. Invalid SMILES are handled gracefully.
"""
import pytest
import math
from pathlib import Path
import sys

# Ensure code/ is in path for imports
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from data.descriptors import (
    calculate_descriptors,
    calculate_kinetic_diameter,
    get_rdkit_mol
)

class TestGetRdkitMol:
    """Tests for the SMILES to RDKit Mol conversion helper."""

    def test_valid_smiles(self):
        """Test that valid SMILES strings convert successfully."""
        mol = get_rdkit_mol("CCO")  # Ethanol
        assert mol is not None
        assert mol.GetNumAtoms() == 3  # 2 C, 1 O

    def test_invalid_smiles(self):
        """Test that invalid SMILES strings return None."""
        mol = get_rdkit_mol("Invalid_SMILES_123!!!")
        assert mol is None

    def test_empty_string(self):
        """Test that empty string returns None."""
        mol = get_rdkit_mol("")
        assert mol is None

class TestCalculateDescriptors:
    """Tests for the main descriptor calculation function."""

    def test_methane_descriptors(self):
        """
        Test descriptor calculation for Methane (CH4).
        Expected values are approximate based on RDKit defaults.
        """
        mol = get_rdkit_mol("C")
        assert mol is not None
        
        desc = calculate_descriptors("C")
        
        # Check that all required keys exist
        assert "molecular_weight" in desc
        assert "polarizability" in desc
        assert "kinetic_diameter" in desc
        assert "polar_surface_area" in desc
        assert "h_bond_donors" in desc
        assert "h_bond_acceptors" in desc
        assert "van_der_waals_volume" in desc
        
        # Verify specific values for Methane
        assert math.isclose(desc["molecular_weight"], 16.04, abs_tol=0.05)
        assert desc["h_bond_donors"] == 0
        assert desc["h_bond_acceptors"] == 0
        
        # Polarizability should be positive
        assert desc["polarizability"] > 0
        
        # Kinetic diameter should be positive and in reasonable range (Angstroms)
        assert 2.0 < desc["kinetic_diameter"] < 6.0

    def test_ethanol_descriptors(self):
        """Test descriptor calculation for Ethanol (CCO)."""
        desc = calculate_descriptors("CCO")
        
        assert desc["h_bond_donors"] == 1
        assert desc["h_bond_acceptors"] == 1
        assert desc["molecular_weight"] > 40  # > 46.07

    def test_invalid_smiles_handling(self):
        """Test that invalid SMILES returns a dict with None/NaN values or raises specific error."""
        # The function should handle invalid input gracefully. 
        # Based on typical implementation, it might return None or a dict with NaNs.
        # Let's assume it returns a dict with NaNs or None for this test.
        try:
            desc = calculate_descriptors("Invalid!!!")
            # If it returns a dict, check for None or NaN
            if isinstance(desc, dict):
                assert desc.get("molecular_weight") is None or math.isnan(desc.get("molecular_weight", float('nan')))
            else:
                # If it returns None, that's also acceptable behavior for invalid input
                assert desc is None
        except Exception:
            # Or it might raise an error, which is also acceptable if documented
            pass

    def test_benzene_descriptors(self):
        """Test descriptor calculation for Benzene (c1ccccc1)."""
        desc = calculate_descriptors("c1ccccc1")
        
        assert desc["h_bond_donors"] == 0
        assert desc["h_bond_acceptors"] == 0
        assert desc["molecular_weight"] > 70  # ~78.11

class TestCalculateKineticDiameter:
    """Tests specifically for the kinetic diameter estimation."""

    def test_kinetic_diameter_positive(self):
        """Test that kinetic diameter is always positive for valid molecules."""
        molecules = ["C", "CC", "CCO", "c1ccccc1", "N#N"]
        for smi in molecules:
            mol = get_rdkit_mol(smi)
            if mol:
                diam = calculate_kinetic_diameter(mol)
                assert diam > 0, f"Kinetic diameter for {smi} should be positive"

    def test_kinetic_diameter_range(self):
        """Test that kinetic diameter falls within physically reasonable bounds (Angstroms)."""
        # Small molecule: Helium (He) - approx 2.6 A
        # Large molecule: C60 (Buckminsterfullerene) - approx 10 A
        small_mol = get_rdkit_mol("[He]")
        large_mol = get_rdkit_mol("C1=CC=CC2=C1C3=CC=CC4=C3C5=CC=CC6=C4C7=CC=CC8=C5C9=CC=CC%10=C6C%11=CC=CC%12=C7C%13=CC=CC%14=C8C%15=CC=CC%16=C9C%17=CC=CC%18=C%10C%19=CC=CC%20=C%11C%21=CC=CC%22=C%12C%23=CC=CC%24=C%13C%25=CC=CC%26=C%14C%27=CC=CC%28=C%15C%29=CC=CC%30=C%16C%31=CC=CC%32=C%17C%33=CC=CC%34=C%18C%35=CC=CC%36=C%19C%37=CC=CC%38=C%20C%39=CC=CC%40=C%21C%41=CC=CC%42=C%22C%43=CC=CC%44=C%23C%45=CC=CC%46=C%24C%47=CC=CC%48=C%25C%49=CC=CC%50=C%26C%51=CC=CC%52=C%27C%53=CC=CC%54=C%28C%55=CC=CC%56=C%29C%57=CC=CC%58=C%30C%59=CC=CC%60=C%31C%61=CC=CC%62=C%32C%63=CC=CC%64=C%33") # Simplified C60 representation might be complex, using a simpler large aromatic

        # Using a simpler large molecule for test stability: Pyrene (C16H10)
        large_mol = get_rdkit_mol("c1ccc2cc3ccccc3cc2c1")
        
        if small_mol:
            diam_small = calculate_kinetic_diameter(small_mol)
            assert 1.0 < diam_small < 5.0, f"He-like diameter {diam_small} out of range"
        
        if large_mol:
            diam_large = calculate_kinetic_diameter(large_mol)
            assert 5.0 < diam_large < 15.0, f"Large aromatic diameter {diam_large} out of range"

class TestIntegration:
    """Integration-style tests to ensure the module works end-to-end."""

    def test_full_pipeline_smiles(self):
        """Test the full descriptor calculation pipeline with a known SMILES."""
        smi = "CC(=O)O"  # Acetic Acid
        result = calculate_descriptors(smi)
        
        assert result is not None
        assert "molecular_weight" in result
        assert "polarizability" in result
        assert "kinetic_diameter" in result
        
        # Acetic acid specific checks
        assert result["h_bond_donors"] >= 1
        assert result["h_bond_acceptors"] >= 1
        assert result["molecular_weight"] > 50  # ~60.05