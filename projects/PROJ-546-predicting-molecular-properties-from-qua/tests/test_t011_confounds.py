"""
Unit tests for T011: Confounds Analysis
"""
import pytest
import csv
import os
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, Fragments
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from confounds import (
    load_molecules_from_csv,
    parse_functional_groups,
    calculate_molecular_properties,
    process_molecule,
    write_confounds_csv
)

@pytest.fixture
def sample_smiles():
    return [
        "CCO",  # Ethanol
        "CC(=O)O",  # Acetic acid
        "c1ccccc1",  # Benzene
        "CC(=O)N",  # Acetamide
    ]

@pytest.fixture
def temp_csv(tmp_path, sample_smiles):
    csv_path = tmp_path / "test_input.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['molecule_id', 'SMILES'])
        for i, smiles in enumerate(sample_smiles):
            writer.writerow([f"mol_{i}", smiles])
    return csv_path

def test_load_molecules_from_csv(temp_csv):
    molecules = load_molecules_from_csv(temp_csv)
    assert len(molecules) == 4
    assert molecules[0]['molecule_id'] == 'mol_0'
    assert molecules[0]['smiles'] == 'CCO'

def test_calculate_molecular_properties():
    mol = Chem.MolFromSmiles("CCO")
    props = calculate_molecular_properties(mol)
    assert 'mw' in props
    assert 'atom_count' in props
    assert props['atom_count'] > 0
    assert props['mw'] > 0.0

def test_parse_functional_groups():
    # Ethanol has OH
    mol = Chem.MolFromSmiles("CCO")
    groups = parse_functional_groups(mol)
    assert 'OH' in groups
    
    # Benzene has aromatic
    mol = Chem.MolFromSmiles("c1ccccc1")
    groups = parse_functional_groups(mol)
    assert 'aromatic' in groups

def test_process_molecule():
    mol_data = {'molecule_id': 'test_1', 'smiles': 'CCO'}
    result = process_molecule(mol_data)
    assert result is not None
    assert result['molecule_id'] == 'test_1'
    assert 'mw' in result
    assert 'atom_count' in result
    assert 'functional_groups' in result

def test_invalid_smiles():
    mol_data = {'molecule_id': 'invalid', 'smiles': 'INVALID_SMILES_STRING'}
    result = process_molecule(mol_data)
    assert result is None

def test_write_confounds_csv(tmp_path):
    results = [
        {'molecule_id': 'mol_1', 'mw': 46.07, 'atom_count': 9, 'functional_groups': 'OH:1'},
        {'molecule_id': 'mol_2', 'mw': 60.05, 'atom_count': 8, 'functional_groups': 'carboxyl:1'}
    ]
    output_path = tmp_path / "output.csv"
    write_confounds_csv(results, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert 'molecule_id' in rows[0]
        assert 'mw' in rows[0]
        assert 'atom_count' in rows[0]
        assert 'functional_groups' in rows[0]