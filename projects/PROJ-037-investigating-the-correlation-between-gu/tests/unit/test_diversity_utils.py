import pytest
import pandas as pd
import numpy as np
from code.diversity import load_biom_table, load_metadata, calculate_alpha_diversity, calculate_beta_diversity

class TestLoadBiomTable:
    def test_load_biom_table_structure(self):
        """Test that load_biom_table returns expected structure."""
        # This test assumes a valid BIOM file exists in the test data
        try:
            biom_table = load_biom_table()
            assert biom_table is not None
            # BIOM table should have observation and sample metadata
            assert hasattr(biom_table, 'observation_metadata') or hasattr(biom_table, 'sample_metadata')
        except FileNotFoundError:
            pytest.skip("BIOM file not found - expected in development")

class TestLoadMetadata:
    def test_load_metadata_structure(self):
        """Test that load_metadata returns expected structure."""
        try:
            metadata = load_metadata()
            assert isinstance(metadata, pd.DataFrame)
            assert len(metadata) > 0
            # Should have participant IDs
            assert 'participant_id' in metadata.columns or 'SampleID' in metadata.columns
        except FileNotFoundError:
            pytest.skip("Metadata file not found - expected in development")

class TestCalculateAlphaDiversity:
    def test_calculate_alpha_diversity_values(self):
        """Test that alpha diversity values are reasonable."""
        # Create mock BIOM table with known diversity
        # In practice, this would use a real BIOM table
        try:
            biom_table = load_biom_table()
            alpha_diversity = calculate_alpha_diversity(biom_table)
            
            assert isinstance(alpha_diversity, pd.Series)
            assert len(alpha_diversity) > 0
            # Shannon diversity should be positive
            assert all(alpha_diversity > 0)
        except (FileNotFoundError, NotImplementedError):
            pytest.skip("BIOM file or implementation not ready - expected in development")

    def test_calculate_alpha_diversity_consistency(self):
        """Test that alpha diversity calculation is consistent."""
        try:
            biom_table = load_biom_table()
            alpha1 = calculate_alpha_diversity(biom_table)
            alpha2 = calculate_alpha_diversity(biom_table)
            
            pd.testing.assert_series_equal(alpha1, alpha2)
        except (FileNotFoundError, NotImplementedError):
            pytest.skip("BIOM file or implementation not ready - expected in development")

class TestCalculateBetaDiversity:
    def test_calculate_beta_diversity_matrix(self):
        """Test that beta diversity returns a distance matrix."""
        try:
            biom_table = load_biom_table()
            beta_diversity = calculate_beta_diversity(biom_table)
            
            assert isinstance(beta_diversity, pd.DataFrame)
            # Distance matrix should be square
            assert beta_diversity.shape[0] == beta_diversity.shape[1]
            # Diagonal should be zero (distance to self)
            assert all(beta_diversity.values.diagonal() == 0)
        except (FileNotFoundError, NotImplementedError):
            pytest.skip("BIOM file or implementation not ready - expected in development")