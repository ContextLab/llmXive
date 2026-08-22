"""
Unit tests for code/data/generate.py
"""
import os
import sys
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.generate import generate_synthetic_phylogenetic_matrix, generate_synthetic_genomic_features

class TestPhylogeneticMatrix:
    """Tests for generate_synthetic_phylogenetic_matrix"""

    def test_matrix_dimensions(self):
        """Test that the matrix is N x N"""
        species = ["A", "B", "C", "D"]
        matrix = generate_synthetic_phylogenetic_matrix(species, random_state=42)
        assert matrix.shape == (4, 4)

    def test_symmetric(self):
        """Test that the matrix is symmetric"""
        species = ["A", "B", "C", "D", "E"]
        matrix = generate_synthetic_phylogenetic_matrix(species, random_state=42)
        assert np.allclose(matrix, matrix.T)

    def test_diagonal_zero(self):
        """Test that diagonal elements are zero"""
        species = ["A", "B", "C"]
        matrix = generate_synthetic_phylogenetic_matrix(species, random_state=42)
        assert np.all(np.diag(matrix) == 0)

    def test_bounds(self):
        """Test that off-diagonal values are within bounds"""
        species = ["A", "B", "C", "D"]
        lower, upper = 0.2, 0.8
        matrix = generate_synthetic_phylogenetic_matrix(species, lower_bound=lower, upper_bound=upper, random_state=42)
        
        # Create a mask for off-diagonal elements
        mask = ~np.eye(4, dtype=bool)
        off_diag_values = matrix[mask]
        
        assert np.all(off_diag_values >= lower)
        assert np.all(off_diag_values <= upper)

    def test_empty_list(self):
        """Test behavior with empty species list"""
        matrix = generate_synthetic_phylogenetic_matrix([], random_state=42)
        assert matrix.shape == (0, 0)

    def test_single_species(self):
        """Test behavior with single species"""
        species = ["A"]
        matrix = generate_synthetic_phylogenetic_matrix(species, random_state=42)
        assert matrix.shape == (1, 1)
        assert matrix[0, 0] == 0

class TestSyntheticGenomics:
    """Tests for generate_synthetic_genomic_features"""

    def test_dataframe_shape(self):
        """Test that the dataframe has correct shape"""
        species = ["A", "B", "C"]
        genes = ["G1", "G2"]
        df, labels = generate_synthetic_genomic_features(species, genes, random_state=42)
        assert df.shape == (3, 3) # 2 genes + 1 species_id column
        assert len(labels) == 3

    def test_columns(self):
        """Test that columns include species_id and genes"""
        species = ["A"]
        genes = ["G1", "G2"]
        df, _ = generate_synthetic_genomic_features(species, genes, random_state=42)
        assert "species_id" in df.columns
        assert "G1" in df.columns
        assert "G2" in df.columns

    def test_binary_values(self):
        """Test that gene expression values are binary (0 or 1)"""
        species = ["A", "B"]
        genes = ["G1"]
        df, _ = generate_synthetic_genomic_features(species, genes, random_state=42)
        gene_col = df["G1"]
        assert all(gene_col.isin([0, 1]))

    def test_label_logic(self):
        """Test that label logic is correct: 1 if sum >= threshold, else 0"""
        # Use a small threshold for easier testing
        species = ["A", "B", "C"]
        genes = ["G1", "G2", "G3"]
        # We need to control the random seed to ensure specific sums
        # With seed 42, let's just verify the logic holds for the generated data
        df, labels = generate_synthetic_genomic_features(species, genes, random_state=42)
        
        # Recalculate expected labels
        gene_sums = df[genes].sum(axis=1)
        # Note: The function uses threshold 12 by default. 
        # For small gene lists (3 genes), sum will never reach 12.
        # So all labels should be 0 unless we change the function logic or use more genes.
        # Let's verify the function logic matches the requirement for a larger set.
        
        # Re-test with 20 genes to match the requirement
        genes_20 = [f"G{i}" for i in range(20)]
        df_20, labels_20 = generate_synthetic_genomic_features(species, genes_20, random_state=42)
        expected_labels = (df_20[genes_20].sum(axis=1) >= 12).astype(int)
        
        assert np.array_equal(labels_20, expected_labels.values)

    def test_empty_inputs(self):
        """Test behavior with empty lists"""
        df, labels = generate_synthetic_genomic_features([], ["G1"], random_state=42)
        assert df.empty
        assert len(labels) == 0

        df, labels = generate_synthetic_genomic_features(["A"], [], random_state=42)
        assert df.empty
        assert len(labels) == 0