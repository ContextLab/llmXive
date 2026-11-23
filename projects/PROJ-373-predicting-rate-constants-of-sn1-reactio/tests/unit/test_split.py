import pytest
import pandas as pd
import numpy as np
import sys
import os
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from models.train import scaffold_split, get_scaffold

class TestScaffoldSplit:
    @pytest.fixture
    def mock_data(self):
        """Create a mock dataset with distinct scaffolds."""
        # Create molecules with distinct scaffolds
        # Scaffold A: C1CCCCC1 (Cyclohexane-like)
        # Scaffold B: C1=CC=CC=C1 (Benzene-like)
        # Scaffold C: CC(C)C (Isobutane-like)
        data = {
            "smiles": [
                "C1CCCCC1", "C1CCCCC1", "C1CCCCC1", # Scaffold A
                "C1=CC=CC=C1", "C1=CC=CC=C1", "C1=CC=CC=C1", # Scaffold B
                "CC(C)C", "CC(C)C", "CC(C)C", # Scaffold C
                "CCO", "CCO", "CCO" # Scaffold D (small)
            ],
            "rate_constant": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
            "substrate_class": ["secondary"] * 12
        }
        return pd.DataFrame(data)

    def test_get_scaffold(self):
        """Test that identical SMILES produce identical scaffolds."""
        fp1 = get_scaffold("C1CCCCC1")
        fp2 = get_scaffold("C1CCCCC1")
        fp3 = get_scaffold("C1=CC=CC=C1")
        
        assert fp1 == fp2, "Identical molecules should have identical scaffolds"
        assert fp1 != fp3, "Different molecules should have different scaffolds"
        assert fp1 != "INVALID", "Valid molecule should not return INVALID"

    def test_scaffold_split_no_leakage(self, mock_data):
        """Test that molecules with identical scaffolds are never split across train/test."""
        train_df, val_df, test_df = scaffold_split(mock_data, train_ratio=0.5, val_ratio=0.25, test_ratio=0.25, random_state=42)
        
        train_scaffolds = set(train_df['scaffold'].unique())
        test_scaffolds = set(test_df['scaffold'].unique())
        
        # Intersection should be empty
        assert len(train_scaffolds & test_scaffolds) == 0, "Scaffold leakage detected!"

    def test_scaffold_split_all_scaffolds_assigned(self, mock_data):
        """Test that all scaffolds are assigned to exactly one split."""
        train_df, val_df, test_df = scaffold_split(mock_data, train_ratio=0.5, val_ratio=0.25, test_ratio=0.25, random_state=42)
        
        all_train_scaffolds = set(train_df['scaffold'].unique())
        all_val_scaffolds = set(val_df['scaffold'].unique())
        all_test_scaffolds = set(test_df['scaffold'].unique())
        
        all_scaffolds = all_train_scaffolds | all_val_scaffolds | all_test_scaffolds
        original_scaffolds = set(mock_data['scaffold'].unique())
        
        assert all_scaffolds == original_scaffolds, "Not all scaffolds were assigned"
        
        # Check for overlap
        assert len(all_train_scaffolds & all_val_scaffolds) == 0
        assert len(all_train_scaffolds & all_test_scaffolds) == 0
        assert len(all_val_scaffolds & all_test_scaffolds) == 0

    def test_reproducibility(self, mock_data):
        """Test that the split is reproducible with the same random state."""
        train1, val1, test1 = scaffold_split(mock_data, random_state=123)
        train2, val2, test2 = scaffold_split(mock_data, random_state=123)
        
        pd.testing.assert_frame_equal(train1.reset_index(drop=True), train2.reset_index(drop=True))
        pd.testing.assert_frame_equal(val1.reset_index(drop=True), val2.reset_index(drop=True))
        pd.testing.assert_frame_equal(test1.reset_index(drop=True), test2.reset_index(drop=True))

    def test_empty_dataset(self):
        """Test that an empty dataset is handled gracefully."""
        empty_df = pd.DataFrame(columns=["smiles", "rate_constant", "substrate_class"])
        with pytest.raises((KeyError, ValueError)):
            scaffold_split(empty_df)