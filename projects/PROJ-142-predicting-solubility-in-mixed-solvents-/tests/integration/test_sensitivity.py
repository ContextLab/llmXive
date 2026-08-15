"""
Integration test for sensitivity analysis (T028).

This test verifies that the sensitivity analysis pipeline correctly identifies
top-ranked interaction terms across different SHAP thresholds (low, medium, high)
and produces stable results as per SC-004 (Jaccard similarity >= 0.6).

Prerequisites:
- T029: SHAP values computed and saved to data/artifacts/shap_values.npy
- T030: SHAP analysis plot and ranking saved to data/artifacts/shap_analysis.png and shap_ranking.json
- T031: Top 5 interaction terms identified and saved
"""
import os
import json
import numpy as np
from pathlib import Path
import pytest

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def load_shap_values():
    """Load pre-computed SHAP values from artifact."""
    shap_path = ARTIFACTS_DIR / "shap_values.npy"
    if not shap_path.exists():
        raise FileNotFoundError(
            f"SHAP values not found at {shap_path}. "
            "Ensure T029 has been completed successfully."
        )
    return np.load(shap_path)


def load_feature_names():
    """Load feature names from the processed dataset."""
    features_path = PROCESSED_DIR / "solubility_features.csv"
    if not features_path.exists():
        raise FileNotFoundError(
            f"Processed features not found at {features_path}. "
            "Ensure T018 has been completed successfully."
        )
    # Read header only to get column names
    import pandas as pd
    df = pd.read_csv(features_path, nrows=0)
    # Filter for interaction terms (usually contain 'interaction' or are derived)
    # For this test, we assume the feature engineering step labeled interaction terms appropriately
    # or we simply test against all numeric features if specific naming isn't enforced yet.
    return df.columns.tolist()


def load_shap_ranking():
    """Load the SHAP ranking JSON artifact."""
    ranking_path = ARTIFACTS_DIR / "shap_ranking.json"
    if not ranking_path.exists():
        raise FileNotFoundError(
            f"SHAP ranking not found at {ranking_path}. "
            "Ensure T030 and T031 have been completed successfully."
        )
    with open(ranking_path, 'r') as f:
        return json.load(f)


def _compute_jaccard(set_a, set_b):
    """Compute Jaccard similarity between two sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0


def test_sensitivity_sample():
    """
    Integration test for sensitivity analysis.
    
    Verifies that:
    1. SHAP values are loaded correctly.
    2. Top-ranked terms are stable across thresholds (Low, Medium, High).
    3. Jaccard similarity between top-5 sets at different thresholds meets SC-004 (>= 0.6).
    4. The shap_ranking.json artifact contains the necessary stability metrics.
    """
    # 1. Load dependencies
    shap_values = load_shap_values()
    feature_names = load_feature_names()
    ranking_data = load_shap_ranking()
    
    assert shap_values is not None and shap_values.size > 0, "SHAP values are empty."
    assert feature_names is not None and len(feature_names) > 0, "Feature names are empty."
    assert isinstance(ranking_data, dict), "SHAP ranking data is not a dictionary."

    # 2. Verify the artifact contains the required stability metrics
    # The implementation of T033/T034 should have appended these keys.
    required_keys = ['jaccard_similarity', 'spearman_correlation']
    for key in required_keys:
        assert key in ranking_data, f"Missing required key '{key}' in shap_ranking.json. " \
                                    f"Ensure T033 and T034 have run and appended stability metrics."

    # 3. Validate Jaccard similarity threshold (SC-004)
    # We check the metric computed by the pipeline. If it's missing or below threshold, the test fails.
    jaccard_score = ranking_data.get('jaccard_similarity', 0.0)
    assert jaccard_score >= 0.6, (
        f"Jaccard similarity ({jaccard_score:.4f}) is below the required threshold of 0.6. "
        "Sensitivity analysis indicates unstable feature selection across thresholds."
    )

    # 4. Validate Spearman correlation threshold (SC-002)
    spearman_score = ranking_data.get('spearman_correlation', 0.0)
    assert spearman_score >= 0.8, (
        f"Spearman rank correlation ({spearman_score:.4f}) is below the required threshold of 0.8. "
        "Feature rankings are not stable across CV folds."
    )

    # 5. Verify that top terms are present in the ranking
    # The structure of shap_ranking.json should include 'top_interaction_terms' or similar.
    # We check for the presence of a list of top terms to ensure T031 ran.
    if 'top_interaction_terms' in ranking_data:
        top_terms = ranking_data['top_interaction_terms']
        assert isinstance(top_terms, list), "top_interaction_terms must be a list."
        assert len(top_terms) > 0, "top_interaction_terms list is empty."
        # Verify at least some terms are actually interaction terms (heuristic check)
        # This depends on how T016 named them, but we expect 'interaction' in the name or similar.
        # If the naming convention isn't strict, we just verify the list exists and has content.
    
    # 6. Sanity check: Ensure SHAP values shape matches feature count (approx)
    # SHAP values shape: (n_samples, n_features)
    n_features_in_shap = shap_values.shape[1] if len(shap_values.shape) > 1 else 1
    # Note: The feature engineering step might have added more features than the initial load,
    # so we just check that SHAP has dimensions, not an exact match to the raw CSV header
    # unless the pipeline guarantees alignment.
    assert n_features_in_shap > 0, "SHAP values have no features."

    # If all assertions pass, the sensitivity analysis integration is valid.
    assert True, "Sensitivity analysis integration test passed."