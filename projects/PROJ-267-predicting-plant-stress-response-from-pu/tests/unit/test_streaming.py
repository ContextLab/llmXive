"""
Unit tests for T040: Streaming Data Loading and Strict Error Handling.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import functions to test
from data_ingestion.download import validate_domain, download_file
from data_ingestion.normalize import apply_lcm_imputation, filter_low_abundance_proteins


class TestDomainValidation:
    """Tests for URL domain validation."""

    def test_valid_ncbi_domain(self):
        url = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE12345"
        assert validate_domain(url) is True

    def test_valid_proteomexchange_domain(self):
        url = "http://proteomexchange.org/cgi/GetDataset?ID=PXD000001"
        assert validate_domain(url) is True

    def test_valid_ebi_domain(self):
        url = "https://www.ebi.ac.uk/pride/archive/projects/PXD000001"
        assert validate_domain(url) is True

    def test_invalid_domain_raises(self):
        url = "https://malicious-site.com/data.csv"
        with pytest.raises(ValueError, match="Invalid domain"):
            validate_domain(url)

    def test_empty_string_raises(self):
        url = ""
        with pytest.raises(ValueError, match="Invalid domain"):
            validate_domain(url)


class TestLCMImputation:
    """Tests for Left-Censored Missing imputation logic."""

    def test_minprob_logic(self):
        """
        Test that MinProb imputes values below the minimum observed value.
        """
        data = pd.DataFrame({
            'protein_A': [10.0, 12.0, np.nan, 11.0],
            'protein_B': [5.0, np.nan, 5.5, 6.0]
        })
        result = apply_lcm_imputation(data)

        # Check that no NaNs remain
        assert result.isna().sum().sum() == 0

        # Check that imputed values are less than the min of the column
        # (MinProb logic: min - delta * std)
        min_A = data['protein_A'].dropna().min()
        imputed_A = result.loc[2, 'protein_A']
        assert imputed_A < min_A, f"Imputed value {imputed_A} should be < min {min_A}"

        min_B = data['protein_B'].dropna().min()
        imputed_B = result.loc[1, 'protein_B']
        assert imputed_B < min_B, f"Imputed value {imputed_B} should be < min {min_B}"

    def test_all_missing_column(self):
        """
        Test behavior when a column is entirely missing.
        """
        data = pd.DataFrame({
            'protein_A': [10.0, 12.0, 11.0],
            'protein_B': [np.nan, np.nan, np.nan]
        })
        result = apply_lcm_imputation(data)

        # Should fill with 0 as per custom implementation fallback
        assert result['protein_B'].iloc[0] == 0
        assert result.isna().sum().sum() == 0

    def test_zero_variance_column(self):
        """
        Test behavior when a column has zero variance.
        """
        data = pd.DataFrame({
            'protein_A': [10.0, 10.0, np.nan, 10.0]
        })
        result = apply_lcm_imputation(data)

        # Should impute with min_val (since std is 0)
        assert result['protein_A'].iloc[2] == 10.0


class TestFilterLowAbundance:
    """Tests for low abundance protein filtering."""

    def test_filter_threshold(self):
        # Create data where col A is 100% present, col B is 50% present, col C is 25% present
        data = pd.DataFrame({
            'A': [1.0, 2.0, 3.0],
            'B': [1.0, np.nan, 3.0],
            'C': [1.0, np.nan, np.nan]
        })

        # Threshold 0.5: A and B pass, C fails
        filtered, dropped = filter_low_abundance_proteins(data, min_detection_rate=0.5)

        assert 'A' in filtered.columns
        assert 'B' in filtered.columns
        assert 'C' not in filtered.columns
        assert dropped == ['C']

    def test_all_missing_dropped(self):
        data = pd.DataFrame({
            'A': [1.0, 2.0],
            'B': [np.nan, np.nan]
        })
        filtered, dropped = filter_low_abundance_proteins(data, min_detection_rate=0.5)

        assert 'B' not in filtered.columns
        assert dropped == ['B']
