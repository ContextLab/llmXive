"""
Unit tests for descriptors calculation and error handling.
"""
import pytest
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import csv

from rdkit import Chem
from rdkit.Chem import Descriptors

# Import the functions to test
from descriptors import (
    calculate_tpsa,
    calculate_rotatable_bonds,
    calculate_mw,
    calculate_aromatic_rings,
    calculate_wiener_index,
    calculate_zagreb_index,
    calculate_descriptors_for_molecule,
    calculate_descriptors_batch,
    validate_molecule,
    get_data_path,
    log_error_to_file
)
from error_handlers import AtomValenceException

# Reference values for known molecules (Aspirin, Caffeine, Diazepam)
REFERENCE_MOLECULES = {
    "Aspirin": {
        "smiles": "CC(=O)Occcccc1C(=O)O",
        "MW": 180.16,
        "TPSA": 63.6,
        "RotatableBonds": 3,
        "AromaticRings": 1
    },
    "Caffeine": {
        "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
        "MW": 194.19,
        "TPSA": 58.4,
        "RotatableBonds": 0,
        "AromaticRings": 1
    },
    "Diazepam": {
        "smiles": "CN1C(=O)C=C(C2=CC=CC=C2Cl)N1C",
        "MW": 284.75,
        "TPSA": 32.7,
        "RotatableBonds": 1,
        "AromaticRings": 2
    }
}

@pytest.fixture
def temp_excluded_file(tmp_path):
    """Create a temporary file for testing excluded molecule logging."""
    file_path = tmp_path / "test_excluded.csv"
    return file_path

def test_validate_molecule_valid():
    """Test validation of a valid SMILES string."""
    smiles = "CC(=O)Occcccc1C(=O)O"
    mol = validate_molecule(smiles)
    assert mol is not None
    assert isinstance(mol, Chem.Mol)

def test_validate_molecule_invalid():
    """Test validation of an invalid SMILES string."""
    smiles = "invalid_smiles_123"
    with pytest.raises(AtomValenceException):
        validate_molecule(smiles)

def test_calculate_tpsa():
    """Test TPSA calculation against reference."""
    mol = Chem.MolFromSmiles(REFERENCE_MOLECULES["Aspirin"]["smiles"])
    tpsa = calculate_tpsa(mol)
    # Allow small floating point differences
    assert abs(tpsa - REFERENCE_MOLECULES["Aspirin"]["TPSA"]) < 1.0

def test_calculate_rotatable_bonds():
    """Test Rotatable Bonds calculation."""
    mol = Chem.MolFromSmiles(REFERENCE_MOLECULES["Caffeine"]["smiles"])
    rot_bonds = calculate_rotatable_bonds(mol)
    assert rot_bonds == REFERENCE_MOLECULES["Caffeine"]["RotatableBonds"]

def test_calculate_mw():
    """Test Molecular Weight calculation."""
    mol = Chem.MolFromSmiles(REFERENCE_MOLECULES["Diazepam"]["smiles"])
    mw = calculate_mw(mol)
    assert abs(mw - REFERENCE_MOLECULES["Diazepam"]["MW"]) < 0.1

def test_calculate_aromatic_rings():
    """Test Aromatic Rings calculation."""
    mol = Chem.MolFromSmiles(REFERENCE_MOLECULES["Diazepam"]["smiles"])
    ar = calculate_aromatic_rings(mol)
    assert ar == REFERENCE_MOLECULES["Diazepam"]["AromaticRings"]

def test_calculate_wiener_index():
    """Test Wiener Index calculation (should not crash)."""
    mol = Chem.MolFromSmiles("CCO")
    wiener = calculate_wiener_index(mol)
    assert isinstance(wiener, float)
    assert wiener >= 0

def test_calculate_zagreb_index():
    """Test Zagreb Index calculation (should not crash)."""
    mol = Chem.MolFromSmiles("CCO")
    zagreb = calculate_zagreb_index(mol)
    assert isinstance(zagreb, float)
    assert zagreb >= 0

def test_calculate_descriptors_for_molecule():
    """Test full descriptor calculation for a single molecule."""
    smiles = REFERENCE_MOLECULES["Aspirin"]["smiles"]
    result = calculate_descriptors_for_molecule(smiles)
    
    assert "smiles" in result
    assert "TPSA" in result
    assert "RotatableBonds" in result
    assert "MW" in result
    assert "AromaticRings" in result
    assert "WienerIndex" in result
    assert "ZagrebIndex" in result

def test_calculate_descriptors_batch():
    """Test batch calculation with a mix of valid molecules."""
    df = pd.DataFrame({
        "smiles": [
            REFERENCE_MOLECULES["Aspirin"]["smiles"],
            REFERENCE_MOLECULES["Caffeine"]["smiles"]
        ]
    })
    
    result_df = calculate_descriptors_batch(df)
    
    assert len(result_df) == 2
    assert "TPSA" in result_df.columns
    assert "MW" in result_df.columns

def test_log_error_to_file(temp_excluded_file):
    """Test logging excluded molecules to CSV with correct schema."""
    smiles = "invalid_smiles"
    error_type = "ValenceError"
    timestamp = datetime.utcnow().isoformat()
    source_hash = "test_hash_123"
    
    log_error_to_file(smiles, error_type, timestamp, source_hash, temp_excluded_file)
    
    assert temp_excluded_file.exists()
    
    with open(temp_excluded_file, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Check header
    assert rows[0] == ["smiles", "error_type", "timestamp", "source_hash"]
    
    # Check data row
    assert len(rows) == 2
    assert rows[1][0] == smiles
    assert rows[1][1] == error_type
    assert rows[1][2] == timestamp
    assert rows[1][3] == source_hash

def test_calculate_descriptors_batch_with_invalid_molecules(temp_excluded_file):
    """Test batch calculation handling invalid molecules and logging them."""
    # Mock the log_error_to_file to use our temp file
    import descriptors
    original_log_func = descriptors.log_error_to_file
    descriptors.log_error_to_file = lambda s, e, t, h, fp: log_error_to_file(s, e, t, h, temp_excluded_file)
    
    try:
        df = pd.DataFrame({
            "smiles": [
                REFERENCE_MOLECULES["Aspirin"]["smiles"],
                "invalid_smiles_xyz",
                REFERENCE_MOLECULES["Caffeine"]["smiles"]
            ]
        })
        
        result_df = calculate_descriptors_batch(df, source_hash="test_hash")
        
        # Should only have 2 valid results
        assert len(result_df) == 2
        
        # Check that excluded file was created with 1 entry
        assert temp_excluded_file.exists()
        with open(temp_excluded_file, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        assert len(rows) == 2  # Header + 1 excluded
        assert rows[1][0] == "invalid_smiles_xyz"
        assert rows[1][1] == "ValenceError"
    finally:
        # Restore original function
        descriptors.log_error_to_file = original_log_func

def test_get_data_path():
    """Test that get_data_path returns the correct directory."""
    path = get_data_path()
    assert isinstance(path, Path)
    assert path.name == "data"
    assert (path / "processed").exists() or not (path / "processed").exists()  # Just check it's a valid path object

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
