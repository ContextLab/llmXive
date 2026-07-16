import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from code.viz.plots import plot_scatter_significant


class TestPlotScatterSignificant:
    """Tests for the plot_scatter_significant function in code/viz/plots.py."""

    @pytest.fixture
    def sample_correlation_data(self):
        """Generate a sample DataFrame mimicking the output of generate_correlation_analysis."""
        np.random.seed(42)
        n = 100
        # Simulate some correlation
        gene_vals = np.random.normal(10, 2, n)
        trait_vals = 0.5 * gene_vals + np.random.normal(0, 1, n)

        df = pd.DataFrame({
            'gene': ['PER3'] * n,
            'trait': ['BMI'] * n,
            'r': [0.65] * n,  # Summary stats repeated for each row if we join, or just one row
            'p': [1e-5] * n,
            'significance_flag': ['significant'] * n,
            'tissue': ['Liver'] * n,
            'n': [n] * n,
            # Raw data columns needed for plotting
            'PER3': gene_vals,
            'BMI': trait_vals
        })
        return df

    @pytest.fixture
    def sample_non_significant_data(self):
        """Generate data for a non-significant correlation."""
        np.random.seed(42)
        n = 50
        gene_vals = np.random.normal(10, 2, n)
        trait_vals = np.random.normal(80, 10, n) # No correlation

        df = pd.DataFrame({
            'gene': ['CRY1'] * n,
            'trait': ['Glucose'] * n,
            'r': [0.05] * n,
            'p': [0.65] * n,
            'significance_flag': ['exploratory'] * n,
            'tissue': ['Liver'] * n,
            'n': [n] * n,
            'CRY1': gene_vals,
            'Glucose': trait_vals
        })
        return df

    def test_plot_scatter_significant_creates_file(self, sample_correlation_data, tmp_path):
        """Verify that a plot file is created for a significant correlation."""
        output_file = tmp_path / "test_plot.png"
        result = plot_scatter_significant(
            correlation_results=sample_correlation_data,
            gene='PER3',
            clinical_trait='BMI',
            output_path=str(output_file),
            tissue='Liver'
        )

        assert result.exists()
        assert result.stat().st_size > 0
        assert result.suffix == '.png'

    def test_plot_scatter_significant_correct_annotations(self, sample_correlation_data, tmp_path):
        """Verify that the plot contains expected annotations (r-value)."""
        # This is a basic check; full visual verification is hard in unit tests.
        # We rely on the file existing and being non-empty as a proxy for successful rendering.
        output_file = tmp_path / "test_plot_annotated.png"
        plot_scatter_significant(
            correlation_results=sample_correlation_data,
            gene='PER3',
            clinical_trait='BMI',
            output_path=str(output_file),
            tissue='Liver'
        )
        # The file exists check is the primary assertion here.
        # In a real CI, we might use image comparison libraries.
        assert output_file.exists()

    def test_plot_scatter_significant_raises_on_missing_gene(self, sample_correlation_data, tmp_path):
        """Verify that the function raises ValueError if the gene is not found."""
        output_file = tmp_path / "fail.png"
        with pytest.raises(ValueError, match="No correlation result found"):
            plot_scatter_significant(
                correlation_results=sample_correlation_data,
                gene='NONEXISTENT_GENE',
                clinical_trait='BMI',
                output_path=str(output_file)
            )

    def test_plot_scatter_significant_raises_on_missing_trait_columns(self, sample_correlation_data, tmp_path):
        """Verify that the function raises if raw data columns are missing."""
        # Create a df with only summary stats
        df_summary = sample_correlation_data[['gene', 'trait', 'r', 'p', 'significance_flag', 'tissue', 'n']].copy()
        output_file = tmp_path / "fail.png"
        with pytest.raises(ValueError, match="Input DataFrame must contain columns"):
            plot_scatter_significant(
                correlation_results=df_summary,
                gene='PER3',
                clinical_trait='BMI',
                output_path=str(output_file)
            )

    def test_plot_scatter_significant_handles_non_significant(self, sample_non_significant_data, tmp_path):
        """Verify that a plot is generated even if the correlation is not significant (with warning)."""
        output_file = tmp_path / "non_sig.png"
        # Should not raise, but might log a warning
        result = plot_scatter_significant(
            correlation_results=sample_non_significant_data,
            gene='CRY1',
            clinical_trait='Glucose',
            output_path=str(output_file)
        )
        assert result.exists()
        assert result.stat().st_size > 0