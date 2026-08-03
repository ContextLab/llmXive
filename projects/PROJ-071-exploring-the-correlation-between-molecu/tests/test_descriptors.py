import pytest
import pandas as pd
from pathlib import Path
import json

from code.descriptors import (
    validate_molecule,
    calculate_tpsa,
    calculate_rotatable_bonds,
    calculate_mw,
    calculate_aromatic_rings,
    calculate_wiener_index,
    calculate_zagreb_index,
    calculate_descriptors_for_molecule,
    log_error_to_file,
    AtomValenceException
)
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

# Reference molecules with known descriptor values
REFERENCE_MOLECULES = {
    "aspirin": {
        "smiles": "CC(=O)Occcccc1C(=O)O",
        "mw": 180.16,
        "tpsa": 63.60,
        "rotatable_bonds": 3,
        "aromatic_rings": 1,
        "wiener_index": 23.0,
        "zagreb_index": 12.0
    },
    "caffeine": {
        "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
        "mw": 194.19,
        "tpsa": 58.44,
        "rotatable_bonds": 0,
        "aromatic_rings": 1,
        "wiener_index": 19.0,
        "zagreb_index": 16.0
    },
    "diazepam": {
        "smiles": "CN1C(=O)C=C(C2=CC=CC=C2Cl)N1C",
        "mw": 284.75,
        "tpsa": 32.68,
        "rotatable_bonds": 1,
        "aromatic_rings": 2,
        "wiener_index": 31.0,
        "zagreb_index": 20.0
    }
}

@pytest.fixture
def temp_excluded_file(tmp_path):
    """Create a temporary file for excluded molecules."""
    return tmp_path / "excluded_molecules.csv"

def test_validate_molecule_valid():
    """Test validation of valid SMILES."""
    mol = validate_molecule("CCO")
    assert mol is not None
    assert isinstance(mol, Chem.Mol)

def test_validate_molecule_invalid():
    """Test validation of invalid SMILES."""
    mol = validate_molecule("invalid_smiles")
    assert mol is None

def test_calculate_tpsa():
    """Test TPSA calculation."""
    mol = Chem.MolFromSmiles("CCO")
    tpsa = calculate_tpsa(mol)
    assert abs(tpsa - 20.23) < 0.01  # Ethanol TPSA

def test_calculate_rotatable_bonds():
    """Test rotatable bonds calculation."""
    mol = Chem.MolFromSmiles("CCCCC")
    rot_bonds = calculate_rotatable_bonds(mol)
    assert rot_bonds == 3  # Pentane has 3 rotatable bonds

def test_calculate_mw():
    """Test molecular weight calculation."""
    mol = Chem.MolFromSmiles("CCO")
    mw = calculate_mw(mol)
    assert abs(mw - 46.07) < 0.01  # Ethanol MW

def test_calculate_aromatic_rings():
    """Test aromatic rings calculation."""
    mol = Chem.MolFromSmiles("c1ccccc1")
    rings = calculate_aromatic_rings(mol)
    assert rings == 1

def test_calculate_wiener_index():
    """Test Wiener index calculation."""
    mol = Chem.MolFromSmiles("CCCC")
    wiener = calculate_wiener_index(mol)
    assert abs(wiener - 6.0) < 0.01  # Butane Wiener index

def test_calculate_zagreb_index():
    """Test Zagreb index calculation."""
    mol = Chem.MolFromSmiles("CC")
    zagreb = calculate_zagreb_index(mol)
    assert abs(zagreb - 2.0) < 0.01  # Ethane Zagreb index

def test_reference_molecules():
    """Test descriptors for reference molecules."""
    for name, ref in REFERENCE_MOLECULES.items():
        mol = Chem.MolFromSmiles(ref["smiles"])
        assert mol is not None, f"Failed to parse {name}"

        # MW
        mw = calculate_mw(mol)
        assert abs(mw - ref["mw"]) < 0.1, f"MW mismatch for {name}: {mw} vs {ref['mw']}"

        # TPSA
        tpsa = calculate_tpsa(mol)
        assert abs(tpsa - ref["tpsa"]) < 0.1, f"TPSA mismatch for {name}: {tpsa} vs {ref['tpsa']}"

        # Rotatable bonds
        rot = calculate_rotatable_bonds(mol)
        assert rot == ref["rotatable_bonds"], f"Rotatable bonds mismatch for {name}"

        # Aromatic rings
        rings = calculate_aromatic_rings(mol)
        assert rings == ref["aromatic_rings"], f"Aromatic rings mismatch for {name}"

def test_log_error_to_file(temp_excluded_file):
    """Test logging errors to file."""
    log_error_to_file(
        smiles="invalid_smiles",
        error_type="TestError",
        timestamp="2024-01-01T00:00:00",
        source_hash="test_hash",
        output_path=temp_excluded_file
    )

    assert temp_excluded_file.exists()
    df = pd.read_csv(temp_excluded_file)
    assert len(df) == 1
    assert df.iloc[0]["smiles"] == "invalid_smiles"
    assert df.iloc[0]["error_type"] == "TestError"

def test_descriptors_for_molecule_success():
    """Test descriptor calculation for a successful molecule."""
    mol = Chem.MolFromSmiles("CCO")
    result = calculate_descriptors_for_molecule(mol, "CCO", "hash", Path("/tmp/test.csv"))
    assert result["status"] == "success"
    assert "tpsa" in result
    assert "mw" in result

def test_descriptors_for_molecule_valence_error(temp_excluded_file):
    """Test descriptor calculation with a valence error."""
    # Create a molecule with valence error (e.g., carbon with 5 bonds)
    # This is hard to construct manually, so we simulate the exception
    from unittest.mock import patch
    
    with patch('code.descriptors.CalcNumAromaticRings', side_effect=AtomValenceException("Valence error")):
        mol = Chem.MolFromSmiles("CCO")
        result = calculate_descriptors_for_molecule(mol, "CCO", "hash", temp_excluded_file)
        assert result["status"] == "failed"
        assert result["error_type"] == "AtomValenceException"
        
        # Check that it was logged
        assert temp_excluded_file.exists()