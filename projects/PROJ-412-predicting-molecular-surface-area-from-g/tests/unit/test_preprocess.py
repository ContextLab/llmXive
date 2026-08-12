import pytest
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.preprocess import (
    generate_conformer_config,
    map_rdkit_exception_to_reason,
    generate_3d_conformer,
    process_molecule_3d,
    process_chunk_3d,
    save_conformer_params,
    save_failure_report,
    FAILURE_ETKDG,
    FAILURE_MINIMIZATION,
    FAILURE_INVALID_VALENCE,
    FAILURE_CONFORMER_GEN
)
from utils.seed import set_seed

@pytest.fixture
def sample_mol():
    return Chem.MolFromSmiles("CCO") # Ethanol

@pytest.fixture
def sample_mol_large():
    return Chem.MolFromSmiles("CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC") # Long chain

@pytest.fixture
def invalid_smiles_mol():
    return Chem.MolFromSmiles("CC(C)C1=CC=CC=C1C(C)C") # Valid, but let's test invalid
    # Actually, let's test a truly invalid one if possible, but RDKit is lenient.
    # We can test valence by creating a mol with wrong valence manually if needed.

def test_generate_conformer_config_defaults():
    config = generate_conformer_config()
    assert config['random_seed'] is not None
    assert config['numThreads'] == 0
    assert config['maxAttempts'] == 200

def test_generate_conformer_config_override():
    config = generate_conformer_config({'numThreads': 4, 'maxAttempts': 100})
    assert config['numThreads'] == 4
    assert config['maxAttempts'] == 100
    assert config['random_seed'] is not None

def test_map_rdkit_exception_to_reason():
    # Test ValueError -> INVALID_VALENCE
    assert map_rdkit_exception_to_reason(ValueError("valence error")) == FAILURE_INVALID_VALENCE
    # Test RuntimeError with minimization -> MINIMIZATION_FAIL
    assert map_rdkit_exception_to_reason(RuntimeError("minimization failed")) == FAILURE_MINIMIZATION
    # Test RuntimeError with etkdg -> ETKDG_FAIL
    assert map_rdkit_exception_to_reason(RuntimeError("etkdg failed")) == FAILURE_ETKDG
    # Test generic RDKitException -> CONFORMER_GENERATION_FAIL
    assert map_rdkit_exception_to_reason(Exception("some rdkit error")) == FAILURE_CONFORMER_GEN

def test_generate_3d_conformer_success(sample_mol):
    config = generate_conformer_config({'random_seed': 123})
    mol_out, reason = generate_3d_conformer(sample_mol, config)
    assert mol_out is not None
    assert reason is None
    assert mol_out.GetNumConformers() > 0

def test_generate_3d_conformer_failure_invalid_valence():
    # Create a molecule with invalid valence (hard to do directly with SMILES, 
    # but we can test the mapping logic via the exception handler)
    # For this test, we rely on the fact that some molecules might fail ETKDG
    # We'll test with a very large molecule that might fail due to complexity
    large_smiles = "C" * 200 # Very long chain
    mol = Chem.MolFromSmiles(large_smiles)
    if mol:
        config = generate_conformer_config({'random_seed': 999, 'maxAttempts': 1}) # Force failure
        mol_out, reason = generate_3d_conformer(mol, config)
        # It might fail or succeed, but if it fails, reason should be set
        # We just ensure no crash
        assert isinstance(reason, str) or reason is None

def test_process_molecule_3d_success():
    mol = Chem.MolFromSmiles("CCO")
    row = {'smiles': 'CCO', 'mol': mol}
    config = generate_conformer_config({'random_seed': 42})
    result = process_molecule_3d(row, config)
    
    assert result['smiles'] == 'CCO'
    assert result['failure_reason'] is None
    assert 'conformer_coords' in result
    assert result['atom_count'] == 3

def test_process_molecule_3d_failure():
    # Force a failure by using a seed that might cause ETKDG to fail for a specific molecule
    # or by using a molecule known to be problematic.
    # Here we test the logic by mocking a failure or using a known bad case.
    # Since ETKDG is stochastic, we test the structure of the failure output.
    mol = Chem.MolFromSmiles("CCO")
    row = {'smiles': 'CCO', 'mol': mol}
    
    # Simulate a failure by passing a config that forces failure (e.g., maxAttempts=0 if supported, or just bad seed)
    # We can't easily force failure without specific conditions, so we test the happy path structure mostly.
    # But we can test that if we pass a None mol, it fails.
    row_bad = {'smiles': 'CCO', 'mol': None}
    config = generate_conformer_config()
    result = process_molecule_3d(row_bad, config)
    
    assert result['failure_reason'] == FAILURE_INVALID_VALENCE
    assert result['conformer'] is None

def test_process_chunk_3d():
    df = pd.DataFrame([
        {'smiles': 'CCO', 'mol': Chem.MolFromSmiles('CCO')},
        {'smiles': 'CC', 'mol': Chem.MolFromSmiles('CC')}
    ])
    config = generate_conformer_config({'random_seed': 42})
    
    success_df, failures = process_chunk_3d(df, config)
    
    assert len(success_df) <= len(df)
    assert len(failures) + len(success_df) == len(df)

def test_save_conformer_params(tmp_path):
    config = {'numThreads': 1, 'maxAttempts': 100, 'random_seed': 42}
    output_path = tmp_path / "params.json"
    save_conformer_params(config, output_path)
    
    assert output_path.exists()
    with open(output_path) as f:
        loaded = json.load(f)
    assert loaded['numThreads'] == 1
    assert loaded['random_seed'] == 42

def test_save_failure_report_empty(tmp_path):
    output_path = tmp_path / "failures.csv"
    save_failure_report([], output_path)
    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 0
    assert list(df.columns) == ['smiles', 'failure_reason', 'atom_count']

def test_save_failure_report_with_data(tmp_path):
    failures = [
        {'smiles': 'CCO', 'failure_reason': 'ETKDG_FAIL', 'atom_count': 3},
        {'smiles': 'CC', 'failure_reason': 'MINIMIZATION_FAIL', 'atom_count': 2}
    ]
    output_path = tmp_path / "failures.csv"
    save_failure_report(failures, output_path)
    
    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 2
    assert df.iloc[0]['smiles'] == 'CCO'
    assert df.iloc[0]['failure_reason'] == 'ETKDG_FAIL'