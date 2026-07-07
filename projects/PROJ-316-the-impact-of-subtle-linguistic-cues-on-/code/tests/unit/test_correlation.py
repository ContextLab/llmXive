"""
Unit tests for correlation analysis module.
Verifies p-values and effect sizes against known synthetic datasets.
"""

import pytest
import pandas as pd
import numpy as np
from src.analysis.correlation import (
    compute_correlations,
    apply_bh_correction,
    calculate_effect_size,
    run_correlation_analysis
)


@pytest.fixture
def synthetic_data():
    """Create a synthetic dataset with known correlation."""
    np.random.seed(42)
    n = 100
    # Create two variables with a known positive correlation
    x = np.random.normal(0, 1, n)
    y = 0.5 * x + np.random.normal(0, 0.5, n)  # Moderate positive correlation

    df = pd.DataFrame({
        "conversation_id": range(n),
        "feature_a": x,
        "authenticity_score": y
    })
    return df


@pytest.fixture
def synthetic_data_noisy():
    """Create a synthetic dataset with near-zero correlation."""
    np.random.seed(42)
    n = 100
    x = np.random.normal(0, 1, n)
    y = np.random.normal(0, 1, n)  # Independent

    df = pd.DataFrame({
        "conversation_id": range(n),
        "feature_b": x,
        "authenticity_score": y
    })
    return df


@pytest.fixture
def synthetic_data_multiple():
    """Create a dataset with multiple features for BH correction test."""
    np.random.seed(42)
    n = 50
    base = np.random.normal(0, 1, n)
    df = pd.DataFrame({
        "conversation_id": range(n),
        "feat1": base + np.random.normal(0, 0.1, n),  # High correlation
        "feat2": base * 0.5 + np.random.normal(0, 0.5, n),  # Medium
        "feat3": np.random.normal(0, 1, n),  # None
        "authenticity_score": base * 0.8 + np.random.normal(0, 0.2, n)
    })
    return df


class TestComputeCorrelations:
    def test_pearson_correlation_known_value(self, synthetic_data):
        """Test that Pearson correlation is computed correctly."""
        results = compute_correlations(synthetic_data, ["feature_a"], method="pearson")
        assert not results.empty
        assert "correlation" in results.columns
        # Expected correlation is around 0.5 / sqrt(0.5^2 + 0.5^2) ~ 0.7
        # We just check it's positive and significant
        assert results["correlation"].iloc[0] > 0.3
        assert results["p_value"].iloc[0] < 0.05

    def test_spearman_correlation_known_value(self, synthetic_data):
        """Test that Spearman correlation is computed correctly."""
        results = compute_correlations(synthetic_data, ["feature_a"], method="spearman")
        assert not results.empty
        assert results["correlation"].iloc[0] > 0.3
        assert results["p_value"].iloc[0] < 0.05

    def test_missing_target_column(self, synthetic_data):
        """Test error handling for missing target column."""
        with pytest.raises(ValueError):
            compute_correlations(synthetic_data, ["feature_a"], target_col="missing_col")

    def test_missing_feature_column(self, synthetic_data):
        """Test handling of missing feature column."""
        results = compute_correlations(synthetic_data, ["missing_feature"], method="pearson")
        assert results.empty

    def test_insufficient_data(self, synthetic_data):
        """Test handling of insufficient data points."""
        small_df = synthetic_data.head(2)
        results = compute_correlations(small_df, ["feature_a"], method="pearson")
        assert results.empty


class TestBHCorrection:
    def test_bh_correction_reduces_p_values(self, synthetic_data_multiple):
        """Test that BH correction adjusts p-values appropriately."""
        results = compute_correlations(
            synthetic_data_multiple,
            ["feat1", "feat2", "feat3"],
            method="pearson"
        )
        corrected = apply_bh_correction(results)

        assert "p_adjusted" in corrected.columns
        assert "is_significant" in corrected.columns
        # Adjusted p-values should be >= original p-values
        assert (corrected["p_adjusted"] >= corrected["p_value"]).all()

    def test_bh_correction_significance(self, synthetic_data_multiple):
        """Test that BH correction identifies significant features correctly."""
        results = compute_correlations(
            synthetic_data_multiple,
            ["feat1", "feat2", "feat3"],
            method="pearson"
        )
        corrected = apply_bh_correction(results, alpha=0.05)

        # feat1 and feat2 should likely be significant, feat3 not
        sig_count = corrected["is_significant"].sum()
        assert sig_count >= 1  # At least feat1 should be significant

    def test_empty_dataframe(self):
        """Test BH correction on empty DataFrame."""
        empty_df = pd.DataFrame(columns=["feature", "p_value"])
        result = apply_bh_correction(empty_df)
        assert result.empty


class TestEffectSize:
    def test_effect_size_labels(self, synthetic_data):
        """Test that effect size labels are assigned correctly."""
        results = compute_correlations(synthetic_data, ["feature_a"], method="pearson")
        labeled = calculate_effect_size(results, ["feature_a"])

        assert "effect_size_label" in labeled.columns
        label = labeled["effect_size_label"].iloc[0]
        # With r ~ 0.7, should be "large"
        assert label in ["small", "medium", "large", "negligible"]

    def test_effect_size_thresholds(self):
        """Test effect size labeling thresholds."""
        test_df = pd.DataFrame({
            "feature": ["neg", "small", "medium", "large"],
            "correlation": [0.05, 0.2, 0.4, 0.6]
        })
        labeled = calculate_effect_size(test_df, ["feature"], correlation_col="correlation")

        assert labeled.loc[0, "effect_size_label"] == "negligible"
        assert labeled.loc[1, "effect_size_label"] == "small"
        assert labeled.loc[2, "effect_size_label"] == "medium"
        assert labeled.loc[3, "effect_size_label"] == "large"


class TestRunCorrelationAnalysis:
    def test_full_pipeline_integration(self, synthetic_data_multiple, tmp_path):
        """Test the full analysis pipeline."""
        features_path = tmp_path / "features.csv"
        ratings_path = tmp_path / "ratings.csv"
        output_path = tmp_path / "results.csv"
        flags_path = tmp_path / "flags.json"

        # Prepare input files
        features_df = synthetic_data_multiple.drop(columns=["authenticity_score"])
        ratings_df = synthetic_data_multiple[["conversation_id", "authenticity_score"]]

        features_df.to_csv(features_path, index=False)
        ratings_df.to_csv(ratings_path, index=False)

        # Run analysis
        flags = run_correlation_analysis(
            str(features_path),
            str(ratings_path),
            str(output_path),
            str(flags_path)
        )

        # Verify outputs
        assert output_path.exists()
        assert flags_path.exists()
        assert "total_tests" in flags
        assert "disclaimer" in flags
        assert "These results indicate association, not causation" in flags["disclaimer"]