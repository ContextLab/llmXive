import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.src.analysis.diversity import (
    calculate_shannon,
    calculate_simpson,
    calculate_chao1,
    calculate_bray_curtis,
    calculate_alpha_beta_diversity
)

@pytest.fixture
def sample_otu_table():
    """Create a sample OTU table for testing."""
    data = {
        'participant_id': ['P001', 'P002', 'P003'],
        'otu_1': [10, 5, 0],
        'otu_2': [5, 10, 0],
        'otu_3': [0, 0, 15]
    }
    return pd.DataFrame(data)

@pytest.fixture
def empty_otu_table():
    """Create an empty OTU table."""
    data = {
        'participant_id': ['P001'],
        'otu_1': [0],
        'otu_2': [0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def single_species_table():
    """Create a table with only one species present."""
    data = {
        'participant_id': ['P001'],
        'otu_1': [100],
        'otu_2': [0],
        'otu_3': [0]
    }
    return pd.DataFrame(data)

class TestAlphaDiversity:
    def test_calculate_shannon_basic(self):
        """Test Shannon diversity calculation with known values."""
        # Equal abundance: 10, 10, 10 -> Shannon = ln(3) ≈ 1.0986
        otu_row = pd.Series([10, 10, 10])
        result = calculate_shannon(otu_row)
        expected = np.log(3)
        assert np.isclose(result, expected, rtol=1e-5)

    def test_calculate_shannon_zero(self):
        """Test Shannon diversity with all zeros."""
        otu_row = pd.Series([0, 0, 0])
        result = calculate_shannon(otu_row)
        assert result == 0.0

    def test_calculate_simpson_basic(self):
        """Test Simpson diversity calculation."""
        # Equal abundance: 10, 10, 10 -> Simpson = 1 - 3*(1/3)^2 = 1 - 1/3 = 0.6667
        otu_row = pd.Series([10, 10, 10])
        result = calculate_simpson(otu_row)
        expected = 1 - (1/3)
        assert np.isclose(result, expected, rtol=1e-5)

    def test_calculate_simpson_zero(self):
        """Test Simpson diversity with all zeros."""
        otu_row = pd.Series([0, 0, 0])
        result = calculate_simpson(otu_row)
        assert result == 0.0

    def test_calculate_chao1_with_doubletons(self):
        """Test Chao1 with singletons and doubletons."""
        # S_obs = 3, F1 = 1, F2 = 1 -> Chao1 = 3 + (1^2)/(2*1) = 3.5
        otu_row = pd.Series([1, 2, 10])  # 1 singleton, 1 doubleton, 1 abundant
        result = calculate_chao1(otu_row)
        expected = 3.5
        assert np.isclose(result, expected, rtol=1e-5)

    def test_calculate_chao1_no_doubletons(self):
        """Test Chao1 when no doubletons exist."""
        # S_obs = 2, F1 = 2, F2 = 0 -> Chao1 = 2 + 2 = 4
        otu_row = pd.Series([1, 1, 0])
        result = calculate_chao1(otu_row)
        expected = 4.0
        assert np.isclose(result, expected, rtol=1e-5)

class TestBetaDiversity:
    def test_calculate_bray_curtis_identical(self):
        """Test Bray-Curtis with identical samples (should be 0)."""
        df = pd.DataFrame({
            'otu_1': [10, 10],
            'otu_2': [5, 5]
        })
        bc_matrix = calculate_bray_curtis(df, ['otu_1', 'otu_2'])
        assert bc_matrix.iloc[0, 0] == 0.0
        assert bc_matrix.iloc[1, 1] == 0.0

    def test_calculate_bray_curtis_completely_different(self):
        """Test Bray-Curtis with completely non-overlapping samples."""
        df = pd.DataFrame({
            'otu_1': [10, 0],
            'otu_2': [0, 10]
        })
        bc_matrix = calculate_bray_curtis(df, ['otu_1', 'otu_2'])
        # BC = 1 - (2*0)/(10+10) = 1.0
        assert np.isclose(bc_matrix.iloc[0, 1], 1.0, rtol=1e-5)

    def test_calculate_bray_curtis_symmetric(self):
        """Test that Bray-Curtis matrix is symmetric."""
        df = pd.DataFrame({
            'otu_1': [10, 5],
            'otu_2': [5, 10]
        })
        bc_matrix = calculate_bray_curtis(df, ['otu_1', 'otu_2'])
        assert np.isclose(bc_matrix.iloc[0, 1], bc_matrix.iloc[1, 0], rtol=1e-5)

class TestIntegration:
    def test_calculate_alpha_beta_diversity(self, sample_otu_table):
        """Test full alpha and beta diversity calculation pipeline."""
        alpha_metrics, beta_metrics = calculate_alpha_beta_diversity(
            sample_otu_table,
            ['otu_1', 'otu_2', 'otu_3']
        )
        
        # Check alpha metrics
        assert 'shannon_diversity' in alpha_metrics.columns
        assert 'simpson_diversity' in alpha_metrics.columns
        assert 'chao1' in alpha_metrics.columns
        assert len(alpha_metrics) == 3
        
        # Check beta metrics
        assert 'bray_curtis' in beta_metrics
        assert 'unifrac_weighted' in beta_metrics
        
        # Check dimensions
        assert beta_metrics['bray_curtis'].shape == (3, 3)
        assert beta_metrics['unifrac_weighted'].shape == (3, 3)

    def test_calculate_alpha_beta_diversity_empty(self, empty_otu_table):
        """Test diversity calculation with empty OTU table."""
        alpha_metrics, beta_metrics = calculate_alpha_beta_diversity(
            empty_otu_table,
            ['otu_1', 'otu_2']
        )
        
        # Should handle zeros gracefully
        assert alpha_metrics['shannon_diversity'].iloc[0] == 0.0
        assert alpha_metrics['simpson_diversity'].iloc[0] == 0.0

    def test_calculate_alpha_beta_diversity_single_species(self, single_species_table):
        """Test diversity calculation with single species."""
        alpha_metrics, beta_metrics = calculate_alpha_beta_diversity(
            single_species_table,
            ['otu_1', 'otu_2', 'otu_3']
        )
        
        # Single species: Shannon = 0, Simpson = 0
        assert alpha_metrics['shannon_diversity'].iloc[0] == 0.0
        assert alpha_metrics['simpson_diversity'].iloc[0] == 0.0
        # Chao1 = S_obs + F1 = 1 + 0 = 1 (if no singletons) or 1 + 1 = 2 (if singleton)
        # In this case: [100, 0, 0] -> S_obs=1, F1=0, F2=0 -> Chao1 = 1
        assert alpha_metrics['chao1'].iloc[0] == 1.0
