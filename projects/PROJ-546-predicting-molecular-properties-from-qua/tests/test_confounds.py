"""
Unit tests for code/confounds.py (T011)
"""
import pytest
import csv
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from confounds import (
    load_molecules_from_csv,
    parse_functional_groups,
    calculate_molecular_properties,
    process_molecule,
    write_confounds_csv,
    verify_distribution_stats
)
from rdkit import Chem

@pytest.fixture
def temp_csv(tmp_path):
    """Creates a temporary CSV file with valid SMILES."""
    csv_file = tmp_path / "test_data.csv"
    content = """molecule_id,SMILES
    mol_1,CCO
    mol_2,CC(=O)O
    mol_3,c1ccccc1"""
    csv_file.write_text(content)
    return csv_file

@pytest.fixture
def temp_output_csv(tmp_path):
    """Creates a temporary path for output CSV."""
    return tmp_path / "output.csv"

@pytest.fixture
def temp_log_file(tmp_path):
    """Creates a temporary path for log file."""
    return tmp_path / "verification.log"

def test_load_molecules_from_csv(temp_csv):
    """Test loading molecules from a CSV file."""
    data = load_molecules_from_csv(temp_csv)
    assert len(data) == 3
    assert data[0]['molecule_id'] == 'mol_1'
    assert data[0]['smiles'] == 'CCO'
    assert data[1]['smiles'] == 'CC(=O)O'
    assert data[2]['smiles'] == 'c1ccccc1'

def test_load_molecules_from_csv_missing_file(tmp_path):
    """Test that FileNotFoundError is raised if file is missing."""
    with pytest.raises(FileNotFoundError):
        load_molecules_from_csv(tmp_path / "non_existent.csv")

def test_parse_functional_groups_alcohol():
    """Test detection of alcohol group."""
    mol = Chem.MolFromSmiles("CCO")
    groups = parse_functional_groups(mol)
    assert "Alcohol" in groups

def test_parse_functional_groups_acid():
    """Test detection of carboxylic acid group."""
    mol = Chem.MolFromSmiles("CC(=O)O")
    groups = parse_functional_groups(mol)
    assert "CarboxylicAcid" in groups

def test_parse_functional_groups_aromatic():
    """Test detection of aromatic group."""
    mol = Chem.MolFromSmiles("c1ccccc1")
    groups = parse_functional_groups(mol)
    assert "Aromatic" in groups

def test_calculate_molecular_properties():
    """Test calculation of MW and atom count."""
    mol = Chem.MolFromSmiles("CCO") # Ethanol: C2H6O
    # MW ~ 46.07, Atoms = 2+6+1 = 9
    props = calculate_molecular_properties(mol)
    assert props['atom_count'] == 9
    assert 45.0 < props['mw'] < 47.0

def test_process_molecule_invalid_smiles():
    """Test that process_molecule returns None for invalid SMILES."""
    res = process_molecule({'molecule_id': 'bad', 'smiles': 'invalid_smiles'})
    assert res is None

def test_write_confounds_csv(temp_output_csv):
    """Test writing results to CSV."""
    results = [
        {'molecule_id': 'm1', 'mw': 46.0, 'atom_count': 9, 'functional_groups': 'Alcohol'},
        {'molecule_id': 'm2', 'mw': 60.0, 'atom_count': 10, 'functional_groups': 'CarboxylicAcid'}
    ]
    write_confounds_csv(results, temp_output_csv)
    
    assert temp_output_csv.exists()
    with open(temp_output_csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]['molecule_id'] == 'm1'
        assert rows[0]['functional_groups'] == 'Alcohol'

def test_verify_distribution_stats(temp_log_file):
    """Test logging of distribution statistics."""
    results = [
        {'molecule_id': 'm1', 'mw': 10.0, 'atom_count': 5},
        {'molecule_id': 'm2', 'mw': 30.0, 'atom_count': 15}
    ]
    verify_distribution_stats(results, temp_log_file)
    
    assert temp_log_file.exists()
    content = temp_log_file.read_text()
    assert "Status: PASS" in content
    assert "Mean" in content
    assert "Std" in content