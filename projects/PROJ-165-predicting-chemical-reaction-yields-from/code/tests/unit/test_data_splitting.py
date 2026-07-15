import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.data.preprocessing import scaffold_split, get_scaffold
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False
    pytest.skip("RDKit not available", allow_module_level=True)

class TestDataSplitting:
    """Unit tests for scaffold-based splitting logic (T017)."""

    @pytest.fixture
    def sample_data(self):
        """Create a sample dataframe with known scaffolds."""
        # Simple SMILES for testing
        data = {
            'smiles': [
                'CCO',       # Ethanol (Scaffold: C-C)
                'CCCO',      # Propanol (Scaffold: C-C-C)
                'CCCCO',     # Butanol (Scaffold: C-C-C-C)
                'CC(C)O',    # Isopropanol (Scaffold: C-C(C)-C -> C-C-C with branch)
                'c1ccccc1',  # Benzene (Scaffold: c1ccccc1)
                'c1ccccc1O', # Phenol (Scaffold: c1ccccc1)
                'c1ccccc1C', # Toluene (Scaffold: c1ccccc1)
                'CC(=O)O',   # Acetic Acid (Scaffold: C-C(=O)-O)
                'CCC(=O)O',  # Propanoic Acid (Scaffold: C-C-C(=O)-O)
                'CC(=O)OC',  # Methyl Acetate (Scaffold: C-C(=O)-O-C)
            ],
            'dft_energy': np.random.rand(10) * 100,
            'solvent': ['A'] * 10,
            'catalyst': ['X'] * 10
        }
        return pd.DataFrame(data)

    def test_scaffold_extraction(self, sample_data):
        """Test that scaffolds are extracted correctly."""
        # We expect some scaffolds to be shared (e.g., Benzene, Phenol, Toluene)
        # and some to be unique.
        scaffolds = sample_data['smiles'].apply(get_scaffold)
        assert len(scaffolds) == len(sample_data)
        assert not scaffolds.isnull().all(), "All scaffolds extracted as NULL/ERROR"

    def test_scaffold_split_no_overlap(self, sample_data):
        """Test that scaffold split ensures zero overlap between train/val/test."""
        train_df, val_df, test_df = scaffold_split(
            sample_data, 
            smiles_col='smiles', 
            train_ratio=0.6, 
            val_ratio=0.2, 
            test_ratio=0.2, 
            seed=42
        )
        
        train_scaffolds = set(train_df['scaffold'].unique())
        val_scaffolds = set(val_df['scaffold'].unique())
        test_scaffolds = set(test_df['scaffold'].unique())
        
        # Check for overlaps
        assert len(train_scaffolds & val_scaffolds) == 0, "Overlap between train and val!"
        assert len(train_scaffolds & test_scaffolds) == 0, "Overlap between train and test!"
        assert len(val_scaffolds & test_scaffolds) == 0, "Overlap between val and test!"

    def test_scaffold_split_coverage(self, sample_data):
        """Test that all samples are assigned to exactly one split."""
        train_df, val_df, test_df = scaffold_split(
            sample_data, 
            smiles_col='smiles', 
            train_ratio=0.6, 
            val_ratio=0.2, 
            test_ratio=0.2, 
            seed=42
        )
        
        total_original = len(sample_data)
        total_split = len(train_df) + len(val_df) + len(test_df)
        
        assert total_original == total_split, f"Sample count mismatch: {total_original} vs {total_split}"

    def test_conditions_preserved_in_split(self, sample_data):
        """Test that condition columns are preserved in the split dataframes (FR-011)."""
        train_df, val_df, test_df = scaffold_split(
            sample_data, 
            smiles_col='smiles', 
            seed=42
        )
        
        # Check that condition columns exist
        assert 'solvent' in train_df.columns
        assert 'catalyst' in train_df.columns
        assert 'solvent' in val_df.columns
        assert 'catalyst' in val_df.columns
        assert 'solvent' in test_df.columns
        assert 'catalyst' in test_df.columns
        
        # Check that the values are consistent with the original data
        # (i.e., we didn't drop rows or scramble values)
        original_solvents = set(sample_data['solvent'])
        split_solvents = set(train_df['solvent']).union(set(val_df['solvent'])).union(set(test_df['solvent']))
        assert original_solvents == split_solvents

    def test_deterministic_split(self, sample_data):
        """Test that splitting with the same seed produces the same result."""
        train1, val1, test1 = scaffold_split(sample_data, smiles_col='smiles', seed=123)
        train2, val2, test2 = scaffold_split(sample_data, smiles_col='smiles', seed=123)
        
        # Compare lengths
        assert len(train1) == len(train2)
        assert len(val1) == len(val2)
        assert len(test1) == len(test2)
        
        # Compare scaffolds sets
        assert set(train1['scaffold'].unique()) == set(train2['scaffold'].unique())
        assert set(val1['scaffold'].unique()) == set(val2['scaffold'].unique())
        assert set(test1['scaffold'].unique()) == set(test2['scaffold'].unique())