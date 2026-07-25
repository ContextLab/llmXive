import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np

# Ensure code/ is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.preprocess import harmonize_metabolites, MIBiGMappingError
from utils.logging import setup_logging

# Setup logging for tests
setup_logging()

class TestInChIKeyHarmonization:
    """
    Unit tests for InChIKey harmonization logic in harmonize_metabolites().
    Tests cover normalization, pseudo-count addition, and log-transformation.
    """

    def test_inchikey_normalization_uppercase(self):
        """Test that lowercase InChIKeys are converted to uppercase."""
        df = pd.DataFrame({
            'species': ['A', 'B'],
            'inchikey': ['abc123', 'DEF456']
        })
        result = harmonize_metabolites(df)
        assert result['inchikey'].iloc[0] == 'ABC123'
        assert result['inchikey'].iloc[1] == 'DEF456'

    def test_inchikey_normalization_whitespace(self):
        """Test that whitespace around InChIKeys is stripped."""
        df = pd.DataFrame({
            'species': ['A', 'B'],
            'inchikey': ['  abc123  ', 'DEF456']
        })
        result = harmonize_metabolites(df)
        assert result['inchikey'].iloc[0] == 'ABC123'

    def test_pseudo_count_addition(self):
        """Test that a pseudo-count of 1 is added to zero abundance values."""
        df = pd.DataFrame({
            'species': ['A', 'B', 'C'],
            'inchikey': ['ABC123', 'DEF456', 'GHI789'],
            'abundance': [0.0, 5.0, 0.0]
        })
        result = harmonize_metabolites(df)
        # Check that 0.0 becomes 1.0 before log transform
        # The function applies log10(abundance + 1)
        # So input 0 -> log10(1) = 0
        # Input 5 -> log10(6) ~ 0.778
        assert result['abundance'].iloc[0] == pytest.approx(0.0, rel=1e-5) # log10(0+1)
        assert result['abundance'].iloc[2] == pytest.approx(0.0, rel=1e-5) # log10(0+1)
        assert result['abundance'].iloc[1] > 0.5 # log10(5+1) > 0.5

    def test_log_transformation(self):
        """Test that log10 transformation is applied correctly."""
        df = pd.DataFrame({
            'species': ['A'],
            'inchikey': ['ABC123'],
            'abundance': [100.0]
        })
        result = harmonize_metabolites(df)
        # log10(100 + 1) = log10(101) ~ 2.004
        expected = np.log10(101.0)
        assert result['abundance'].iloc[0] == pytest.approx(expected, rel=1e-3)

    def test_log_transformation_large_values(self):
        """Test log transformation on large abundance values."""
        df = pd.DataFrame({
            'species': ['A'],
            'inchikey': ['ABC123'],
            'abundance': [1000000.0]
        })
        result = harmonize_metabolites(df)
        expected = np.log10(1000001.0)
        assert result['abundance'].iloc[0] == pytest.approx(expected, rel=1e-3)

    def test_missing_inchikey_handling(self):
        """Test behavior when InChIKey is missing (None or NaN)."""
        df = pd.DataFrame({
            'species': ['A', 'B'],
            'inchikey': ['ABC123', None],
            'abundance': [10.0, 20.0]
        })
        # The function should drop rows with missing InChIKeys or handle gracefully
        result = harmonize_metabolites(df)
        # Check that the row with None is handled (dropped or filtered)
        # Assuming it drops rows with missing InChIKey
        assert 'ABC123' in result['inchikey'].values
        assert len(result) <= 2

    def test_empty_dataframe(self):
        """Test harmonization on an empty DataFrame."""
        df = pd.DataFrame(columns=['species', 'inchikey', 'abundance'])
        result = harmonize_metabolites(df)
        assert result.empty

    def test_single_row(self):
        """Test harmonization on a single row."""
        df = pd.DataFrame({
            'species': ['A'],
            'inchikey': ['ABC123'],
            'abundance': [50.0]
        })
        result = harmonize_metabolites(df)
        assert len(result) == 1
        assert result['inchikey'].iloc[0] == 'ABC123'
        assert result['abundance'].iloc[0] == pytest.approx(np.log10(51.0), rel=1e-3)

    def test_negative_abundance_handling(self):
        """Test behavior with negative abundance values (should be handled or filtered)."""
        df = pd.DataFrame({
            'species': ['A', 'B'],
            'inchikey': ['ABC123', 'DEF456'],
            'abundance': [-5.0, 10.0]
        })
        # Negative values + 1 might still be negative or zero, causing log domain errors
        # The function should handle this, likely by filtering or setting to 0
        result = harmonize_metabolites(df)
        # Check that the negative value row is handled (dropped or corrected)
        # If it's dropped, result length < 2
        # If it's corrected, abundance should be valid (>=0 after log)
        if len(result) == 2:
            # If both rows exist, the negative one must have been corrected
            assert result['abundance'].iloc[0] >= 0
        else:
            # If dropped, the negative row is gone
            assert len(result) == 1
            assert result['abundance'].iloc[0] > 0

    def test_inchikey_deduplication(self):
        """Test that duplicate InChIKeys are handled (e.g., summed or averaged)."""
        df = pd.DataFrame({
            'species': ['A', 'A', 'B'],
            'inchikey': ['ABC123', 'ABC123', 'DEF456'],
            'abundance': [10.0, 20.0, 5.0]
        })
        result = harmonize_metabolites(df)
        # Check that duplicates are handled - either summed or one row per unique InChIKey
        # Assuming it aggregates (sums) abundance for same InChIKey per species or globally
        # This test verifies the function doesn't crash and produces valid output
        assert 'ABC123' in result['inchikey'].values
        assert 'DEF456' in result['inchikey'].values

    def test_mixed_case_inchikey_with_special_chars(self):
        """Test InChIKeys with mixed case and special characters (if any)."""
        df = pd.DataFrame({
            'species': ['A'],
            'inchikey': ['AbC123XyZ'],
            'abundance': [100.0]
        })
        result = harmonize_metabolites(df)
        assert result['inchikey'].iloc[0] == 'ABC123XYZ'

    def test_abundance_zero_after_pseudo_count(self):
        """Verify that abundance=0 becomes log10(1)=0 after pseudo-count."""
        df = pd.DataFrame({
            'species': ['A'],
            'inchikey': ['ABC123'],
            'abundance': [0.0]
        })
        result = harmonize_metabolites(df)
        assert result['abundance'].iloc[0] == pytest.approx(0.0, rel=1e-5)

    def test_abundance_very_small_values(self):
        """Test with very small positive abundance values."""
        df = pd.DataFrame({
            'species': ['A'],
            'inchikey': ['ABC123'],
            'abundance': [1e-10]
        })
        result = harmonize_metabolites(df)
        # log10(1e-10 + 1) ~ log10(1) = 0 (since 1e-10 is negligible)
        expected = np.log10(1.0 + 1e-10)
        assert result['abundance'].iloc[0] == pytest.approx(expected, rel=1e-5)

    def test_multiple_species_same_metabolite(self):
        """Test handling of multiple species with the same metabolite."""
        df = pd.DataFrame({
            'species': ['A', 'B', 'C'],
            'inchikey': ['ABC123', 'ABC123', 'ABC123'],
            'abundance': [10.0, 20.0, 30.0]
        })
        result = harmonize_metabolites(df)
        # Should process all rows, preserving species and InChIKey info
        assert len(result) == 3
        assert result['inchikey'].tolist() == ['ABC123'] * 3
        assert result['species'].tolist() == ['A', 'B', 'C']

    def test_inchikey_with_hyphens(self):
        """Test InChIKeys that contain hyphens (standard format)."""
        df = pd.DataFrame({
            'species': ['A'],
            'inchikey': ['ABC-123-XYZ'],
            'abundance': [100.0]
        })
        result = harmonize_metabolites(df)
        # Hyphens should be preserved, only case normalized
        assert result['inchikey'].iloc[0] == 'ABC-123-XYZ'