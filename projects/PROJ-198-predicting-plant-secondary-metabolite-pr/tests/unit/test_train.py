"""
Unit tests for phylogenetic stratified splitting logic (T022).
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path if running standalone
code_path = Path(__file__).parent.parent
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from modeling.train import create_stratified_split, StratifiedSplitError, get_clade_members, find_balanced_clades
import dendropy


@pytest.fixture
def sample_tree():
    """Create a simple Newick tree for testing."""
    # Tree structure: ((A,B),(C,D));
    # Clade 1: A, B
    # Clade 2: C, D
    newick = "((A:1,B:1)Clade1:1,(C:1,D:1)Clade2:1)Root;"
    tree = dendropy.Tree.get(
        data=newick,
        schema="newick",
        preserve_underscores=True
    )
    return tree


@pytest.fixture
def sample_data():
    """Create a sample dataframe with species matching the tree."""
    data = {
        'species': ['A', 'B', 'C', 'D'],
        'value': [10, 20, 30, 40],
        'feature1': [0.1, 0.2, 0.3, 0.4]
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_tree_file(sample_tree):
    """Write sample tree to a temporary file."""
    fd, path = tempfile.mkstemp(suffix='.nwk')
    with os.fdopen(fd, 'w') as f:
        f.write(str(sample_tree.as_newick_string()))
    return path


def test_get_clade_members(sample_tree):
    """Test that get_clade_members correctly retrieves tips from a clade."""
    # Find the root
    root = sample_tree.seed_node
    # Find the child clade that contains A and B
    # In the tree ((A,B),(C,D)), the root has two children.
    # One child is the clade (A,B).
    clade_ab = None
    for child in root.child_nodes():
        tips = [t.label for t in child.leaf_nodes()]
        if set(tips) == {'A', 'B'}:
            clade_ab = child
            break

    assert clade_ab is not None
    
    members = get_clade_members(sample_tree, clade_ab)
    assert set(members) == {'A', 'B'}


def test_find_balanced_clades(sample_tree):
    """Test that balanced clades are found correctly."""
    clades = find_balanced_clades(sample_tree, min_size=2)
    
    # We expect two clades: one with A,B and one with C,D
    # The order might vary
    all_members = []
    for clade in clades:
        all_members.extend(clade)
    
    assert set(all_members) == {'A', 'B', 'C', 'D'}
    assert len(clades) == 2
    for clade in clades:
        assert len(clade) == 2


def test_create_stratified_split_success(temp_tree_file, sample_data):
    """Test successful creation of a stratified split."""
    train_df, test_df = create_stratified_split(
        sample_data,
        phylogeny_path=temp_tree_file,
        test_size=0.5,
        random_state=42
    )
    
    # Check shapes
    assert len(train_df) + len(test_df) == len(sample_data)
    
    # Check that species are disjoint
    train_species = set(train_df['species'])
    test_species = set(test_df['species'])
    assert train_species.isdisjoint(test_species)
    
    # Check that all species are present
    assert train_species.union(test_species) == {'A', 'B', 'C', 'D'}


def test_create_stratified_split_missing_species(temp_tree_file, sample_data):
    """Test handling of species not in the tree."""
    data_with_extra = sample_data.copy()
    new_row = pd.DataFrame({'species': ['E'], 'value': [50], 'feature1': [0.5]})
    data_with_extra = pd.concat([data_with_extra, new_row], ignore_index=True)
    
    # Should not raise, but 'E' should be excluded or handled
    # Our implementation drops species not in tree for stratification
    train_df, test_df = create_stratified_split(
        data_with_extra,
        phylogeny_path=temp_tree_file,
        test_size=0.5,
        random_state=42
    )
    
    # 'E' should not be in either set
    assert 'E' not in train_df['species'].values
    assert 'E' not in test_df['species'].values
    assert len(train_df) + len(test_df) == 4


def test_create_stratified_split_insufficient_data(temp_tree_file):
    """Test error when not enough data."""
    data = pd.DataFrame({'species': ['A'], 'value': [10], 'feature1': [0.1]})
    
    with pytest.raises(StratifiedSplitError):
        create_stratified_split(
            data,
            phylogeny_path=temp_tree_file,
            test_size=0.5,
            random_state=42
        )


def test_create_stratified_split_no_tree_file():
    """Test error when tree file is missing."""
    data = pd.DataFrame({'species': ['A'], 'value': [10], 'feature1': [0.1]})
    
    with pytest.raises(StratifiedSplitError):
        create_stratified_split(
            data,
            phylogeny_path="nonexistent_tree.nwk",
            test_size=0.5,
            random_state=42
        )
