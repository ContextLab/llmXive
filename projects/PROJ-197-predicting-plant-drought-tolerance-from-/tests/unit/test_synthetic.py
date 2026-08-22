"""
Unit tests for synthetic data generation (T012).
"""
import os
import sys
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.generate import generate_synthetic_genomic_features, generate_synthetic_phylogenetic_matrix
from code.config import get_config

class TestSyntheticGenomics:
    """Tests for T012: Synthetic genomic feature generation."""

    def test_gene_list_count(self):
        """Verify the gene list has exactly 20 genes as specified."""
        config = get_config()
        gene_list = config.get('gene_list', [
            'NCED3', 'ABF3', 'P5CS', 'DREB2A', 'ERF1', 'ABI5', 'RD29A', 
            'COR15A', 'LEA3', 'HSP70', 'SOD', 'APX1', 'CAT1', 'GPX1', 
            'MDHAR', 'DHAR', 'GSTU', 'ZAT12', 'WRKY33', 'MYB96'
        ])
        assert len(gene_list) == 20, f"Expected 20 genes, got {len(gene_list)}"

    def test_seed_reproducibility(self):
        """Verify that random_state=42 produces consistent results."""
        species_list = [f"Species_{i}" for i in range(10)]
        gene_list = ['A', 'B', 'C', 'D', 'E']
        
        df1, labels1 = generate_synthetic_genomic_features(
            species_list, gene_list, random_state=42
        )
        df2, labels2 = generate_synthetic_genomic_features(
            species_list, gene_list, random_state=42
        )
        
        pd.testing.assert_frame_equal(df1, df2)
        np.testing.assert_array_equal(labels1, labels2)

    def test_label_logic_threshold(self):
        """Verify label = 1 if sum >= 12, else 0."""
        # Manually construct a scenario where we know the sum
        species_list = ["S1", "S2"]
        gene_list = [f"Gene_{i}" for i in range(20)]
        
        # We can't easily force specific values without mocking, 
        # but we can verify the column exists and is binary
        df, labels = generate_synthetic_genomic_features(species_list, gene_list, random_state=42)
        
        assert 'label' in df.columns
        assert set(labels).issubset({0, 1})
        
        # Verify the logic manually on a small subset if possible, 
        # but primarily ensure the calculation exists
        row_sums = df[gene_list].sum(axis=1)
        expected_labels = (row_sums >= 12).astype(int).values
        np.testing.assert_array_equal(labels, expected_labels)

    def test_output_shape(self):
        """Verify output shape matches input species count."""
        n_species = 50
        species_list = [f"Species_{i}" for i in range(n_species)]
        gene_list = ['A', 'B', 'C']
        
        df, labels = generate_synthetic_genomic_features(species_list, gene_list, random_state=42)
        
        assert len(df) == n_species
        assert len(labels) == n_species
        assert df.shape[1] == len(gene_list) + 1  # +1 for species_id

class TestPhylogeneticMatrix:
    """Tests for T016: Synthetic phylogenetic matrix generation."""

    def test_symmetry(self):
        """Verify the matrix is symmetric."""
        species_list = [f"Species_{i}" for i in range(10)]
        matrix = generate_synthetic_phylogenetic_matrix(species_list, random_state=42)
        
        np.testing.assert_array_almost_equal(matrix, matrix.T)

    def test_diagonal_zeros(self):
        """Verify diagonal elements are zero."""
        species_list = [f"Species_{i}" for i in range(10)]
        matrix = generate_synthetic_phylogenetic_matrix(species_list, random_state=42)
        
        np.testing.assert_array_almost_equal(np.diag(matrix), np.zeros(len(species_list)))

    def test_bounds(self):
        """Verify off-diagonal elements are within bounds."""
        species_list = [f"Species_{i}" for i in range(10)]
        lower, upper = 0.2, 0.8
        matrix = generate_synthetic_phylogenetic_matrix(
            species_list, lower_bound=lower, upper_bound=upper, random_state=42
        )
        
        # Check off-diagonal elements
        for i in range(len(species_list)):
            for j in range(len(species_list)):
                if i != j:
                    assert lower <= matrix[i, j] <= upper