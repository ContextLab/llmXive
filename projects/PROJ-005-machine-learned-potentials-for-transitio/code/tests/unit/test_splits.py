"""
Unit tests for the LLSO split generation logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.splits import (
    extract_ligand_scaffold_id,
    generate_llso_splits,
    write_splits_json,
    load_graphs_for_splitting
)

@pytest.fixture
def sample_graphs_df():
    """Create a sample DataFrame mimicking the processed graphs."""
    data = {
        'sample_id': [f'sample_{i}' for i in range(20)],
        'ligand_class': ['Group13'] * 10 + ['Conventional'] * 10,
        'metal_center': ['Pd'] * 20,
        # Simulate some SMILES with shared scaffolds and some unique
        'coordination_sphere_smiles': [
            'B(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold A
            'B(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold A
            'B(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold A
            'Al(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold B (Al instead of B)
            'Al(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold B
            'Ga(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold C
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D (Conventional)
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
            'P(c1ccccc1)(c2ccccc2)c3ccccc3', # Scaffold D
        ]
    }
    return pd.DataFrame(data)

def test_extract_ligand_scaffold_id_valid_smiles(sample_graphs_df):
    """Test that valid SMILES produce consistent scaffold IDs."""
    row = sample_graphs_df.iloc[0]
    scaffold_id_1 = extract_ligand_scaffold_id(row)
    
    row_2 = sample_graphs_df.iloc[1]
    scaffold_id_2 = extract_ligand_scaffold_id(row_2)
    
    # Same SMILES should yield same scaffold ID
    assert scaffold_id_1 == scaffold_id_2
    assert isinstance(scaffold_id_1, str)
    assert len(scaffold_id_1) == 16  # Hex length from sha256[:16]

def test_extract_ligand_scaffold_id_invalid_smiles():
    """Test handling of invalid or missing SMILES."""
    row = pd.Series({'sample_id': 'test_1', 'coordination_sphere_smiles': None})
    scaffold_id = extract_ligand_scaffold_id(row)
    assert scaffold_id.startswith('fallback_')
    
    row_invalid = pd.Series({'sample_id': 'test_2', 'coordination_sphere_smiles': 'invalid_smiles_!!!'})
    scaffold_id_invalid = extract_ligand_scaffold_id(row_invalid)
    assert scaffold_id_invalid.startswith('fallback_')

def test_generate_llso_splits_no_overlap(sample_graphs_df):
    """Test that generated splits have no scaffold overlap between train and test."""
    # Add scaffold_id column
    sample_graphs_df['scaffold_id'] = sample_graphs_df.apply(
        lambda row: extract_ligand_scaffold_id(row), axis=1
    )
    
    splits = generate_llso_splits(sample_graphs_df, n_folds=5, seed=42)
    
    assert len(splits) == 5
    
    for split in splits:
        train_scaffolds = set(split['train_scaffolds'])
        test_scaffolds = set(split['test_scaffolds'])
        val_scaffolds = set(split['val_scaffolds'])
        
        # Check train-test disjoint
        assert train_scaffolds.isdisjoint(test_scaffolds), \
            f"Train and test sets share scaffolds: {train_scaffolds & test_scaffolds}"
        
        # Check val-test disjoint
        assert val_scaffolds.isdisjoint(test_scaffolds), \
            f"Val and test sets share scaffolds: {val_scaffolds & test_scaffolds}"
        
        # Check that test set is not empty
        assert len(split['test_indices']) > 0, "Test set should not be empty"

def test_write_splits_json(sample_graphs_df):
    """Test writing splits to JSON."""
    sample_graphs_df['scaffold_id'] = sample_graphs_df.apply(
        lambda row: extract_ligand_scaffold_id(row), axis=1
    )
    
    splits = generate_llso_splits(sample_graphs_df, n_folds=5, seed=42)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "test_splits.json"
        write_splits_json(splits, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded_splits = json.load(f)
        
        assert len(loaded_splits) == 5
        assert 'train_indices' in loaded_splits[0]
        assert 'val_indices' in loaded_splits[0]
        assert 'test_indices' in loaded_splits[0]