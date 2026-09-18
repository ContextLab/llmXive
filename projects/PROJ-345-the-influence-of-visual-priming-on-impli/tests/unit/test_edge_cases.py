"""
Unit tests for edge cases: missing metadata and high collinearity.

Tests cover:
1. Handling of missing stimulus metadata in preprocessing.
2. Handling of high collinearity (VIF > 5.0) in model metrics.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import from project modules based on API surface
from code.data.preprocess import check_confounding, load_human_rated_ambiguity
from code.models.metrics import calculate_vif, check_collinearity, run_vif_analysis


class TestMissingMetadata:
    """Tests for handling missing metadata scenarios."""

    def test_missing_human_rated_ambiguity_file(self):
        """Test that missing human-rated ambiguity file raises appropriate error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "nonexistent_ambiguity.csv"
            
            # Should raise FileNotFoundError or similar
            with pytest.raises(FileNotFoundError):
                load_human_rated_ambiguity(missing_path)

    def test_empty_metadata_dataframe(self):
        """Test handling of empty metadata dataframe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_file = Path(tmpdir) / "empty_ambiguity.csv"
            # Create empty CSV with headers only
            pd.DataFrame(columns=["stimulus_id", "ambiguity"]).to_csv(empty_file, index=False)
            
            df = load_human_rated_ambiguity(empty_file)
            assert df.empty, "Expected empty dataframe for empty CSV"

    def test_partial_missing_metadata(self):
        """Test handling of partial missing metadata (some stimuli without ratings)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            partial_file = Path(tmpdir) / "partial_ambiguity.csv"
            # Create CSV with some missing ambiguity values
            data = {
                "stimulus_id": ["stim1", "stim2", "stim3"],
                "ambiguity": [0.5, None, 0.8]
            }
            pd.DataFrame(data).to_csv(partial_file, index=False)
            
            df = load_human_rated_ambiguity(partial_file)
            assert len(df) == 3, "Expected 3 rows"
            assert df["ambiguity"].isna().sum() == 1, "Expected 1 missing value"


class TestHighCollinearity:
    """Tests for handling high collinearity scenarios."""

    def test_vif_calculation_with_perfect_collinearity(self):
        """Test VIF calculation with perfect collinearity (should return very high VIF)."""
        # Create data with perfect collinearity
        n = 100
        x1 = np.random.randn(n)
        x2 = x1 * 2  # Perfectly correlated
        
        df = pd.DataFrame({
            "y": np.random.randn(n),
            "x1": x1,
            "x2": x2
        })
        
        vif_results = calculate_vif(df[["x1", "x2"]])
        
        # At least one VIF should be very high (approaching infinity)
        assert any(vif_results["VIF"] > 1000), "Expected very high VIF for perfect collinearity"

    def test_vif_calculation_with_high_collinearity(self):
        """Test VIF calculation with high collinearity (VIF > 5.0)."""
        n = 100
        x1 = np.random.randn(n)
        x2 = x1 * 0.95 + np.random.randn(n) * 0.1  # High correlation (~0.95)
        
        df = pd.DataFrame({
            "y": np.random.randn(n),
            "x1": x1,
            "x2": x2
        })
        
        vif_results = calculate_vif(df[["x1", "x2"]])
        
        # Check that VIF > 5.0 for high collinearity
        assert any(vif_results["VIF"] > 5.0), "Expected VIF > 5.0 for high collinearity"

    def test_check_collinearity_flagging(self):
        """Test that check_collinearity correctly flags high collinearity."""
        n = 100
        x1 = np.random.randn(n)
        x2 = x1 * 0.95 + np.random.randn(n) * 0.1  # High correlation
        
        df = pd.DataFrame({
            "y": np.random.randn(n),
            "x1": x1,
            "x2": x2
        })
        
        result = check_collinearity(df[["x1", "x2"]])
        
        assert result["is_confounded"] is True, "Expected is_confounded=True for high collinearity"
        assert result["max_vif"] > 5.0, "Expected max_vif > 5.0"

    def test_vif_analysis_with_multiple_predictors(self):
        """Test VIF analysis with multiple predictors where some are collinear."""
        n = 100
        x1 = np.random.randn(n)
        x2 = x1 * 0.9 + np.random.randn(n) * 0.2  # High correlation with x1
        x3 = np.random.randn(n)  # Independent
        x4 = x3 * 0.3 + np.random.randn(n) * 0.8  # Low correlation with x3
        
        df = pd.DataFrame({
            "y": np.random.randn(n),
            "x1": x1,
            "x2": x2,
            "x3": x3,
            "x4": x4
        })
        
        vif_results = calculate_vif(df[["x1", "x2", "x3", "x4"]])
        
        # x1 and x2 should have high VIF
        x1_vif = vif_results[vif_results["feature"] == "x1"]["VIF"].values[0]
        x2_vif = vif_results[vif_results["feature"] == "x2"]["VIF"].values[0]
        
        assert x1_vif > 5.0, "Expected x1 VIF > 5.0"
        assert x2_vif > 5.0, "Expected x2 VIF > 5.0"
        
        # x3 and x4 should have lower VIF
        x3_vif = vif_results[vif_results["feature"] == "x3"]["VIF"].values[0]
        x4_vif = vif_results[vif_results["feature"] == "x4"]["VIF"].values[0]
        
        assert x3_vif < 5.0, "Expected x3 VIF < 5.0"
        assert x4_vif < 5.0, "Expected x4 VIF < 5.0"

    def test_run_vif_analysis_output_structure(self):
        """Test that run_vif_analysis returns expected structure."""
        n = 100
        x1 = np.random.randn(n)
        x2 = np.random.randn(n)  # Independent
        
        df = pd.DataFrame({
            "y": np.random.randn(n),
            "x1": x1,
            "x2": x2
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "vif_report.json"
            
            result = run_vif_analysis(df[["x1", "x2"]], output_path)
            
            assert "max_vif" in result, "Expected max_vif in result"
            assert "is_confounded" in result, "Expected is_confounded in result"
            assert "vif_by_feature" in result, "Expected vif_by_feature in result"
            
            # Verify JSON file was written
            assert output_path.exists(), "Expected vif report JSON file to exist"
            
            with open(output_path) as f:
                saved_data = json.load(f)
                assert saved_data == result, "Expected saved JSON to match return value"


class TestConfoundingCheckEdgeCases:
    """Tests for confounding check edge cases."""

    def test_confounding_check_with_zero_variance(self):
        """Test confounding check with zero variance in one variable."""
        n = 50
        data = {
            "prime_order": [1] * n,  # Zero variance
            "block": list(range(n))
        }
        df = pd.DataFrame(data)
        
        # Should handle gracefully, likely return no correlation or warning
        result = check_confounding(df, "prime_order", "block")
        
        assert "prime_order_correlation" in result
        assert "is_confounded" in result

    def test_confounding_check_with_small_sample(self):
        """Test confounding check with very small sample size."""
        n = 5
        data = {
            "prime_order": [1, 2, 3, 4, 5],
            "block": [1, 2, 3, 4, 5]
        }
        df = pd.DataFrame(data)
        
        result = check_confounding(df, "prime_order", "block")
        
        assert "prime_order_correlation" in result
        assert "is_confounded" in result

    def test_confounding_check_with_categorical_data(self):
        """Test confounding check with categorical data."""
        n = 100
        data = {
            "prime_condition": np.random.choice(["A", "B"], n),
            "block": np.random.choice([1, 2, 3], n)
        }
        df = pd.DataFrame(data)
        
        # Convert to numeric for correlation
        df["prime_condition_num"] = df["prime_condition"].map({"A": 0, "B": 1})
        
        result = check_confounding(df, "prime_condition_num", "block")
        
        assert "prime_order_correlation" in result
        assert "is_confounded" in result