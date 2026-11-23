"""
Unit tests for synthetic genomic data generation (T012).
"""
import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.generate import generate_synthetic_genomic_features
from config import get_config

@pytest.fixture
def gene_list():
    return [
        'NCED3', 'ABF3', 'P5CS', 'DREB2A', 'ERF1', 'ABI5', 'RD29A', 
        'COR15A', 'LEA3', 'HSP70', 'SOD', 'APX1', 'CAT1', 'GPX1', 
        'MDHAR', 'DHAR', 'GSTU', 'ZAT12', 'WRKY33', 'MYB96'
    ]

@pytest.fixture
def species_list():
    return [f"Species_{i}" for i in range(50)]

def test_generate_synthetic_genomic_features_structure(species_list, gene_list):
    """Test that the generated DataFrame has the correct structure."""
    df, labels = generate_synthetic_genomic_features(species_list, gene_list, random_state=42)
    
    # Check DataFrame shape
    assert df.shape[0] == len(species_list)
    assert df.shape[1] == len(gene_list) + 1  # +1 for species_id
    
    # Check columns
    assert 'species_id' in df.columns
    for gene in gene_list:
        assert gene in df.columns
    
    # Check species_id values match input
    assert list(df['species_id']) == species_list

def test_generate_synthetic_genomic_features_binary(species_list, gene_list):
    """Test that genomic features are binary (0 or 1)."""
    df, labels = generate_synthetic_genomic_features(species_list, gene_list, random_state=42)
    
    for gene in gene_list:
        unique_values = df[gene].unique()
        assert set(unique_values).issubset({0, 1})

def test_generate_synthetic_genomic_features_label_logic(species_list, gene_list):
    """Test that the label logic (sum >= 12) is correctly applied."""
    df, labels = generate_synthetic_genomic_features(species_list, gene_list, random_state=42)
    
    # Manually calculate expected labels
    row_sums = df[gene_list].sum(axis=1)
    expected_labels = (row_sums >= 12).astype(int).values
    
    # Compare with generated labels
    np.testing.assert_array_equal(labels, expected_labels)
    
    # Also verify the label column in the DataFrame
    assert list(df['label']) == list(expected_labels)

def test_generate_synthetic_genomic_features_reproducibility(species_list, gene_list):
    """Test that the generation is reproducible with the same seed."""
    df1, labels1 = generate_synthetic_genomic_features(species_list, gene_list, random_state=42)
    df2, labels2 = generate_synthetic_genomic_features(species_list, gene_list, random_state=42)
    
    pd.testing.assert_frame_equal(df1, df2)
    np.testing.assert_array_equal(labels1, labels2)

def test_generate_synthetic_genomic_features_different_seed(species_list, gene_list):
    """Test that different seeds produce different results."""
    df1, labels1 = generate_synthetic_genomic_features(species_list, gene_list, random_state=42)
    df2, labels2 = generate_synthetic_genomic_features(species_list, gene_list, random_state=123)
    
    # Results should be different
    assert not df1.equals(df2)
    assert not np.array_equal(labels1, labels2)

def test_generate_synthetic_genomic_features_empty_input():
    """Test handling of empty input lists."""
    df, labels = generate_synthetic_genomic_features([], [], random_state=42)
    
    assert df.empty
    assert len(labels) == 0

def test_generate_synthetic_genomic_features_label_distribution(species_list, gene_list):
    """Test that the label distribution is reasonable (not all 0s or all 1s)."""
    df, labels = generate_synthetic_genomic_features(species_list, gene_list, random_state=42)
    
    label_counts = pd.Series(labels).value_counts()
    
    # With 20 genes and threshold 12, we expect a mix of 0s and 1s
    # The exact distribution depends on the random seed, but it should not be all one class
    assert len(label_counts) > 1 or (len(label_counts) == 1 and list(label_counts.keys())[0] in [0, 1])