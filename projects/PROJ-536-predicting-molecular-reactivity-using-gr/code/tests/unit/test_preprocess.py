import pytest
import pandas as pd
import numpy as np
import os
import sys
from unittest.mock import MagicMock, patch
import tempfile

# Add code directory to path if not already there
code_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'code')
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from src.data.preprocess import get_murcko_scaffold, calculate_scaffold_split

class TestScaffoldSplit:
    
    def test_get_murcko_scaffold_basic(self):
        """Test basic scaffold extraction."""
        # Benzene -> Benzene
        smiles = "c1ccccc1"
        scaffold = get_murcko_scaffold(smiles)
        assert scaffold is not None
        # The scaffold of benzene is benzene
        assert "c1ccccc1" in scaffold or scaffold == "c1ccccc1"
        
        # Toluene -> Benzene (scaffold removes methyl)
        toluene = "Cc1ccccc1"
        scaffold_tol = get_murcko_scaffold(toluene)
        assert scaffold_tol is not None
        # Should be benzene ring
        assert scaffold_tol == "c1ccccc1"
    
    def test_get_murcko_scaffold_invalid(self):
        """Test handling of invalid SMILES."""
        assert get_murcko_scaffold(None) is None
        assert get_murcko_scaffold("") is None
        assert get_murcko_scaffold("INVALID_SMILES_STRING") is None
    
    def test_scaffold_split_no_leakage(self):
        """Test that scaffold split ensures no scaffold overlap between sets."""
        # Create a mock dataset
        # We need molecules that map to known scaffolds
        # Scaffold A: Benzene (c1ccccc1) -> 3 samples
        # Scaffold B: Pyridine (c1ccncc1) -> 2 samples
        # Scaffold C: Cyclohexane (C1CCCCC1) -> 1 sample
        
        data = {
            'smiles': [
                "c1ccccc1", "c1ccccc1", "c1ccccc1", # 3 Benzene
                "c1ccncc1", "c1ccncc1",            # 2 Pyridine
                "C1CCCCC1"                         # 1 Cyclohexane
            ],
            'yield': [0.8, 0.9, 0.85, 0.7, 0.75, 0.6]
        }
        df = pd.DataFrame(data)
        
        # Run split with seed 42
        # With 6 samples, split might be 4/1/1 or similar depending on shuffle
        # The critical part is that if a scaffold is in train, it cannot be in val/test
        
        splits = calculate_scaffold_split(
            df, 
            smiles_col='smiles', 
            split_ratios=(0.6, 0.2, 0.2), 
            seed=42
        )
        
        train_scaffolds = set()
        val_scaffolds = set()
        test_scaffolds = set()
        
        for smiles in splits['train']['smiles']:
            s = get_murcko_scaffold(smiles)
            if s: train_scaffolds.add(s)
        for smiles in splits['val']['smiles']:
            s = get_murcko_scaffold(smiles)
            if s: val_scaffolds.add(s)
        for smiles in splits['test']['smiles']:
            s = get_murcko_scaffold(smiles)
            if s: test_scaffolds.add(s)
        
        # Check intersection
        assert len(train_scaffolds & val_scaffolds) == 0, "Leakage between Train and Val"
        assert len(train_scaffolds & test_scaffolds) == 0, "Leakage between Train and Test"
        assert len(val_scaffolds & test_scaffolds) == 0, "Leakage between Val and Test"
        
        # Check total count
        total_samples = len(splits['train']) + len(splits['val']) + len(splits['test'])
        assert total_samples == len(df), "Sample count mismatch"
    
    def test_scaffold_split_invalid_smiles_handling(self):
        """Test that invalid SMILES are handled gracefully."""
        data = {
            'smiles': [
                "c1ccccc1", 
                "INVALID", 
                "c1ccncc1"
            ],
            'yield': [0.8, 0.9, 0.7]
        }
        df = pd.DataFrame(data)
        
        # Should not raise an error, just exclude invalid ones
        splits = calculate_scaffold_split(df, smiles_col='smiles', seed=42)
        
        # Check that invalid was excluded
        total = len(splits['train']) + len(splits['val']) + len(splits['test'])
        assert total == 2, "Invalid SMILES should be excluded from split"
    
    def test_split_ratios_sum_error(self):
        """Test that incorrect ratios raise an error."""
        df = pd.DataFrame({'smiles': ['c1ccccc1'], 'yield': [0.5]})
        with pytest.raises(ValueError):
            calculate_scaffold_split(df, split_ratios=(0.5, 0.5, 0.5))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])