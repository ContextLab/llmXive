"""
Integration test for permutation importance pipeline.

Task: T111 [US3] Integration test for permutation importance pipeline.
Goal: Implement `test_permutation_importance_generates_ranked_features` to assert correct ranking logic.

This test verifies that the permutation importance module:
1. Successfully loads a trained Random Forest model and corresponding feature data.
2. Computes permutation importance scores for all features.
3. Generates a ranked list of features based on their importance scores.
4. Ensures the ranking logic is correct (higher importance -> higher rank).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
from sklearn.ensemble import RandomForestRegressor
from sklearn.datasets import make_regression

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root / "code"))

from attribution.permutation_importance import compute_permutation_importance


def _create_mock_model_and_data(temp_dir: Path):
    """
    Helper to create a mock trained Random Forest model and feature data
    for testing purposes.
    """
    # Generate synthetic regression data that mimics the feature space
    # We use a fixed seed for reproducibility
    X, y = make_regression(
        n_samples=500,
        n_features=10,
        n_informative=5,
        noise=0.1,
        random_state=42
    )
    
    # Train a Random Forest model
    rf_model = RandomForestRegressor(
        n_estimators=50,
        max_depth=5,
        random_state=42,
        n_jobs=1
    )
    rf_model.fit(X, y)
    
    # Save the model
    model_path = temp_dir / "mock_rf_model.pkl"
    import joblib
    joblib.dump(rf_model, model_path)
    
    # Save feature data (mimicking features_2d.parquet or similar)
    # We'll save as JSON for simplicity in this test
    feature_data = {
        "feature_names": [f"feature_{i}" for i in range(X.shape[1])],
        "X": X.tolist(),
        "y": y.tolist()
    }
    
    data_path = temp_dir / "mock_feature_data.json"
    with open(data_path, "w") as f:
        json.dump(feature_data, f)
        
    return model_path, data_path


def test_permutation_importance_generates_ranked_features():
    """
    Test that permutation importance generates a correctly ranked list of features.
    
    This test:
    1. Creates a mock trained Random Forest model and feature data.
    2. Runs the permutation importance computation.
    3. Verifies that the output is a ranked list of features.
    4. Asserts that the ranking logic is correct (importance scores are ordered).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_path = Path(tmp_dir)
        
        # Create mock model and data
        model_path, data_path = _create_mock_model_and_data(temp_path)
        
        # Define output path for results
        output_path = temp_path / "permutation_importance_result.json"
        
        # Run permutation importance
        # We use a small n_repeats for speed in testing
        compute_permutation_importance(
            model_path=str(model_path),
            data_path=str(data_path),
            output_path=str(output_path),
            n_repeats=3,
            random_state=42
        )
        
        # Verify output file was created
        assert output_path.exists(), "Permutation importance result file was not created"
        
        # Load and validate the result
        with open(output_path, "r") as f:
            result = json.load(f)
        
        # Check required keys exist
        assert "feature_importance" in result, "Missing 'feature_importance' key in result"
        assert "ranked_features" in result, "Missing 'ranked_features' key in result"
        
        feature_importance = result["feature_importance"]
        ranked_features = result["ranked_features"]
        
        # Verify feature_importance is a list of dicts with score and name
        assert isinstance(feature_importance, list), "feature_importance must be a list"
        assert len(feature_importance) > 0, "feature_importance list cannot be empty"
        
        for item in feature_importance:
            assert "feature_name" in item, "Each item must have 'feature_name'"
            assert "importance_score" in item, "Each item must have 'importance_score'"
            assert isinstance(item["importance_score"], (int, float)), "importance_score must be numeric"
        
        # Verify ranked_features is a list of feature names ordered by importance
        assert isinstance(ranked_features, list), "ranked_features must be a list"
        assert len(ranked_features) == len(feature_importance), "ranked_features length must match feature_importance"
        
        # Verify ranking logic: features should be ordered by importance_score descending
        # Extract scores in the order they appear in ranked_features
        scores_in_rank_order = []
        feature_name_to_score = {item["feature_name"]: item["importance_score"] for item in feature_importance}
        
        for feature_name in ranked_features:
            assert feature_name in feature_name_to_score, f"Feature {feature_name} in ranked_features not found in feature_importance"
            scores_in_rank_order.append(feature_name_to_score[feature_name])
        
        # Check that scores are in descending order (highest importance first)
        # Allow for floating point precision issues
        for i in range(len(scores_in_rank_order) - 1):
            assert scores_in_rank_order[i] >= scores_in_rank_order[i+1] - 1e-9, \
                f"Ranking is incorrect: score {scores_in_rank_order[i]} should be >= {scores_in_rank_order[i+1]}"
        
        # Additional check: verify that the top feature has the highest score
        if len(scores_in_rank_order) > 0:
            max_score = max(feature_name_to_score.values())
            top_feature = ranked_features[0]
            assert abs(feature_name_to_score[top_feature] - max_score) < 1e-9, \
                "Top ranked feature should have the highest importance score"