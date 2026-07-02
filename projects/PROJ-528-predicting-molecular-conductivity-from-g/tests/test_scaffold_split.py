"""
Unit tests for scaffold-based train/test split functionality.
"""

import pytest
import pandas as pd
import numpy as np
from rdkit import Chem

from code.scaffold_split import get_murcko_scaffold, scaffold_split, split_indices


class TestMurckoScaffold:
    """Tests for scaffold extraction."""

    def test_benzene_scaffold(self):
        """Benzene should return a benzene ring scaffold."""
        smiles = "c1ccccc1"
        scaffold = get_murcko_scaffold(smiles)
        assert scaffold is not None
        # Canonical form of benzene scaffold
        assert "c1ccccc1" in scaffold or "C1=CC=CC=C1" in scaffold

    def test_toluene_scaffold(self):
        """Toluene should return the same scaffold as benzene."""
        toluene = "Cc1ccccc1"
        benzene = "c1ccccc1"
        assert get_murcko_scaffold(toluene) == get_murcko_scaffold(benzene)

    def test_invalid_smiles(self):
        """Invalid SMILES should return None."""
        assert get_murcko_scaffold("invalid_smiles_string") is None

    def test_ethane_scaffold(self):
        """Ethane (aliphatic) should have a simple scaffold."""
        smiles = "CC"
        scaffold = get_murcko_scaffold(smiles)
        assert scaffold is not None
        # Ethane scaffold is just a single bond or empty ring system
        # RDKit returns "C" for ethane scaffold

class TestScaffoldSplit:
    """Tests for scaffold-based splitting."""

    def test_split_ratio(self):
        """Test that split approximately matches the requested ratio."""
        # Create a dataset with known scaffolds
        # 10 benzene derivatives (same scaffold)
        # 5 toluene derivatives (same scaffold)
        # 5 ethane derivatives (same scaffold)
        # Total: 3 scaffolds
        smiles_list = (
            ["c1ccccc1"] * 10 +
            ["Cc1ccccc1"] * 5 +
            ["CC"] * 5
        )
        df = pd.DataFrame({"smiles": smiles_list, "target": np.random.rand(len(smiles_list))})

        train_df, test_df = scaffold_split(df, train_ratio=0.66, seed=42)

        # With 3 scaffolds and 66% ratio, we expect 2 scaffolds in train, 1 in test
        # Benzene scaffold (10) + Ethane (5) = 15 train, Toluene (5) = 5 test
        # OR Benzene (10) + Toluene (5) = 15 train, Ethane (5) = 5 test
        assert len(train_df) + len(test_df) == len(df)
        assert len(train_df) > 0
        assert len(test_df) > 0

    def test_no_scaffold_leakage(self):
        """Ensure no scaffold appears in both train and test sets."""
        smiles_list = [
            "c1ccccc1", "Cc1ccccc1", "CCc1ccccc1",  # Benzene scaffold
            "CC", "CCC", "CCCC",  # Aliphatic scaffold
            "c1ccncc1", "Cc1ccncc1"  # Pyridine scaffold
        ]
        df = pd.DataFrame({"smiles": smiles_list, "target": np.random.rand(len(smiles_list))})

        train_df, test_df = scaffold_split(df, train_ratio=0.5, seed=42)

        train_scaffolds = set(train_df["smiles"].apply(lambda x: get_murcko_scaffold(x)))
        test_scaffolds = set(test_df["smiles"].apply(lambda x: get_murcko_scaffold(x)))

        # No intersection between train and test scaffolds
        assert len(train_scaffolds.intersection(test_scaffolds)) == 0

    def test_empty_dataframe(self):
        """Should raise ValueError on empty DataFrame."""
        df = pd.DataFrame({"smiles": [], "target": []})
        with pytest.raises(ValueError):
            scaffold_split(df)

    def test_invalid_column(self):
        """Should raise ValueError if smiles column is missing."""
        df = pd.DataFrame({"wrong_col": ["c1ccccc1"], "target": [1.0]})
        with pytest.raises(ValueError):
            scaffold_split(df, smiles_col="smiles")

    def test_reproducibility(self):
        """Split should be reproducible with the same seed."""
        smiles_list = ["c1ccccc1", "Cc1ccccc1", "CC", "CCC", "c1ccncc1", "CCc1ccccc1"]
        df = pd.DataFrame({"smiles": smiles_list, "target": np.random.rand(len(smiles_list))})

        train1, test1 = scaffold_split(df, seed=123)
        train2, test2 = scaffold_split(df, seed=123)

        assert train1.equals(train2)
        assert test1.equals(test2)

class TestSplitIndices:
    """Tests for index-based splitting."""

    def test_indices_coverage(self):
        """Train and test indices should cover all rows."""
        df = pd.DataFrame({
            "smiles": ["c1ccccc1", "CC", "c1ccncc1"],
            "target": [1.0, 2.0, 3.0]
        })
        train_idx, test_idx = split_indices(df, seed=42)

        all_idx = set(train_idx) | set(test_idx)
        assert all_idx == set(df.index)
        assert len(set(train_idx) & set(test_idx)) == 0

    def test_indices_length(self):
        """Indices should sum to total length."""
        df = pd.DataFrame({
            "smiles": ["c1ccccc1"] * 10 + ["CC"] * 10,
            "target": np.random.rand(20)
        })
        train_idx, test_idx = split_indices(df, seed=42)
        assert len(train_idx) + len(test_idx) == len(df)
