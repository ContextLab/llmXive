"""
Unit tests for MoleculeProcessor (SMILES parsing, descriptors, graph features).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.preprocess import MoleculeProcessor

@pytest.fixture
def valid_smiles():
    return [
        "CCO",          # Ethanol
        "CC(=O)O",      # Acetic acid
        "c1ccccc1",     # Benzene
        "CC1=CC=CC=C1", # Toluene
        "C1CCCCC1"      # Cyclohexane
    ]

@pytest.fixture
def invalid_smiles():
    return ["INVALID", "####", ""]

@pytest.fixture
def processor_config():
    return {
        "bias_threshold": 0.85,
        "retention_threshold": 0.95
    }

def test_parse_smiles_valid(valid_smiles, processor_config):
    processor = MoleculeProcessor(processor_config)
    for smiles in valid_smiles:
        mol = processor.parse_smiles(smiles)
        assert mol is not None, f"Failed to parse {smiles}"
        assert Chem.MolToSmiles(mol) is not None

def test_parse_smiles_invalid(invalid_smiles, processor_config):
    processor = MoleculeProcessor(processor_config)
    for smiles in invalid_smiles:
        mol = processor.parse_smiles(smiles)
        assert mol is None, f"Should return None for invalid {smiles}"

def test_calculate_descriptors(valid_smiles, processor_config):
    processor = MoleculeProcessor(processor_config)
    mol = processor.parse_smiles("CCO")
    descriptors = processor.calculate_descriptors(mol)
    
    # Check for expected keys
    assert "MW" in descriptors
    assert "logP" in descriptors
    assert "TPSA" in descriptors
    
    # Check types
    assert isinstance(descriptors["MW"], float)
    assert isinstance(descriptors["logP"], float)

def test_flatten_graph_statistics(valid_smiles, processor_config):
    processor = MoleculeProcessor(processor_config)
    mol = processor.parse_smiles("c1ccccc1")
    graph_stats = processor.flatten_graph_statistics(mol)
    
    assert "mean_node_degree" in graph_stats
    assert "num_atoms" in graph_stats
    assert "num_bonds" in graph_stats

def test_process_dataframe(valid_smiles, invalid_smiles, processor_config, tmp_path):
    # Create a mixed dataframe
    data = {
        "smiles": valid_smiles + invalid_smiles,
        "permeability_coefficient": [-5.0] * len(valid_smiles) + [-4.0] * len(invalid_smiles),
        "polymer_type": ["P1"] * len(valid_smiles) + ["P2"] * len(invalid_smiles)
    }
    df = pd.DataFrame(data)
    input_file = tmp_path / "input.csv"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    df.to_csv(input_file, index=False)
    
    processor = MoleculeProcessor(processor_config)
    # Set retention low to avoid exit, but we expect some rows dropped
    processor.config["retention_threshold"] = 0.5 
    
    result_df = processor.process(input_file, output_dir)
    
    # Should have valid rows only
    assert len(result_df) == len(valid_smiles)
    assert "MW" in result_df.columns
    assert "logP" in result_df.columns
    assert "graph_features" in result_df.columns # Or flattened cols

if __name__ == "__main__":
    pytest.main([__file__, "-v"])