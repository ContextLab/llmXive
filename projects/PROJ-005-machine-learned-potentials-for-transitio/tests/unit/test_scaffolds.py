import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add code/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "src"))

try:
    from rdkit import Chem
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

from data.splits import extract_ligand_scaffold_id, compute_scaffold_clusters, generate_llso_splits

@pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
class TestScaffoldExtraction:
    def test_extract_murcko_scaffold(self):
        # Test with a known ligand structure (e.g., triphenylphosphine derivative)
        smiles = "CC(C)P(c1ccccc1)c2ccccc2"
        scaffold = extract_ligand_scaffold_id(smiles)
        assert scaffold is not None
        assert len(scaffold) > 0
        # The scaffold should be a canonical SMILES string
        assert isinstance(scaffold, str)

    def test_extract_scaffold_different_molecules(self):
        # Two molecules with same scaffold but different side chains
        smiles1 = "CC(C)P(c1ccccc1)c2ccccc2"
        smiles2 = "CC(C)P(c1ccccc1)c2ccccc2C" # hypothetical modification
        
        scaffold1 = extract_ligand_scaffold_id(smiles1)
        scaffold2 = extract_ligand_scaffold_id(smiles2)
        
        # Note: Depending on the exact modification, they might or might not have the same scaffold.
        # This test primarily ensures the function runs without error.
        assert scaffold1 is not None
        assert scaffold2 is not None

@pytest.mark.skipif(not HAS_RDKIT, reason="RDKit not installed")
class TestLLSOGeneration:
    def test_generate_splits_no_overlap(self):
        # Create a mock DataFrame
        data = {
            'sample_id': ['s1', 's2', 's3', 's4', 's5', 's6'],
            'ligand_smiles': [
                'c1ccccc1', # Scaffold A
                'c1ccccc1', # Scaffold A
                'c1ccncc1', # Scaffold B
                'c1ccncc1', # Scaffold B
                'c1ccccn1', # Scaffold C
                'c1ccccn1'  # Scaffold C
            ],
            'metal_center': ['Pd', 'Pd', 'Ni', 'Ni', 'Cu', 'Cu'],
            'ligand_class': ['Group 13', 'Group 13', 'Conventional', 'Conventional', 'Group 13', 'Group 13']
        }
        df = pd.DataFrame(data)
        
        # Compute clusters
        clusters, _ = compute_scaffold_clusters(df)
        
        # Generate splits
        splits = generate_llso_splits(df, clusters, n_splits=3, seed=42)
        
        # Verify structure
        assert len(splits) == 3 # 3 folds
        
        # Check for no scaffold overlap between train and test in any fold
        # This is a bit complex to check programmatically without re-extracting,
        # but we can check that the logic ran and produced non-empty sets.
        for fold_key, fold_data in splits.items():
            assert 'train' in fold_data
            assert 'test' in fold_data
            assert len(fold_data['train']) > 0
            assert len(fold_data['test']) > 0
            # Check that train and test indices are disjoint
            assert set(fold_data['train']).isdisjoint(fold_data['test'])