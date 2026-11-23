"""
Unit test for Task T028: Verify Permutation Importance runs with 1,000 permutations
and returns a valid score distribution.

This test exercises the `perform_permutation_importance` function from
`code/analyze_explainability.py` to ensure it executes correctly with the
specified number of permutations and returns a non-empty, valid score distribution.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analyze_explainability import perform_permutation_importance, load_model, load_data
from utils import set_seed


class TestPermutationImportance:
    """Test suite for Permutation Importance functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup fixtures for each test."""
        set_seed(42)
        self.test_data_path = project_root / "data" / "processed" / "cleaned_316L.csv"
        self.models_dir = project_root / "models" / "artifacts"

    def test_permutation_importance_runs_with_1000_permutations(self):
        """
        Verify that perform_permutation_importance runs with exactly 1,000 permutations.
        
        This test:
        1. Loads the preprocessed dataset (cleaned_316L.csv)
        2. Loads the best performing model (Gradient Boosting or MLP)
        3. Calls perform_permutation_importance with n_permutations=1000
        4. Verifies the function returns a valid score distribution
        """
        # Skip if required files don't exist (prerequisites not met)
        if not self.test_data_path.exists():
            pytest.skip(f"Test data not found: {self.test_data_path}. Run T018 first.")
        
        # Load data
        df = load_data(self.test_data_path)
        
        # Define features and target based on the project's data model
        feature_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        target_col = 'porosity'
        
        # Filter to only available columns (in case schema varies)
        available_features = [col for col in feature_cols if col in df.columns]
        if not available_features:
            pytest.skip("No feature columns found in dataset.")
        
        X = df[available_features]
        y = df[target_col]
        
        # Load the best model (try Gradient Boosting first, then MLP)
        gb_model_path = self.models_dir / "gradient_boosting_model.pkl"
        mlp_model_path = self.models_dir / "mlp_model.pkl"
        
        model = None
        if gb_model_path.exists():
            model = load_model(gb_model_path)
        elif mlp_model_path.exists():
            model = load_model(mlp_model_path)
        else:
            pytest.skip("No trained models found. Run T025 first.")
        
        # Run permutation importance with exactly 1,000 permutations
        n_permutations = 1000
        result = perform_permutation_importance(model, X, y, n_permutations=n_permutations)
        
        # Verify result structure
        assert result is not None, "Permutation importance returned None"
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        
        # Check for expected keys
        assert "feature_names" in result, "Missing 'feature_names' in result"
        assert "importance_scores" in result, "Missing 'importance_scores' in result"
        assert "std_scores" in result, "Missing 'std_scores' in result"
        
        # Verify feature names match input
        assert result["feature_names"] == available_features, \
            f"Feature names mismatch: {result['feature_names']} != {available_features}"
        
        # Verify importance scores is a list/array with correct length
        importance_scores = result["importance_scores"]
        assert len(importance_scores) == len(available_features), \
            f"Importance scores length mismatch: {len(importance_scores)} != {len(available_features)}"
        
        # Verify scores are numeric and valid
        for score in importance_scores:
            assert isinstance(score, (int, float, np.number)), \
                f"Importance score must be numeric, got {type(score)}"
            assert not np.isnan(score), "Importance score contains NaN"
            assert not np.isinf(score), "Importance score contains Inf"
        
        # Verify standard deviations are present and valid
        std_scores = result["std_scores"]
        assert len(std_scores) == len(available_features), \
            f"Std scores length mismatch: {len(std_scores)} != {len(available_features)}"
        
        for std in std_scores:
            assert isinstance(std, (int, float, np.number)), \
                f"Std score must be numeric, got {type(std)}"
            assert std >= 0, f"Std score must be non-negative, got {std}"
            assert not np.isnan(std), "Std score contains NaN"
            assert not np.isinf(std), "Std score contains Inf"
        
        # Verify the distribution is not trivial (at least one feature has non-zero importance)
        assert any(score != 0 for score in importance_scores), \
            "All importance scores are zero - permutation importance failed to detect feature importance"
        
        print(f"✓ Permutation importance completed successfully with {n_permutations} permutations")
        print(f"  Feature importance scores: {dict(zip(result['feature_names'], result['importance_scores']))}")
        print(f"  Std deviations: {dict(zip(result['feature_names'], result['std_scores']))}")

    def test_permutation_importance_reproducibility(self):
        """
        Verify that permutation importance is reproducible with fixed seed.
        """
        if not self.test_data_path.exists():
            pytest.skip(f"Test data not found: {self.test_data_path}")
        
        df = load_data(self.test_data_path)
        feature_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
        available_features = [col for col in feature_cols if col in df.columns]
        
        if not available_features:
            pytest.skip("No feature columns found in dataset.")
        
        X = df[available_features]
        y = df['porosity']
        
        gb_model_path = self.models_dir / "gradient_boosting_model.pkl"
        if not gb_model_path.exists():
            pytest.skip("No trained models found.")
        
        model = load_model(gb_model_path)
        
        # Run twice with same seed
        set_seed(123)
        result1 = perform_permutation_importance(model, X, y, n_permutations=100)
        
        set_seed(123)
        result2 = perform_permutation_importance(model, X, y, n_permutations=100)
        
        # Results should be identical with same seed
        np.testing.assert_array_equal(
            result1["importance_scores"],
            result2["importance_scores"],
            err_msg="Permutation importance results are not reproducible with fixed seed"
        )
        
        print("✓ Permutation importance is reproducible with fixed seed")

    def test_permutation_importance_edge_cases(self):
        """
        Test edge cases: small dataset, single feature.
        """
        if not self.test_data_path.exists():
            pytest.skip(f"Test data not found: {self.test_data_path}")
        
        df = load_data(self.test_data_path)
        
        # Create a minimal subset for edge case testing
        feature_cols = ['laser_power', 'scan_speed']
        available_features = [col for col in feature_cols if col in df.columns]
        
        if len(available_features) < 2:
            pytest.skip("Need at least 2 feature columns for edge case test.")
        
        X = df[available_features].head(20)  # Small sample
        y = df['porosity'].head(20)
        
        gb_model_path = self.models_dir / "gradient_boosting_model.pkl"
        if not gb_model_path.exists():
            pytest.skip("No trained models found.")
        
        model = load_model(gb_model_path)
        
        # Run with fewer permutations for speed in edge case test
        result = perform_permutation_importance(model, X, y, n_permutations=10)
        
        assert result is not None
        assert len(result["importance_scores"]) == len(available_features)
        assert all(isinstance(s, (int, float, np.number)) for s in result["importance_scores"])
        
        print("✓ Edge case test passed (small dataset)")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])