"""
Unit tests for confound_analysis.py (T011b)
"""
import csv
import os
import tempfile
from pathlib import Path
import pytest

# Import the module functions
from confound_analysis import (
    load_molecules_from_csv,
    parse_functional_groups,
    calculate_molecular_properties,
    process_molecule,
    write_confounds_csv
)

from rdkit import Chem


def test_parse_functional_groups_aromatic():
    """Test detection of aromatic rings."""
    mol = Chem.MolFromSmiles("c1ccccc1") # Benzene
    groups = parse_functional_groups(mol)
    assert 'aromatic' in groups


def test_parse_functional_groups_amide():
    """Test detection of amide groups."""
    mol = Chem.MolFromSmiles("CC(=O)N") # Acetamide
    groups = parse_functional_groups(mol)
    assert 'amide' in groups


def test_parse_functional_groups_hydroxyl():
    """Test detection of hydroxyl groups."""
    mol = Chem.MolFromSmiles("CCO") # Ethanol
    groups = parse_functional_groups(mol)
    assert 'hydroxyl' in groups


def test_calculate_molecular_properties():
    """Test MW and atom count calculation."""
    mol = Chem.MolFromSmiles("CCO") # Ethanol: C2H6O -> MW ~46.07, Atoms: 9
    props = calculate_molecular_properties(mol)
    
    assert 'mw' in props
    assert 'atom_count' in props
    assert props['atom_count'] == 9
    assert 46.0 < props['mw'] < 47.0


def test_process_molecule():
    """Test full processing of a molecule entry."""
    mol = Chem.MolFromSmiles("c1ccccc1")
    entry = {'id': 'test_001', 'smiles': 'c1ccccc1', 'mol': mol}
    
    result = process_molecule(entry)
    
    assert result['molecule_id'] == 'test_001'
    assert 'mw' in result
    assert 'atom_count' in result
    assert 'functional_groups' in result
    assert 'aromatic' in result['functional_groups']


def test_write_confounds_csv():
    """Test writing results to CSV."""
    results = [
        {'molecule_id': 'm1', 'mw': 100.0, 'atom_count': 10, 'functional_groups': 'aromatic'},
        {'molecule_id': 'm2', 'mw': 50.0, 'atom_count': 5, 'functional_groups': 'hydroxyl'}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = f.name
    
    try:
        write_confounds_csv(results, temp_path)
        
        assert os.path.exists(temp_path)
        
        with open(temp_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 2
        assert rows[0]['molecule_id'] == 'm1'
        assert rows[0]['functional_groups'] == 'aromatic'
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_load_molecules_from_csv():
    """Test loading molecules from a temporary CSV."""
    csv_content = """molecule_id,smiles
    m1,c1ccccc1
    m2,CCO
    m3,invalid_smiles
    """
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write(csv_content)
        temp_path = f.name
    
    try:
        molecules = load_molecules_from_csv(temp_path)
        
        # Should skip invalid
        assert len(molecules) == 2
        ids = [m['id'] for m in molecules]
        assert 'm1' in ids
        assert 'm2' in ids
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)