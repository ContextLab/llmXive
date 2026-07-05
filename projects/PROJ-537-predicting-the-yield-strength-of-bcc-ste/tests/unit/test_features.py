"""
Unit tests for feature encoding (one-hot, atomic fractions) and normalization
as required by User Story 2 (T024 implementation).
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling.features import (
    encode_composition,
    encode_dft_descriptors,
    calculate_vif,
    normalize_features
)
from config import CONFIG


class TestCompositionEncoding:
    """Tests for one-hot encoding and atomic fraction calculation."""

    def test_one_hot_encoding_basic(self):
        """Test basic one-hot encoding of alloy composition."""
        # Sample composition string (e.g., "Fe0.95Cr0.05")
        compositions = [
            "Fe0.95Cr0.05",
            "Fe0.90Cr0.05Mo0.05",
            "Fe1.00"
        ]

        df = pd.DataFrame({"composition": compositions})
        encoded = encode_composition(df)

        # Check that element columns are created
        expected_elements = {"Fe", "Cr", "Mo"}
        for elem in expected_elements:
            assert elem in encoded.columns, f"Expected column {elem} not found"

        # Check that values sum to 1.0 (within floating point tolerance)
        element_cols = [col for col in encoded.columns if col in expected_elements]
        row_sums = encoded[element_cols].sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6), "Atomic fractions should sum to 1.0"

    def test_one_hot_encoding_missing_elements(self):
        """Test that missing elements get zero values."""
        compositions = [
            "Fe0.95Cr0.05",
            "Fe1.00"  # No Cr
        ]
        df = pd.DataFrame({"composition": compositions})
        encoded = encode_composition(df)

        # First row should have Cr > 0
        assert encoded.loc[0, "Cr"] > 0, "First row should have Cr"
        # Second row should have Cr = 0
        assert encoded.loc[1, "Cr"] == 0, "Second row should have no Cr"

    def test_one_hot_encoding_normalization(self):
        """Test that fractions are normalized even if input doesn't sum to 1."""
        # This tests the robustness of the parser
        compositions = [
            "Fe0.5Cr0.5",  # Sums to 1
            "Fe0.4Cr0.4"   # Sums to 0.8 - should be normalized to 0.5/0.5
        ]
        df = pd.DataFrame({"composition": compositions})
        encoded = encode_composition(df)

        # Check normalization
        row_sums = encoded[["Fe", "Cr"]].sum(axis=1)
        assert np.allclose(row_sums, 1.0, atol=1e-6), "Fractions should be normalized"


class TestDFTDescriptorEncoding:
    """Tests for DFT descriptor normalization."""

    def test_dft_normalization(self):
        """Test that DFT descriptors are normalized correctly."""
        data = {
            "shear_modulus_GPa": [80.0, 100.0, 120.0],
            "bulk_modulus_GPa": [150.0, 160.0, 170.0],
            "electronic_specific_heat": [2.0, 4.0, 6.0]
        }
        df = pd.DataFrame(data)

        normalized = normalize_features(df, ["shear_modulus_GPa", "bulk_modulus_GPa", "electronic_specific_heat"])

        # Check that mean is 0 and std is 1 for normalized columns
        for col in ["shear_modulus_GPa", "bulk_modulus_GPa", "electronic_specific_heat"]:
            assert np.isclose(normalized[col].mean(), 0.0, atol=1e-6), f"{col} should have mean 0"
            assert np.isclose(normalized[col].std(), 1.0, atol=1e-6), f"{col} should have std 1"

    def test_dft_normalization_single_value(self):
        """Test normalization with single value (edge case)."""
        data = {
            "shear_modulus_GPa": [100.0]
        }
        df = pd.DataFrame(data)

        # Should not crash, though std will be 0
        normalized = normalize_features(df, ["shear_modulus_GPa"])
        assert normalized["shear_modulus_GPa"].iloc[0] == 0.0, "Single value should normalize to 0"


class TestVIFCalculation:
    """Tests for Variance Inflation Factor calculation."""

    def test_vif_no_multicollinearity(self):
        """Test VIF with independent features."""
        data = {
            "feature1": np.random.rand(100),
            "feature2": np.random.rand(100),
            "feature3": np.random.rand(100)
        }
        df = pd.DataFrame(data)

        vif_results = calculate_vif(df)

        # VIF should be close to 1 for independent features
        for vif_val in vif_results.values():
            assert vif_val < 5.0, f"VIF should be low for independent features, got {vif_val}"

    def test_vif_high_collinearity(self):
        """Test VIF detection of high collinearity."""
        x = np.random.rand(100)
        data = {
            "feature1": x,
            "feature2": x * 2 + np.random.normal(0, 0.01, 100),  # Highly correlated
            "feature3": np.random.rand(100)
        }
        df = pd.DataFrame(data)

        vif_results = calculate_vif(df)

        # feature1 and feature2 should have high VIF
        assert vif_results["feature1"] > 5.0, "feature1 should have high VIF"
        assert vif_results["feature2"] > 5.0, "feature2 should have high VIF"


class TestIntegration:
    """Integration tests for the full feature engineering pipeline."""

    def test_full_feature_pipeline(self):
        """Test end-to-end feature encoding."""
        # Create sample data that mimics the merged dataset structure
        data = {
            "composition": ["Fe0.95Cr0.05", "Fe0.90Mo0.10", "Fe0.85Cr0.10Mo0.05"],
            "shear_modulus_GPa": [80.0, 90.0, 85.0],
            "bulk_modulus_GPa": [150.0, 160.0, 155.0]
        }
        df = pd.DataFrame(data)

        # Encode composition
        encoded = encode_composition(df)

        # Encode DFT descriptors
        dft_features = encode_dft_descriptors(encoded)

        # Normalize all features
        feature_cols = [col for col in dft_features.columns if col not in ["composition"]]
        final_features = normalize_features(dft_features, feature_cols)

        # Verify structure
        assert "Fe" in final_features.columns
        assert "Cr" in final_features.columns
        assert "Mo" in final_features.columns
        assert "shear_modulus_GPa" in final_features.columns
        assert "bulk_modulus_GPa" in final_features.columns

        # Verify normalization
        for col in ["shear_modulus_GPa", "bulk_modulus_GPa"]:
            assert np.isclose(final_features[col].mean(), 0.0, atol=1e-6), f"{col} should be normalized"