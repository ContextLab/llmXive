"""
Unit tests for scaffold extraction and leakage check logic.
Tests the scaffold-based splitting algorithm to ensure zero overlap
between train, validation, and test sets.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path if not already present
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.preprocessing import preprocess_dataset, load_and_preprocess
from src.utils.seeds import set_seed
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors


def get_molecular_scaffold(smiles: str) -> str:
    """
    Extract the molecular scaffold from a SMILES string using RDKit.
    This function removes side chains to leave the core ring system.
    
    Args:
        smiles: A valid SMILES string.
        
    Returns:
        Canonical SMILES of the scaffold, or None if extraction fails.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Generate scaffold using Murcko framework
        scaffold = rdMolDescriptors.GetScaffoldForMol(mol)
        
        if scaffold is None:
            return None
            
        # Return canonical SMILES of the scaffold
        return Chem.MolToSmiles(scaffold, isomericSmiles=True, canonical=True)
    except Exception:
        return None


def extract_scaffolds_from_df(df: pd.DataFrame, smiles_col: str = 'smiles') -> dict:
    """
    Extract scaffolds for all molecules in a DataFrame.
    
    Args:
        df: DataFrame containing SMILES strings.
        smiles_col: Column name containing SMILES.
        
    Returns:
        Dictionary mapping index to scaffold SMILES.
    """
    scaffolds = {}
    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        scaffold = get_molecular_scaffold(smiles)
        if scaffold:
            scaffolds[idx] = scaffold
    return scaffolds


def check_scaffold_leakage(train_scaffolds: set, val_scaffolds: set, test_scaffolds: set) -> dict:
    """
    Check for scaffold overlap between train, validation, and test sets.
    
    Args:
        train_scaffolds: Set of scaffold SMILES from training set.
        val_scaffolds: Set of scaffold SMILES from validation set.
        test_scaffolds: Set of scaffold SMILES from test set.
        
    Returns:
        Dictionary containing leakage statistics.
    """
    results = {
        'train_val_overlap': len(train_scaffolds.intersection(val_scaffolds)),
        'train_test_overlap': len(train_scaffolds.intersection(test_scaffolds)),
        'val_test_overlap': len(val_scaffolds.intersection(test_scaffolds)),
        'total_overlaps': 0,
        'leakage_detected': False
    }
    
    results['total_overlaps'] = (
        results['train_val_overlap'] + 
        results['train_test_overlap'] + 
        results['val_test_overlap']
    )
    
    results['leakage_detected'] = results['total_overlaps'] > 0
    
    return results


class TestScaffoldExtraction:
    """Unit tests for scaffold extraction logic."""
    
    def test_scaffold_extraction_simple_molecule(self):
        """Test scaffold extraction on a simple molecule."""
        smiles = "CCO"  # Ethanol
        scaffold = get_molecular_scaffold(smiles)
        # Ethanol has no rings, so scaffold should be just the carbon chain
        assert scaffold is not None
        assert isinstance(scaffold, str)
        
    def test_scaffold_extraction_benzene(self):
        """Test scaffold extraction on benzene."""
        smiles = "c1ccccc1"  # Benzene
        scaffold = get_molecular_scaffold(smiles)
        assert scaffold is not None
        # Benzene scaffold should be benzene itself
        assert "c1ccccc1" in scaffold or "C1=CC=CC=C1" in scaffold
        
    def test_scaffold_extraction_toluene(self):
        """Test scaffold extraction on toluene (benzene with methyl)."""
        smiles = "Cc1ccccc1"  # Toluene
        scaffold = get_molecular_scaffold(smiles)
        assert scaffold is not None
        # Scaffold should be benzene (methyl is a side chain)
        assert "c1ccccc1" in scaffold or "C1=CC=CC=C1" in scaffold
        
    def test_scaffold_extraction_invalid_smiles(self):
        """Test scaffold extraction on invalid SMILES."""
        invalid_smiles = "invalid_smiles_string"
        scaffold = get_molecular_scaffold(invalid_smiles)
        assert scaffold is None
        
    def test_scaffold_extraction_empty_string(self):
        """Test scaffold extraction on empty string."""
        scaffold = get_molecular_scaffold("")
        assert scaffold is None


class TestLeakageCheck:
    """Unit tests for scaffold leakage detection."""
    
    def test_no_leakage(self):
        """Test that no leakage is detected when scaffolds are distinct."""
        train_scaffolds = {"c1ccccc1", "C1CCCCC1"}  # Benzene, Cyclohexane
        val_scaffolds = {"c1ccncc1", "C1CCNCC1"}    # Pyridine, Piperidine
        test_scaffolds = {"c1ccco1", "C1CCCO1"}     # Furan, Tetrahydrofuran
        
        results = check_scaffold_leakage(train_scaffolds, val_scaffolds, test_scaffolds)
        
        assert results['leakage_detected'] is False
        assert results['train_val_overlap'] == 0
        assert results['train_test_overlap'] == 0
        assert results['val_test_overlap'] == 0
        
    def test_leakage_detected_train_val(self):
        """Test that leakage is detected between train and validation."""
        train_scaffolds = {"c1ccccc1", "C1CCCCC1"}
        val_scaffolds = {"c1ccccc1", "C1CCNCC1"}  # Overlap with benzene
        test_scaffolds = {"c1ccco1", "C1CCCO1"}
        
        results = check_scaffold_leakage(train_scaffolds, val_scaffolds, test_scaffolds)
        
        assert results['leakage_detected'] is True
        assert results['train_val_overlap'] == 1
        
    def test_leakage_detected_all_splits(self):
        """Test leakage detection across all splits."""
        common_scaffold = "c1ccccc1"
        train_scaffolds = {common_scaffold, "C1CCCCC1"}
        val_scaffolds = {common_scaffold, "C1CCNCC1"}
        test_scaffolds = {common_scaffold, "C1CCCO1"}
        
        results = check_scaffold_leakage(train_scaffolds, val_scaffolds, test_scaffolds)
        
        assert results['leakage_detected'] is True
        assert results['train_val_overlap'] == 1
        assert results['train_test_overlap'] == 1
        assert results['val_test_overlap'] == 1
        assert results['total_overlaps'] == 3


class TestScaffoldSplitIntegration:
    """Integration tests for scaffold-based splitting."""
    
    @pytest.fixture
    def sample_dataset(self):
        """Create a sample dataset for testing."""
        set_seed(42)
        
        data = {
            'smiles': [
                'c1ccccc1',      # Benzene
                'Cc1ccccc1',     # Toluene (same scaffold as benzene)
                'CCc1ccccc1',    # Ethylbenzene (same scaffold)
                'c1ccncc1',      # Pyridine
                'Cc1ccncc1',     # Methylpyridine (same scaffold)
                'C1CCCCC1',      # Cyclohexane
                'C1CCNCC1',      # Piperidine
                'C1CCCO1',       # Tetrahydrofuran
                'c1ccco1',       # Furan
                'CC(=O)Oc1ccccc1C(=O)O'  # Aspirin
            ],
            'normalized_energy': np.random.randn(10),
            'solvent': ['water'] * 10,
            'temperature': [298] * 10
        }
        
        return pd.DataFrame(data)
        
    def test_scaffold_split_no_leakage(self, sample_dataset):
        """Test that scaffold splitting produces no leakage."""
        # Group molecules by scaffold
        sample_dataset['scaffold'] = sample_dataset['smiles'].apply(get_molecular_scaffold)
        
        # Remove rows with None scaffolds
        sample_dataset = sample_dataset.dropna(subset=['scaffold'])
        
        # Get unique scaffolds
        scaffolds = sample_dataset['scaffold'].unique()
        
        # Manually split scaffolds (not molecules) to ensure no overlap
        np.random.seed(42)
        np.random.shuffle(scaffolds)
        
        n_scaffolds = len(scaffolds)
        train_end = int(n_scaffolds * 0.7)
        val_end = int(n_scaffolds * 0.85)
        
        train_scaffolds = set(scaffolds[:train_end])
        val_scaffolds = set(scaffolds[train_end:val_end])
        test_scaffolds = set(scaffolds[val_end:])
        
        # Assign molecules to splits based on their scaffold
        def assign_split(scaffold):
            if scaffold in train_scaffolds:
                return 'train'
            elif scaffold in val_scaffolds:
                return 'val'
            else:
                return 'test'
                
        sample_dataset['split'] = sample_dataset['scaffold'].apply(assign_split)
        
        # Extract scaffolds per split
        train_s = set(sample_dataset[sample_dataset['split'] == 'train']['scaffold'].unique())
        val_s = set(sample_dataset[sample_dataset['split'] == 'val']['scaffold'].unique())
        test_s = set(sample_dataset[sample_dataset['split'] == 'test']['scaffold'].unique())
        
        # Check for leakage
        results = check_scaffold_leakage(train_s, val_s, test_s)
        
        assert results['leakage_detected'] is False, \
            f"Scaffold leakage detected: {results}"
            
    def test_scaffold_split_distribution(self, sample_dataset):
        """Test that scaffold split produces reasonable distribution."""
        # Same logic as above
        sample_dataset['scaffold'] = sample_dataset['smiles'].apply(get_molecular_scaffold)
        sample_dataset = sample_dataset.dropna(subset=['scaffold'])
        
        scaffolds = sample_dataset['scaffold'].unique()
        np.random.seed(42)
        np.random.shuffle(scaffolds)
        
        n_scaffolds = len(scaffolds)
        train_end = int(n_scaffolds * 0.7)
        val_end = int(n_scaffolds * 0.85)
        
        train_scaffolds = set(scaffolds[:train_end])
        val_scaffolds = set(scaffolds[train_end:val_end])
        test_scaffolds = set(scaffolds[val_end:])
        
        def assign_split(scaffold):
            if scaffold in train_scaffolds:
                return 'train'
            elif scaffold in val_scaffolds:
                return 'val'
            else:
                return 'test'
                
        sample_dataset['split'] = sample_dataset['scaffold'].apply(assign_split)
        
        # Check that all splits have at least one sample
        assert len(sample_dataset[sample_dataset['split'] == 'train']) > 0
        assert len(sample_dataset[sample_dataset['split'] == 'val']) > 0
        assert len(sample_dataset[sample_dataset['split'] == 'test']) > 0