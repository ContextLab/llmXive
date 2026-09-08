"""
Unit tests for phylogenetic stratified split logic.

Tests for T019: Unit test for phylogenetic stratified split logic in tests/unit/test_modeling.py
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path to match project structure
sys.path.insert(0, str(Path(__file__).parent.parent))

from modeling.train import (
    create_stratified_split,
    get_clade_members,
    find_balanced_clades,
    StratifiedSplitError
)


class TestGetCladeMembers:
    """Tests for get_clade_members function."""

    def test_returns_dict_of_clades(self):
        """Test that get_clade_members returns a dictionary mapping clade names to species lists."""
        # Mock tree data
        mock_tree = MagicMock()
        mock_tree.taxon_namespace = MagicMock()
        
        # Create mock taxa
        taxon1 = MagicMock()
        taxon1.label = "Species_A"
        taxon2 = MagicMock()
        taxon2.label = "Species_B"
        taxon3 = MagicMock()
        taxon3.label = "Species_C"
        
        mock_tree.taxon_namespace.__iter__ = lambda self: iter([taxon1, taxon2, taxon3])
        mock_tree.taxon_namespace.__len__ = lambda self: 3
        
        # Mock get_clade_members to return expected structure
        # Since we're testing the logic, we'll mock the internal behavior
        with patch('modeling.train.load_phylogeny') as mock_load:
            mock_load.return_value = mock_tree
            
            result = get_clade_members(mock_tree, min_size=1)
            
            assert isinstance(result, dict)
            # The function should return a dict with clade names as keys
            # and lists of species as values
            for clade_name, species_list in result.items():
                assert isinstance(clade_name, str)
                assert isinstance(species_list, list)

    def test_respects_min_size_parameter(self):
        """Test that get_clade_members filters clades smaller than min_size."""
        mock_tree = MagicMock()
        
        # Mock a scenario where we have clades of different sizes
        mock_tree.taxon_namespace = MagicMock()
        taxon1 = MagicMock()
        taxon1.label = "Species_A"
        mock_tree.taxon_namespace.__iter__ = lambda self: iter([taxon1])
        mock_tree.taxon_namespace.__len__ = lambda self: 1
        
        with patch('modeling.train.load_phylogeny') as mock_load:
            mock_load.return_value = mock_tree
            
            # With min_size=2, should return empty or filtered result
            result = get_clade_members(mock_tree, min_size=2)
            
            # All values in the result should have length >= min_size
            for species_list in result.values():
                assert len(species_list) >= 2, "Clade size should respect min_size parameter"


class TestFindBalancedClades:
    """Tests for find_balanced_clades function."""

    def test_returns_balanced_clades(self):
        """Test that find_balanced_clades returns clades with reasonable size balance."""
        mock_tree = MagicMock()
        mock_tree.taxon_namespace = MagicMock()
        
        # Create mock taxa
        taxa = []
        for i in range(20):
            taxon = MagicMock()
            taxon.label = f"Species_{i}"
            taxa.append(taxon)
        
        mock_tree.taxon_namespace.__iter__ = lambda self: iter(taxa)
        mock_tree.taxon_namespace.__len__ = lambda self: 20
        
        with patch('modeling.train.load_phylogeny') as mock_load:
            mock_load.return_value = mock_tree
            
            result = find_balanced_clades(mock_tree, min_clade_size=3, max_clade_size=8)
            
            assert isinstance(result, dict)
            # Check that all clades are within size bounds
            for clade_name, species_list in result.items():
                assert len(species_list) >= 3, "Clade should respect min_clade_size"
                assert len(species_list) <= 8, "Clade should respect max_clade_size"

    def test_handles_very_small_dataset(self):
        """Test behavior when dataset is too small for balanced clades."""
        mock_tree = MagicMock()
        mock_tree.taxon_namespace = MagicMock()
        
        # Create only 2 taxa
        taxa = []
        for i in range(2):
            taxon = MagicMock()
            taxon.label = f"Species_{i}"
            taxa.append(taxon)
        
        mock_tree.taxon_namespace.__iter__ = lambda self: iter(taxa)
        mock_tree.taxon_namespace.__len__ = lambda self: 2
        
        with patch('modeling.train.load_phylogeny') as mock_load:
            mock_load.return_value = mock_tree
            
            # With min_clade_size=3, should handle gracefully
            result = find_balanced_clades(mock_tree, min_clade_size=3, max_clade_size=8)
            
            # Should return whatever is possible or empty
            assert isinstance(result, dict)


class TestCreateStratifiedSplit:
    """Tests for create_stratified_split function."""

    def test_returns_train_test_split(self):
        """Test that create_stratified_split returns proper train/test splits."""
        # Create a small mock dataset
        species_list = ["Species_A", "Species_B", "Species_C", "Species_D", "Species_E"]
        clade_map = {
            "Clade_1": ["Species_A", "Species_B", "Species_C"],
            "Clade_2": ["Species_D", "Species_E"]
        }
        
        # Mock the clade finding function
        with patch('modeling.train.find_balanced_clades') as mock_find:
            mock_find.return_value = clade_map
            
            train_df, test_df = create_stratified_split(
                species_list=species_list,
                test_size=0.2,
                min_clade_size=1,
                max_clade_size=10
            )
            
            # Verify return types
            assert isinstance(train_df, pd.DataFrame)
            assert isinstance(test_df, pd.DataFrame)
            
            # Verify that train and test don't overlap
            train_species = set(train_df['species'])
            test_species = set(test_df['species'])
            assert len(train_species.intersection(test_species)) == 0, \
                "Train and test sets should not overlap"

    def test_respects_test_size(self):
        """Test that the split approximately respects the test_size parameter."""
        species_list = [f"Species_{i}" for i in range(100)]
        clade_map = {
            "Clade_1": species_list[:50],
            "Clade_2": species_list[50:]
        }
        
        with patch('modeling.train.find_balanced_clades') as mock_find:
            mock_find.return_value = clade_map
            
            train_df, test_df = create_stratified_split(
                species_list=species_list,
                test_size=0.3,
                min_clade_size=1,
                max_clade_size=100
            )
            
            total = len(train_df) + len(test_df)
            test_ratio = len(test_df) / total
            
            # Allow some tolerance due to clade-based splitting
            assert 0.2 <= test_ratio <= 0.4, \
                f"Test ratio {test_ratio} should be approximately 0.3"

    def test_preserves_species_in_splits(self):
        """Test that all species are accounted for in the splits."""
        species_list = ["Species_A", "Species_B", "Species_C", "Species_D"]
        clade_map = {
            "Clade_1": ["Species_A", "Species_B"],
            "Clade_2": ["Species_C", "Species_D"]
        }
        
        with patch('modeling.train.find_balanced_clades') as mock_find:
            mock_find.return_value = clade_map
            
            train_df, test_df = create_stratified_split(
                species_list=species_list,
                test_size=0.5,
                min_clade_size=1,
                max_clade_size=10
            )
            
            all_species = set(train_df['species'].tolist()) | set(test_df['species'].tolist())
            assert all_species == set(species_list), \
                "All species should be present in either train or test set"

    def test_raises_error_on_empty_clades(self):
        """Test that appropriate errors are raised for invalid inputs."""
        # Test with empty species list
        with pytest.raises((StratifiedSplitError, ValueError)):
            create_stratified_split(
                species_list=[],
                test_size=0.2,
                min_clade_size=1,
                max_clade_size=10
            )

    def test_handles_single_clade(self):
        """Test behavior when all species belong to a single clade."""
        species_list = ["Species_A", "Species_B", "Species_C", "Species_D", "Species_E"]
        clade_map = {
            "Clade_1": species_list
        }
        
        with patch('modeling.train.find_balanced_clades') as mock_find:
            mock_find.return_value = clade_map
            
            # Should still produce a split, even if one clade
            train_df, test_df = create_stratified_split(
                species_list=species_list,
                test_size=0.2,
                min_clade_size=1,
                max_clade_size=10
            )
            
            assert len(train_df) + len(test_df) == len(species_list)

    def test_stratification_preserves_clade_structure(self):
        """Test that entire clades are kept together (no species from same clade in both sets)."""
        species_list = ["Species_A", "Species_B", "Species_C", "Species_D", "Species_E", "Species_F"]
        clade_map = {
            "Clade_1": ["Species_A", "Species_B"],
            "Clade_2": ["Species_C", "Species_D"],
            "Clade_3": ["Species_E", "Species_F"]
        }
        
        with patch('modeling.train.find_balanced_clades') as mock_find:
            mock_find.return_value = clade_map
            
            train_df, test_df = create_stratified_split(
                species_list=species_list,
                test_size=0.33,
                min_clade_size=1,
                max_clade_size=10
            )
            
            train_species = set(train_df['species'].tolist())
            test_species = set(test_df['species'].tolist())
            
            # Check that no clade is split between train and test
            for clade_name, members in clade_map.items():
                in_train = [s for s in members if s in train_species]
                in_test = [s for s in members if s in test_species]
                
                # Either all members are in train, all in test, or none (if filtered)
                # But not split between both
                assert not (in_train and in_test), \
                    f"Clade {clade_name} is split between train and test sets"