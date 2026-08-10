"""
Unit tests for feature extraction logic (T018).
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.extract_features import (
    extract_ngram_features,
    extract_pos_features,
    stratified_sample_by_length,
    validate_features
)

class TestNgramFeatures:
    def test_extract_ngram_features_basic(self):
        text = "The cat sat on the mat."
        features = extract_ngram_features(text)
        # Should have some features
        assert isinstance(features, dict)
        assert len(features) > 0
        # Check that values are numeric
        for v in features.values():
            assert isinstance(v, (int, float))

    def test_extract_ngram_features_empty(self):
        text = ""
        features = extract_ngram_features(text)
        # Should return default zeros or empty dict with zeros
        # Based on implementation, it returns a dict with zeros
        assert isinstance(features, dict)
        # Implementation returns {f"ngram_{i}": 0.0 for i in range(30)}
        assert all(v == 0.0 for v in features.values())

class TestStratifiedSample:
    def test_stratified_sample_length(self):
        # Create mock data with varying lengths
        data = [
            {"question": "Short", "id": 1},
            {"question": "Medium length question", "id": 2},
            {"question": "This is a very long question with many words to increase the length significantly", "id": 3},
            {"question": "Another short", "id": 4},
            {"question": "Medium again", "id": 5},
        ]
        
        sample = stratified_sample_by_length(data, n=3, seed=42)
        assert len(sample) == 3
        # Check that IDs are preserved
        ids = [s['id'] for s in sample]
        assert len(set(ids)) == 3 # No duplicates

class TestFeatureValidation:
    def test_validate_features_valid(self):
        data = [
            {
                "token_id": 0,
                "feature_vector": [1.0, 0.0, 0.5, 0.9, 2.0],
                "example_id": "1"
            },
            {
                "token_id": 1,
                "feature_vector": [2.0, 1.0, 0.2, 0.8, 3.0],
                "example_id": "1"
            }
        ]
        df = pd.DataFrame(data)
        assert validate_features(df) is True

    def test_validate_features_missing_column(self):
        data = [
            {
                "token_id": 0,
                "feature_vector": [1.0, 0.0],
                # Missing example_id
            }
        ]
        df = pd.DataFrame(data)
        assert validate_features(df) is False

    def test_validate_features_nan_in_vector(self):
        data = [
            {
                "token_id": 0,
                "feature_vector": [1.0, np.nan, 0.5],
                "example_id": "1"
            }
        ]
        df = pd.DataFrame(data)
        assert validate_features(df) is False

    def test_validate_features_non_list_vector(self):
        data = [
            {
                "token_id": 0,
                "feature_vector": "not a list",
                "example_id": "1"
            }
        ]
        df = pd.DataFrame(data)
        assert validate_features(df) is False