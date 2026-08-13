"""
Unit tests for confound analysis functionality.

Tests for code/confound_analysis.py (Task T011b)
"""
import csv
import os
import tempfile
from pathlib import Path
import pytest

try:
    from rdkit import Chem
except ImportError:
    pytest.skip("RDKit not installed", allow_module_level=True)

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
from confound_analysis import (
    parse_functional_groups,
    calculate_molecular_properties,
    process_molecule,
    FUNCTIONAL_GROUPS
)

class TestFunctionalGroupDetection:
    """Test functional group detection using SMARTS patterns."""

    def test_amide_detection(self):
        """Test detection of amide functional group."""
        smiles = "CC(=O)N"  # Acetamide
        mol = Chem.MolFromSmiles(smiles)
        groups = parse_functional_groups(mol)
        assert "amide" in groups

    def test_aromatic_detection(self):
        """Test detection of aromatic rings."""
        smiles = "c1ccccc1"  # Benzene
        mol = Chem.MolFromSmiles(smiles)
        groups = parse_functional_groups(mol)
        assert "aromatic" in groups

    def test_alcohol_detection(self):
        """Test detection of alcohol functional group."""
        smiles = "CCO"  # Ethanol
        mol = Chem.MolFromSmiles(smiles)
        groups = parse_functional_groups(mol)
        assert "alcohol" in groups

    def test_carboxylic_acid_detection(self):
        """Test detection of carboxylic acid."""
        smiles = "CC(=O)O"  # Acetic acid
        mol = Chem.MolFromSmiles(smiles)
        groups = parse_functional_groups(mol)
        assert "carboxylic_acid" in groups

    def test_multiple_groups(self):
        """Test detection of multiple functional groups."""
        smiles = "NC(=O)c1ccccc1"  # Benzamide (amide + aromatic)
        mol = Chem.MolFromSmiles(smiles)
        groups = parse_functional_groups(mol)
        assert "amide" in groups
        assert "aromatic" in groups

    def test_no_groups(self):
        """Test molecule with no standard functional groups."""
        smiles = "CCCC"  # Butane
        mol = Chem.MolFromSmiles(smiles)
        groups = parse_functional_groups(mol)
        # Butane should have no special groups
        assert len(groups) == 0

    def test_invalid_molecule(self):
        """Test handling of invalid molecule."""
        groups = parse_functional_groups(None)
        assert groups == set()

class TestMolecularProperties:
    """Test molecular property calculations."""

    def test_molecular_weight_water(self):
        """Test molecular weight calculation for water."""
        mol = Chem.MolFromSmiles("O")
        props = calculate_molecular_properties(mol)
        # Water: H2O = 2*1.008 + 15.999 ≈ 18.015
        assert 17.9 < props['mw'] < 18.2

    def test_atom_count_water(self):
        """Test atom count for water."""
        mol = Chem.MolFromSmiles("O")
        props = calculate_molecular_properties(mol)
        assert props['atom_count'] == 3

    def test_molecular_weight_benzene(self):
        """Test molecular weight for benzene."""
        mol = Chem.MolFromSmiles("c1ccccc1")
        props = calculate_molecular_properties(mol)
        # Benzene: C6H6 = 6*12.01 + 6*1.008 ≈ 78.11
        assert 77.0 < props['mw'] < 79.0

    def test_atom_count_benzene(self):
        """Test atom count for benzene."""
        mol = Chem.MolFromSmiles("c1ccccc1")
        props = calculate_molecular_properties(mol)
        assert props['atom_count'] == 12

    def test_invalid_molecule_properties(self):
        """Test property calculation for invalid molecule."""
        props = calculate_molecular_properties(None)
        assert props['mw'] == 0.0
        assert props['atom_count'] == 0

class TestProcessMolecule:
    """Test complete molecule processing."""

    def test_valid_molecule(self):
        """Test processing of a valid molecule."""
        result = process_molecule("CCO", "test_001")
        assert result is not None
        assert result['molecule_id'] == "test_001"
        assert result['mw'] > 0
        assert result['atom_count'] > 0
        assert 'alcohol' in result['functional_groups']

    def test_invalid_smiles(self):
        """Test processing of invalid SMILES."""
        result = process_molecule("invalid_smiles", "test_002")
        assert result is None

    def test_functional_groups_format(self):
        """Test that functional groups are pipe-separated."""
        result = process_molecule("NC(=O)c1ccccc1", "test_003")
        assert result is not None
        groups_str = result['functional_groups']
        # Should be pipe-separated or empty
        if groups_str:
            assert "|" in groups_str or not any(g in groups_str for g in FUNCTIONAL_GROUPS if FUNCTIONAL_GROUPS[g].count('|') > 0)
        # Check that if multiple groups exist, they are sorted
        if "|" in groups_str:
            groups_list = groups_str.split("|")
            assert groups_list == sorted(groups_list)

class TestFunctionalGroupPatterns:
    """Test that all defined functional group patterns are valid SMARTS."""

    def test_all_patterns_valid(self):
        """Verify all functional group patterns compile as valid SMARTS."""
        for group_name, smarts in FUNCTIONAL_GROUPS.items():
            try:
                pattern = Chem.MolFromSmarts(smarts)
                assert pattern is not None, f"Invalid SMARTS for {group_name}: {smarts}"
            except Exception as e:
                pytest.fail(f"Failed to parse SMARTS for {group_name}: {smarts} - {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])