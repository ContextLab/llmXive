"""
Unit tests for diversity metric calculations in src/analysis/diversity.py.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the functions to test
from code.src.analysis.diversity import (
    calculate_shannon,
    calculate_simpson,
    calculate_chao1,
    calculate_bray_curtis,
    calculate_unifrac_weighted,
    calculate_alpha_beta_diversity
)

@pytest.fixture
def sample_otu_table():
    """Create a sample OTU table for testing."""
    data = {
        'species_A': [10, 5, 0, 20],
        'species_B': [5, 10, 5, 0],
        'species_C': [0, 5, 10, 5],
        'species_D': [5, 0, 5, 10]
    }
    index = ['sample_1', 'sample_2', 'sample_3', 'sample_4']
    return pd.DataFrame(data, index=index)

@pytest.fixture
def empty_otu_table():
    """Create an empty OTU table."""
    return pd.DataFrame()

@pytest.fixture
def single_species_table():
    """Create a table with only one species (zero diversity)."""
    data = {
        'species_A': [10, 20, 30]
    }
    index = ['sample_1', 'sample_2', 'sample_3']
    return pd.DataFrame(data, index=index)

class TestAlphaDiversity:
    def test_calculate_shannon_normal_data(self, sample_otu_table):
        """Test Shannon calculation on normal data."""
        result = calculate_shannon(sample_otu_table)
        assert len(result) == 4
        assert all(result >= 0), "Shannon index must be non-negative"
        # Sample 1 has equal distribution (20 total, 5 each) -> max diversity
        # Sample 3 has unequal distribution -> lower diversity
        assert result['sample_1'] > result['sample_3']

    def test_calculate_shannon_empty_table(self, empty_otu_table):
        """Test Shannon calculation on empty table."""
        result = calculate_shannon(empty_otu_table)
        assert len(result) == 0

    def test_calculate_shannon_single_species(self, single_species_table):
        """Test Shannon calculation on single species (should be 0)."""
        result = calculate_shannon(single_species_table)
        # Shannon for single species is 0
        assert all(result == 0), "Shannon index for single species should be 0"

    def test_calculate_simpson_normal_data(self, sample_otu_table):
        """Test Simpson calculation on normal data."""
        result = calculate_simpson(sample_otu_table)
        assert len(result) == 4
        assert all(result >= 0) and all(result <= 1), "Simpson diversity (1-D) must be between 0 and 1"

    def test_calculate_simpson_empty_table(self, empty_otu_table):
        """Test Simpson calculation on empty table."""
        result = calculate_simpson(empty_otu_table)
        assert len(result) == 0

    def test_calculate_simpson_single_species(self, single_species_table):
        """Test Simpson calculation on single species (should be 0)."""
        result = calculate_simpson(single_species_table)
        assert all(result == 0), "Simpson diversity for single species should be 0"

    def test_calculate_chao1_normal_data(self, sample_otu_table):
        """Test Chao1 calculation on normal data."""
        result = calculate_chao1(sample_otu_table)
        assert len(result) == 4
        assert all(result >= 0), "Chao1 richness must be non-negative"
        # Chao1 should be at least the observed species count
        observed = (sample_otu_table > 0).sum(axis=1)
        assert all(result >= observed), "Chao1 should be >= observed species"

    def test_calculate_chao1_empty_table(self, empty_otu_table):
        """Test Chao1 calculation on empty table."""
        result = calculate_chao1(empty_otu_table)
        assert len(result) == 0

    def test_calculate_chao1_singletons_doubletons(self):
        """Test Chao1 with specific singleton/doubleton counts."""
        # Create a table with known F1 and F2
        data = {
            'sp1': [1, 0, 0],
            'sp2': [1, 0, 0],
            'sp3': [2, 0, 0],
            'sp4': [2, 0, 0],
            'sp5': [3, 0, 0]
        }
        df = pd.DataFrame(data, index=['s1', 's2', 's3'])
        # s1: F1=2, F2=2 -> Chao1 = 5 + (4 / 4) = 6
        result = calculate_chao1(df)
        assert result['s1'] == 6.0

class TestBetaDiversity:
    def test_calculate_bray_curtis_normal_data(self, sample_otu_table):
        """Test Bray-Curtis calculation."""
        result = calculate_bray_curtis(sample_otu_table)
        assert result.shape == (4, 4)
        assert all(result.values >= 0) and all(result.values <= 1)
        # Diagonal should be 0 (distance to self)
        assert all(np.diag(result.values) == 0)

    def test_calculate_bray_curtis_empty_table(self, empty_otu_table):
        """Test Bray-Curtis on empty table."""
        result = calculate_bray_curtis(empty_otu_table)
        assert result.empty

    def test_calculate_bray_curtis_identical_samples(self):
        """Test Bray-Curtis with identical samples (should be 0)."""
        data = {
            'sp1': [10, 10],
            'sp2': [5, 5]
        }
        df = pd.DataFrame(data, index=['s1', 's2'])
        result = calculate_bray_curtis(df)
        assert result['s1']['s2'] == 0.0

    def test_calculate_unifrac_weighted_no_tree(self, sample_otu_table):
        """Test UniFrac without a tree (should fallback to Bray-Curtis)."""
        result = calculate_unifrac_weighted(sample_otu_table, tree_path=None)
        # Should return a Bray-Curtis-like matrix
        assert result.shape == (4, 4)
        assert all(result.values >= 0)

    def test_calculate_unifrac_weighted_missing_tree(self, sample_otu_table):
        """Test UniFrac with a non-existent tree path."""
        fake_path = Path("/nonexistent/tree.nwk")
        result = calculate_unifrac_weighted(sample_otu_table, tree_path=fake_path)
        assert result.shape == (4, 4)

class TestIntegration:
    def test_calculate_alpha_beta_diversity(self, sample_otu_table, tmp_path):
        """Test the full pipeline of diversity calculation."""
        results = calculate_alpha_beta_diversity(
            sample_otu_table,
            output_dir=tmp_path,
            tree_path=None
        )

        assert 'shannon' in results
        assert 'simpson' in results
        assert 'chao1' in results
        assert 'bray_curtis' in results
        assert 'unifrac_weighted' in results

        # Check files were created
        assert (tmp_path / "alpha_diversity.csv").exists()
        assert (tmp_path / "bray_curtis_distance.csv").exists()
        # UniFrac fallback creates the same file as Bray-Curtis in this test context
        # or we check if it exists if not empty
        if not results['unifrac_weighted'].empty:
            assert (tmp_path / "unifrac_weighted_distance.csv").exists()

    def test_diversity_with_zero_variance(self):
        """Test diversity calculation with zero variance (constant counts)."""
        data = {
            'sp1': [10, 10, 10],
            'sp2': [10, 10, 10]
        }
        df = pd.DataFrame(data, index=['s1', 's2', 's3'])
        shannon = calculate_shannon(df)
        # If all counts are equal, diversity is max for that richness
        # But if only 1 species has non-zero, diversity is 0
        # Here we have 2 species, equal counts -> non-zero diversity
        assert all(shannon > 0)

        simpson = calculate_simpson(df)
        assert all(simpson > 0)
        assert all(simpson < 1)
