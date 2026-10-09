"""
Unit tests for axis validation logic (T012).
"""

import math
from unittest.mock import patch

import numpy as np

# Import the functions to test
from src.services.axis_validator import (
    calculate_lexical_overlap,
    calculate_semantic_distance,
    preprocess_text,
    validate_axis_definition,
    validate_coarse_fine_independence,
    validate_source_observation_distinctness,
)


class TestPreprocessText:
    def test_basic_tokenization(self):
        text = "Hello, world! This is a test."
        tokens = preprocess_text(text)
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
        assert "," not in tokens
        assert "!" not in tokens

    def test_empty_string(self):
        assert preprocess_text("") == []

    def test_non_string_input(self):
        assert preprocess_text(123) == []


class TestLexicalOverlap:
    def test_identical_texts(self):
        text = "the quick brown fox"
        overlap = calculate_lexical_overlap(text, text)
        assert overlap == 1.0

    def test_no_overlap(self):
        text_a = "apple banana"
        text_b = "cherry date"
        overlap = calculate_lexical_overlap(text_a, text_b)
        assert overlap == 0.0

    def test_partial_overlap(self):
        text_a = "apple banana cherry"
        text_b = "banana cherry date"
        # Union: {apple, banana, cherry, date} (4)
        # Intersection: {banana, cherry} (2)
        # Jaccard = 2/4 = 0.5
        overlap = calculate_lexical_overlap(text_a, text_b)
        assert math.isclose(overlap, 0.5)


class TestSemanticDistance:
    @patch("src.services.axis_validator.load_sentence_model_cached")
    def test_identical_embeddings(self, mock_model):
        # Mock the model to return identical vectors
        mock_emb = np.array([[1.0, 0.0], [1.0, 0.0]])
        mock_model.return_value.encode.return_value = mock_emb

        dist = calculate_semantic_distance("test", "test")
        assert dist == 0.0

    @patch("src.services.axis_validator.load_sentence_model_cached")
    def test_opposite_embeddings(self, mock_model):
        # Mock the model to return opposite vectors
        mock_emb = np.array([[1.0, 0.0], [-1.0, 0.0]])
        mock_model.return_value.encode.return_value = mock_emb

        dist = calculate_semantic_distance("test", "test")
        # Cosine similarity = -1, Distance = 1 - (-1) = 2.0
        assert dist == 2.0

    @patch("src.services.axis_validator.load_sentence_model_cached")
    def test_orthogonal_embeddings(self, mock_model):
        # Mock the model to return orthogonal vectors
        mock_emb = np.array([[1.0, 0.0], [0.0, 1.0]])
        mock_model.return_value.encode.return_value = mock_emb

        dist = calculate_semantic_distance("test", "test")
        # Cosine similarity = 0, Distance = 1.0
        assert dist == 1.0


class TestValidationLogic:
    def test_validate_coarse_fine_independence_pass(self):
        # Mock the functions to return passing values
        with (
            patch("src.services.axis_validator.calculate_lexical_overlap", return_value=0.5),
            patch("src.services.axis_validator.calculate_semantic_distance", return_value=0.2),
        ):

            is_valid, metrics = validate_coarse_fine_independence("desc1", "desc2")
            assert is_valid is True
            assert metrics["lexical_pass"] is True
            assert metrics["semantic_pass"] is True

    def test_validate_coarse_fine_independence_fail_lexical(self):
        with (
            patch("src.services.axis_validator.calculate_lexical_overlap", return_value=0.3),
            patch("src.services.axis_validator.calculate_semantic_distance", return_value=0.2),
        ):

            is_valid, metrics = validate_coarse_fine_independence("desc1", "desc2")
            assert is_valid is False
            assert metrics["lexical_pass"] is False

    def test_validate_coarse_fine_independence_fail_semantic(self):
        with (
            patch("src.services.axis_validator.calculate_lexical_overlap", return_value=0.5),
            patch("src.services.axis_validator.calculate_semantic_distance", return_value=0.4),
        ):

            is_valid, metrics = validate_coarse_fine_independence("desc1", "desc2")
            assert is_valid is False
            assert metrics["semantic_pass"] is False

    def test_validate_source_observation_distinctness_pass(self):
        with patch("src.services.axis_validator.calculate_lexical_overlap", return_value=0.5):
            is_valid, metrics = validate_source_observation_distinctness(
                "fine desc", "different observation"
            )
            assert is_valid is True
            assert metrics["source_observation_distinct"] is True

    def test_validate_source_observation_distinctness_empty(self):
        is_valid, metrics = validate_source_observation_distinctness("fine desc", "")
        assert is_valid is False
        assert metrics["source_observation_distinct"] is False

    def test_validate_source_observation_distinctness_too_similar(self):
        with patch("src.services.axis_validator.calculate_lexical_overlap", return_value=0.9):
            is_valid, metrics = validate_source_observation_distinctness("fine desc", "fine desc")
            assert is_valid is False
            assert metrics["source_observation_distinct"] is False

    def test_validate_axis_definition_full_pass(self):
        axis_data = {
            "coarse": {"description": "Coarse description here"},
            "fine": {
                "description": "Fine description here",
                "source_observation": "Some observation",
            },
        }

        with (
            patch("src.services.axis_validator.calculate_lexical_overlap", return_value=0.5),
            patch("src.services.axis_validator.calculate_semantic_distance", return_value=0.2),
        ):

            is_valid, result = validate_axis_definition(axis_data)
            assert is_valid is True
            assert len(result["errors"]) == 0

    def test_validate_axis_definition_full_fail(self):
        axis_data = {
            "coarse": {"description": "Coarse description here"},
            "fine": {
                "description": "Fine description here",
                "source_observation": "Some observation",
            },
        }

        with (
            patch("src.services.axis_validator.calculate_lexical_overlap", return_value=0.3),
            patch("src.services.axis_validator.calculate_semantic_distance", return_value=0.2),
        ):

            is_valid, result = validate_axis_definition(axis_data)
            assert is_valid is False
            assert "Coarse and Fine descriptions fail independence constraints." in result["errors"]
