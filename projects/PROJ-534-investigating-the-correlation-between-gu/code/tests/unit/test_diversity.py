"""
Unit tests for diversity metric calculations.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import logging

# Import the functions to test
from code.src.analysis.diversity import (
    calculate_shannon,
    calculate_simpson,
    calculate_chao1,
    calculate_bray_curtis,
    calculate_alpha_beta_diversity
)

logger = logging.getLogger(__name__)


@pytest.fixture
def sample_otu_table():
    """
    Create a simple OTU table for testing.
    Rows: Samples, Columns: OTUs
    """
    data = {
        'OTU_1': [10, 5, 0, 20],
        'OTU_2': [5, 5, 0, 5],
        'OTU_3': [0, 0, 0, 5],
        'OTU_4': [5, 10, 0, 0]
    }
    index = ['Sample_1', 'Sample_2', 'Sample_3', 'Sample_4']
    return pd.DataFrame(data, index=index)


@pytest.fixture
def empty_otu_table():
    """
    Create an OTU table with all zeros.
    """
    data = {
        'OTU_1': [0, 0],
        'OTU_2': [0, 0]
    }
    index = ['Empty_1', 'Empty_2']
    return pd.DataFrame(data, index=index)


@pytest.fixture
def single_species_table():
    """
    Table with only one species present.
    """
    data = {
        'OTU_1': [10, 20],
        'OTU_2': [0, 0]
    }
    index = ['Single_1', 'Single_2']
    return pd.DataFrame(data, index=index)


class TestAlphaDiversity:
    def test_shannon_calculation(self, sample_otu_table):
        """Test Shannon diversity calculation."""
        result = calculate_shannon(sample_otu_table)
        assert len(result) == 4
        # Sample_3 has all zeros, should be NaN
        assert pd.isna(result['Sample_3'])
        # Sample_1: 10, 5, 0, 5 -> Total 20. Probs: 0.5, 0.25, 0, 0.25
        # H = -(0.5*ln(0.5) + 0.25*ln(0.25) + 0.25*ln(0.25))
        #   = -(-0.3465 - 0.3465 - 0.3465) = 1.039
        expected_s1 = - (0.5 * np.log(0.5) + 0.25 * np.log(0.25) + 0.25 * np.log(0.25))
        assert np.isclose(result['Sample_1'], expected_s1)

    def test_simpson_calculation(self, sample_otu_table):
        """Test Simpson diversity (1-D) calculation."""
        result = calculate_simpson(sample_otu_table)
        assert len(result) == 4
        assert pd.isna(result['Sample_3'])
        # Sample_1: D = 0.5^2 + 0.25^2 + 0.25^2 = 0.25 + 0.0625 + 0.0625 = 0.375
        # 1-D = 0.625
        expected_s1 = 1.0 - (0.5**2 + 0.25**2 + 0.25**2)
        assert np.isclose(result['Sample_1'], expected_s1)

    def test_chao1_calculation(self, sample_otu_table):
        """Test Chao1 richness estimation."""
        result = calculate_chao1(sample_otu_table)
        assert len(result) == 4
        assert pd.isna(result['Sample_3'])

    def test_empty_otu_table(self, empty_otu_table):
        """Test handling of empty tables."""
        shannon = calculate_shannon(empty_otu_table)
        simpson = calculate_simpson(empty_otu_table)
        chao1 = calculate_chao1(empty_otu_table)

        assert all(pd.isna(shannon))
        assert all(pd.isna(simpson))
        assert all(pd.isna(chao1))

    def test_single_species(self, single_species_table):
        """Test metrics when only one species is present."""
        shannon = calculate_shannon(single_species_table)
        simpson = calculate_simpson(single_species_table)

        # Shannon should be 0 (only one species, p=1, ln(1)=0)
        assert np.isclose(shannon['Single_1'], 0.0)
        assert np.isclose(shannon['Single_2'], 0.0)

        # Simpson (1-D) should be 0 (D=1)
        assert np.isclose(simpson['Single_1'], 0.0)
        assert np.isclose(simpson['Single_2'], 0.0)


class TestBetaDiversity:
    def test_bray_curtis_symmetry(self, sample_otu_table):
        """Test that Bray-Curtis matrix is symmetric."""
        result = calculate_bray_curtis(sample_otu_table)
        assert result.equals(result.T)

    def test_bray_curtis_diagonal(self, sample_otu_table):
        """Test that diagonal of Bray-Curtis is 0."""
        result = calculate_bray_curtis(sample_otu_table)
        np.testing.assert_array_almost_equal(np.diag(result.values), np.zeros(len(result)))

    def test_bray_curtis_range(self, sample_otu_table):
        """Test that Bray-Curtis values are between 0 and 1."""
        result = calculate_bray_curtis(sample_otu_table)
        assert (result >= 0).all().all()
        assert (result <= 1).all().all()

    def test_identical_samples(self):
        """Test Bray-Curtis for identical samples."""
        data = {
            'OTU_1': [10, 10],
            'OTU_2': [5, 5]
        }
        df = pd.DataFrame(data, index=['A', 'B'])
        result = calculate_bray_curtis(df)
        # Distance between A and B should be 0
        assert np.isclose(result.loc['A', 'B'], 0.0)

    def test_disjoint_samples(self):
        """Test Bray-Curtis for completely different samples."""
        data = {
            'OTU_1': [10, 0],
            'OTU_2': [0, 10]
        }
        df = pd.DataFrame(data, index=['A', 'B'])
        result = calculate_bray_curtis(df)
        # Distance should be 1
        assert np.isclose(result.loc['A', 'B'], 1.0)


class TestIntegration:
    def test_calculate_alpha_beta_diversity(self, sample_otu_table, tmp_path):
        """Test the main integration function."""
        # Create a mock cohort file
        cohort_df = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'age': [65, 70, 68, 72],
            'OTU_1': [10, 5, 0, 20],
            'OTU_2': [5, 5, 0, 5],
            'OTU_3': [0, 0, 0, 5],
            'OTU_4': [5, 10, 0, 0]
        })
        cohort_path = tmp_path / "filtered_cohort.csv"
        cohort_df.to_csv(cohort_path, index=False)

        output_dir = tmp_path / "results"

        alpha_metrics, beta_metrics = calculate_alpha_beta_diversity(
            cohort_path=cohort_path,
            otu_column_prefix="OTU_",
            output_dir=output_dir
        )

        # Check output files exist
        assert (output_dir / "alpha_diversity.csv").exists()
        assert (output_dir / "beta_diversity_bray_curtis.csv").exists()

        # Check alpha metrics content
        assert 'shannon' in alpha_metrics.columns
        assert 'simpson' in alpha_metrics.columns
        assert 'chao1' in alpha_metrics.columns
        assert len(alpha_metrics) == 4

        # Check beta metrics content
        assert len(beta_metrics) == 4
        assert list(beta_metrics.index) == ['Sample_1', 'Sample_2', 'Sample_3', 'Sample_4']