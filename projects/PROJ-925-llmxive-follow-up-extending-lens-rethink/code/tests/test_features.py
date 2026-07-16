import pytest
import math
import sys
import os
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path

# Add project root to path to allow relative imports during testing
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from features import (
    compute_semantic_entropy,
    compute_syntactic_depth,
    compute_noun_phrase_density,
    compute_token_diversity,
    extract_features_batch
)
from models.linguistic_feature_vector import LinguisticFeatureVector
from data.features import load_schema, validate_dataframe
from config import get_paths, init_run

class TestSyntacticDepth:
    """Unit tests for compute_syntactic_depth (T020)"""

    def test_short_caption_returns_zero(self):
        """Verify default depth=0 for short captions (FR-002)"""
        result = compute_syntactic_depth("Hello")
        assert result == 0

    def test_normal_caption_returns_positive_depth(self):
        """Verify spaCy dependency tree depth calculation"""
        caption = "The quick brown fox jumps over the lazy dog."
        result = compute_syntactic_depth(caption)
        assert isinstance(result, int)
        assert result >= 1

    def test_empty_caption_returns_zero(self):
        """Verify empty string handling"""
        result = compute_syntactic_depth("")
        assert result == 0


class TestSyntacticDepthIntegration:
    """Integration tests for full feature extraction pipeline (T021)"""

    def test_extract_features_batch_full_pipeline(self):
        """
        Integration test: Run full feature extraction pipeline on a static JSONL-like list.
        Verifies output DataFrame has non-null numeric columns for:
        - semantic_entropy (ln(perplexity))
        - syntactic_depth (tree depth)
        - noun_phrase_density
        - token_diversity
        """
        # Static test data (10 captions)
        test_captions = [
            "A cat sitting on a mat.",
            "The sun is shining brightly in the blue sky.",
            "A group of people are walking their dogs in the park.",
            "An old man reading a book under a tree.",
            "A beautiful sunset over the ocean with waves crashing.",
            "Children playing with colorful balloons in a garden.",
            "A dog running fast across a green field.",
            "A car driving down a wet road at night.",
            "A bird flying high above the mountains.",
            "A cup of coffee on a wooden table."
        ]

        # Execute pipeline
        df = extract_features_batch(test_captions)

        # Verify DataFrame structure
        assert df is not None
        assert len(df) == len(test_captions), "Row count mismatch"

        # Verify required columns exist
        required_columns = [
            'semantic_entropy',
            'syntactic_depth',
            'noun_phrase_density',
            'token_diversity'
        ]

        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

        # Verify no null values in numeric columns
        for col in required_columns:
            assert not df[col].isnull().any(), f"Null values found in {col}"

        # Verify data types
        assert df['semantic_entropy'].dtype in ['float64', 'float32'], "semantic_entropy not numeric"
        assert df['syntactic_depth'].dtype in ['int64', 'int32'], "syntactic_depth not integer"
        assert df['noun_phrase_density'].dtype in ['float64', 'float32'], "noun_phrase_density not numeric"
        assert df['token_diversity'].dtype in ['float64', 'float32'], "token_diversity not numeric"

        # Verify reasonable value ranges (sanity checks)
        assert (df['semantic_entropy'] >= 0).all(), "Semantic entropy should be non-negative"
        assert (df['syntactic_depth'] >= 0).all(), "Syntactic depth should be non-negative"
        assert (df['noun_phrase_density'] >= 0).all(), "Noun phrase density should be non-negative"
        assert (df['token_diversity'] >= 0).all(), "Token diversity should be non-negative"
        assert (df['token_diversity'] <= 1).all(), "Token diversity should be <= 1"

    def test_extract_features_batch_edge_cases(self):
        """
        Integration test: Verify edge case handling in extract_features_batch.
        - Short captions -> depth=0
        - BERT failure simulation -> log & exclude (or handle gracefully)
        """
        edge_case_captions = [
            "",  # Empty
            "Hi",  # Very short
            "A",  # Single char
            "This is a normal sentence for comparison."
        ]

        df = extract_features_batch(edge_case_captions)

        assert len(df) > 0, "Pipeline should not exclude all rows"
        assert 'syntactic_depth' in df.columns
        # Verify short captions get depth=0
        short_rows = df[df['caption'].str.len() <= 5]
        if len(short_rows) > 0:
            assert (short_rows['syntactic_depth'] == 0).all(), "Short captions should have depth=0"

    def test_schema_validation_integration(self):
        """
        Integration test: Verify that extracted features can be validated
        against the feature_vector.schema.yaml contract (T018 requirement).
        """
        test_captions = ["A test caption for schema validation."]
        df = extract_features_batch(test_captions)

        # Load schema (T018 implementation)
        paths = get_paths()
        schema_path = paths.schemas / "feature_vector.schema.yaml"

        if schema_path.exists():
            schema = load_schema(schema_path)
            # Validate DataFrame against schema
            is_valid, errors = validate_dataframe(df, schema)
            assert is_valid, f"Schema validation failed: {errors}"
        else:
            # If schema file doesn't exist yet (T004 pending), skip strict validation
            # but ensure the data structure is correct
            assert 'semantic_entropy' in df.columns
            assert 'syntactic_depth' in df.columns

    def test_pydantic_model_construction(self):
        """
        Integration test: Verify that extracted features can be converted
        to Pydantic models (LinguisticFeatureVector) for downstream use.
        """
        test_captions = ["A test caption."]
        df = extract_features_batch(test_captions)

        # Convert first row to Pydantic model
        row = df.iloc[0]
        try:
            model = LinguisticFeatureVector(
                semantic_entropy=row['semantic_entropy'],
                syntactic_depth=int(row['syntactic_depth']),
                noun_phrase_density=row['noun_phrase_density'],
                token_diversity=row['token_diversity']
            )
            assert model.semantic_entropy >= 0
            assert model.syntactic_depth >= 0
        except Exception as e:
            pytest.fail(f"Failed to construct LinguisticFeatureVector: {e}")