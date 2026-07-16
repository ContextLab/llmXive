"""
Tests for correlation analysis in code/analysis/correlation.py
"""

import numpy as np
import pandas as pd
import pytest

from analysis.correlation import generate_correlation_analysis, _check_normality


class TestCheckNormality:
    def test_normal_distribution(self):
        # Generate normal data
        data = pd.Series(np.random.normal(0, 1, 100))
        is_normal, p = _check_normality(data)
        assert is_normal is True or p > 0.05  # Shapiro might vary, but likely normal

    def test_non_normal_distribution(self):
        # Generate exponential data (non-normal)
        data = pd.Series(np.random.exponential(1, 100))
        is_normal, p = _check_normality(data)
        # Exponential is strongly non-normal
        assert is_normal is False or p < 0.05

    def test_small_sample_size(self):
        # Small sample
        data = pd.Series([1, 2, 3])
        is_normal, p = _check_normality(data)
        assert is_normal is False
        assert p == 0.0  # Defined as 0.0 in implementation for small N

    def test_empty_data(self):
        data = pd.Series([])
        is_normal, p = _check_normality(data)
        assert is_normal is False


class TestGenerateCorrelationAnalysis:
    @pytest.fixture
    def sample_data(self):
        np.random.seed(42)
        n_samples = 100
        indices = [f"sample_{i}" for i in range(n_samples)]

        # Create expression data (genes PER1, PER2, CRY1)
        expression_df = pd.DataFrame(
            {
                "PER1": np.random.normal(10, 2, n_samples),
                "PER2": np.random.normal(12, 3, n_samples),
                "CRY1": np.random.normal(8, 1, n_samples),
                "NON_CIRCADIAN": np.random.normal(5, 1, n_samples),
            },
            index=indices
        )

        # Create phenotype data (BMI, Glucose)
        # Correlate PER1 with BMI
        bmi = expression_df["PER1"] * 0.5 + np.random.normal(25, 2, n_samples)
        glucose = expression_df["CRY1"] * -0.2 + np.random.normal(100, 10, n_samples)

        phenotype_df = pd.DataFrame(
            {
                "BMI": bmi,
                "Glucose": glucose,
                "BP": np.random.normal(120, 10, n_samples),
            },
            index=indices
        )

        return expression_df, phenotype_df

    def test_correlation_computation(self, sample_data):
        expr, pheno = sample_data
        gene_list = ["PER1", "PER2", "CRY1"]
        traits = ["BMI", "Glucose"]

        # Mock FDR table (PER1 is significant)
        fdr_df = pd.DataFrame(
            {"p_adj": [0.01, 0.2, 0.03]},
            index=["PER1", "PER2", "CRY1"]
        )

        result = generate_correlation_analysis(
            expression_df=expr,
            phenotype_df=pheno,
            gene_list=gene_list,
            trait_columns=traits,
            fdr_adjusted_pvalues=fdr_df
        )

        assert isinstance(result, pd.DataFrame)
        assert "gene" in result.columns
        assert "trait" in result.columns
        assert "r" in result.columns
        assert "p" in result.columns
        assert "significance_flag" in result.columns

        # Check specific results
        # PER1 vs BMI should be significant (based on mock FDR)
        per1_bmi = result[(result["gene"] == "PER1") & (result["trait"] == "BMI")]
        assert len(per1_bmi) == 1
        assert per1_bmi.iloc[0]["significance_flag"] == "significant"

        # PER2 vs BMI should be exploratory (FDR 0.2 > 0.05)
        per2_bmi = result[(result["gene"] == "PER2") & (result["trait"] == "BMI")]
        assert len(per2_bmi) == 1
        assert per2_bmi.iloc[0]["significance_flag"] == "exploratory"

    def test_no_fdr_table(self, sample_data):
        expr, pheno = sample_data
        gene_list = ["PER1"]
        traits = ["BMI"]

        # Run without FDR table
        result = generate_correlation_analysis(
            expression_df=expr,
            phenotype_df=pheno,
            gene_list=gene_list,
            trait_columns=traits,
            fdr_adjusted_pvalues=None
        )

        assert len(result) == 1
        # Significance determined by raw p-value here
        # Since we generated correlation, p should be small
        assert result.iloc[0]["p"] < 0.05

    def test_missing_gene(self, sample_data):
        expr, pheno = sample_data
        gene_list = ["NON_EXISTENT"]
        traits = ["BMI"]

        result = generate_correlation_analysis(
            expression_df=expr,
            phenotype_df=pheno,
            gene_list=gene_list,
            trait_columns=traits
        )

        assert len(result) == 0

    def test_misaligned_indices(self):
        # Create data with different indices
        expr = pd.DataFrame({"G1": [1, 2, 3]}, index=["a", "b", "c"])
        pheno = pd.DataFrame({"T1": [10, 20, 30]}, index=["b", "c", "d"])

        result = generate_correlation_analysis(
            expression_df=expr,
            phenotype_df=pheno,
            gene_list=["G1"],
            trait_columns=["T1"]
        )

        # Should align on 'b', 'c'
        assert len(result) == 1

    def test_spearman_vs_pearson_selection(self):
        # Create non-normal data
        np.random.seed(42)
        n = 100
        expr = pd.DataFrame({"G1": np.random.exponential(1, n)}, index=range(n))
        pheno = pd.DataFrame({"T1": np.random.exponential(1, n)}, index=range(n))

        result = generate_correlation_analysis(
            expression_df=expr,
            phenotype_df=pheno,
            gene_list=["G1"],
            trait_columns=["T1"]
        )

        # Should have used Spearman
        # We can't directly inspect the method in the output, but we can verify it ran
        assert len(result) == 1
        # If it crashed on normality test, it would fail.
        # The implementation falls back to Spearman if normality fails.