"""
Unit tests for axis semantic overlap constraints.

This module tests the validation logic in src/services/axis_validator.py
to ensure Coarse and Fine axes are sufficiently independent.

Dependencies:
  - T010 (axis.schema.yaml) for schema reference
  - T012 (axis_validator.py) for validation logic
"""
import pytest
import math
from unittest.mock import patch, MagicMock
import numpy as np

from src.services.axis_validator import (
    load_sentence_model_cached,
    preprocess_text,
    calculate_lexical_overlap,
    calculate_semantic_distance,
    validate_coarse_fine_independence,
    validate_source_observation_distinctness,
    validate_axis_definition
)


class TestPreprocessText:
    """Tests for text preprocessing utility."""

    def test_lowercases_input(self):
        result = preprocess_text("Hello WORLD")
        assert result == "hello world"

    def test_removes_punctuation(self):
        result = preprocess_text("Hello, world! How are you?")
        # Punctuation should be stripped, leaving only words and spaces
        assert "!" not in result
        assert "," not in result
        assert "?" not in result
        assert "." not in result

    def test_handles_empty_string(self):
        result = preprocess_text("")
        assert result == ""

    def test_handles_whitespace_only(self):
        result = preprocess_text("   \t\n   ")
        assert result == ""

    def test_removes_multiple_spaces(self):
        result = preprocess_text("Hello    World")
        assert "  " not in result


class TestLexicalOverlap:
    """Tests for Jaccard similarity calculation."""

    def test_identical_texts(self):
        """Jaccard similarity of identical sets is 1.0."""
        text1 = "the quick brown fox"
        text2 = "the quick brown fox"
        overlap = calculate_lexical_overlap(text1, text2)
        assert abs(overlap - 1.0) < 1e-6

    def test_no_overlap(self):
        """Jaccard similarity of disjoint sets is 0.0."""
        text1 = "apple banana cherry"
        text2 = "dog cat fish"
        overlap = calculate_lexical_overlap(text1, text2)
        assert abs(overlap - 0.0) < 1e-6

    def test_partial_overlap(self):
        """Test partial overlap calculation."""
        # Set A: {the, quick, brown, fox}
        # Set B: {the, quick, red, car}
        # Intersection: {the, quick} -> 2
        # Union: {the, quick, brown, fox, red, car} -> 6
        # Jaccard: 2/6 = 0.333...
        text1 = "the quick brown fox"
        text2 = "the quick red car"
        overlap = calculate_lexical_overlap(text1, text2)
        expected = 2.0 / 6.0
        assert abs(overlap - expected) < 1e-6

    def test_case_insensitivity(self):
        """Overlap calculation should be case-insensitive."""
        text1 = "Hello World"
        text2 = "hello world"
        overlap = calculate_lexical_overlap(text1, text2)
        assert abs(overlap - 1.0) < 1e-6

    def test_empty_input(self):
        """Empty inputs should result in 0.0 overlap."""
        overlap = calculate_lexical_overlap("", "")
        assert overlap == 0.0

    def test_one_empty_input(self):
        """One empty input should result in 0.0 overlap."""
        overlap = calculate_lexical_overlap("hello", "")
        assert overlap == 0.0


class TestSemanticDistance:
    """Tests for semantic distance calculation using embeddings."""

    @patch('src.services.axis_validator.load_sentence_model_cached')
    def test_identical_embeddings_zero_distance(self, mock_model_loader):
        """Cosine distance of identical vectors is 0.0."""
        mock_model = MagicMock()
        mock_model_loader.return_value = mock_model
        
        # Mock embeddings to be identical
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        mock_model.encode.side_effect = [vec1, vec2]

        distance = calculate_semantic_distance("hello", "hello")
        assert abs(distance - 0.0) < 1e-6

    @patch('src.services.axis_validator.load_sentence_model_cached')
    def test_opposite_embeddings_max_distance(self, mock_model_loader):
        """Cosine distance of opposite vectors is 2.0 (1 - (-1))."""
        mock_model = MagicMock()
        mock_model_loader.return_value = mock_model
        
        # Mock embeddings to be opposite
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([-1.0, 0.0, 0.0])
        mock_model.encode.side_effect = [vec1, vec2]

        distance = calculate_semantic_distance("hello", "goodbye")
        # Cosine similarity = -1, so distance = 1 - (-1) = 2
        assert abs(distance - 2.0) < 1e-6

    @patch('src.services.axis_validator.load_sentence_model_cached')
    def test_orthogonal_embeddings_one_distance(self, mock_model_loader):
        """Cosine distance of orthogonal vectors is 1.0."""
        mock_model = MagicMock()
        mock_model_loader.return_value = mock_model
        
        # Mock embeddings to be orthogonal
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.0, 1.0, 0.0])
        mock_model.encode.side_effect = [vec1, vec2]

        distance = calculate_semantic_distance("hello", "world")
        # Cosine similarity = 0, so distance = 1 - 0 = 1
        assert abs(distance - 1.0) < 1e-6

    @patch('src.services.axis_validator.load_sentence_model_cached')
    def test_partial_similarity(self, mock_model_loader):
        """Test with partially similar vectors."""
        mock_model = MagicMock()
        mock_model_loader.return_value = mock_model
        
        # Vectors with cosine similarity of 0.5
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([0.5, math.sqrt(0.75), 0.0])  # norm = 1, dot = 0.5
        mock_model.encode.side_effect = [vec1, vec2]

        distance = calculate_semantic_distance("text1", "text2")
        # Cosine similarity = 0.5, so distance = 1 - 0.5 = 0.5
        assert abs(distance - 0.5) < 1e-6


class TestValidationLogic:
    """Integration tests for the full validation pipeline."""

    @patch('src.services.axis_validator.load_sentence_model_cached')
    def test_valid_independent_axes(self, mock_model_loader):
        """Test that sufficiently different axes pass validation."""
        mock_model = MagicMock()
        mock_model_loader.return_value = mock_model
        
        # Mock lexical overlap > 0.4 (e.g., 0.5)
        with patch('src.services.axis_validator.calculate_lexical_overlap', return_value=0.5):
            # Mock semantic distance < 0.3 (e.g., 0.2)
            with patch('src.services.axis_validator.calculate_semantic_distance', return_value=0.2):
                coarse = {
                    "character": "Elizabeth Bennet",
                    "axis_name": "Innocence",
                    "description": "She is naive, trusting, and optimistic about people's intentions."
                }
                fine = {
                    "character": "Elizabeth Bennet",
                    "axis_name": "Experience",
                    "description": "She is cautious, skeptical, and carefully evaluates people's character.",
                    "source_observation": "Her realization of Wickham's true nature after Darcy's letter."
                }
                
                is_valid, reason = validate_coarse_fine_independence(coarse, fine)
                
                assert is_valid is True
                assert "failed" not in reason.lower()

    @patch('src.services.axis_validator.load_sentence_model_cached')
    def test_axes_too_lexically_similar(self, mock_model_loader):
        """Test that axes with high lexical overlap fail."""
        mock_model = MagicMock()
        mock_model_loader.return_value = mock_model
        
        # Mock lexical overlap < 0.4 (e.g., 0.3)
        with patch('src.services.axis_validator.calculate_lexical_overlap', return_value=0.3):
            # Mock semantic distance < 0.3 (e.g., 0.2)
            with patch('src.services.axis_validator.calculate_semantic_distance', return_value=0.2):
                coarse = {
                    "character": "Elizabeth Bennet",
                    "axis_name": "Kindness",
                    "description": "She is kind and helpful to others."
                }
                fine = {
                    "character": "Elizabeth Bennet",
                    "axis_name": "Kindness-Refined",
                    "description": "She is kind and helpful to people.",
                    "source_observation": "She helps her sister Jane."
                }
                
                is_valid, reason = validate_coarse_fine_independence(coarse, fine)
                
                assert is_valid is False
                assert "lexical" in reason.lower()

    @patch('src.services.axis_validator.load_sentence_model_cached')
    def test_axes_semantically_too_similar(self, mock_model_loader):
        """Test that axes with low semantic distance fail."""
        mock_model = MagicMock()
        mock_model_loader.return_value = mock_model
        
        # Mock lexical overlap > 0.4 (e.g., 0.5)
        with patch('src.services.axis_validator.calculate_lexical_overlap', return_value=0.5):
            # Mock semantic distance >= 0.3 (e.g., 0.4)
            with patch('src.services.axis_validator.calculate_semantic_distance', return_value=0.4):
                coarse = {
                    "character": "Elizabeth Bennet",
                    "axis_name": "Intelligence",
                    "description": "She is very smart and perceptive."
                }
                fine = {
                    "character": "Elizabeth Bennet",
                    "axis_name": "Perception",
                    "description": "She is very smart and perceptive about others.",
                    "source_observation": "She notices Darcy's pride immediately."
                }
                
                is_valid, reason = validate_coarse_fine_independence(coarse, fine)
                
                assert is_valid is False
                assert "semantic" in reason.lower() or "distance" in reason.lower()

    @patch('src.services.axis_validator.load_sentence_model_cached')
    def test_both_constraints_violated(self, mock_model_loader):
        """Test failure when both lexical and semantic constraints are violated."""
        mock_model = MagicMock()
        mock_model_loader.return_value = mock_model
        
        with patch('src.services.axis_validator.calculate_lexical_overlap', return_value=0.2):
            with patch('src.services.axis_validator.calculate_semantic_distance', return_value=0.8):
                coarse = {
                    "character": "Elizabeth Bennet",
                    "axis_name": "Test",
                    "description": "A test description."
                }
                fine = {
                    "character": "Elizabeth Bennet",
                    "axis_name": "Test",
                    "description": "A test description.",
                    "source_observation": "Observation."
                }
                
                is_valid, reason = validate_coarse_fine_independence(coarse, fine)
                
                assert is_valid is False
                # Should mention both issues or the first one encountered
                assert "failed" in reason.lower()

    def test_missing_source_observation(self):
        """Test that missing source_observation fails distinctness check."""
        fine = {
            "character": "Elizabeth Bennet",
            "axis_name": "Experience",
            "description": "She is cautious."
            # Missing source_observation
        }
        
        is_valid, reason = validate_source_observation_distinctness(fine)
        
        assert is_valid is False
        assert "source_observation" in reason.lower()

    def test_empty_source_observation(self):
        """Test that empty source_observation fails distinctness check."""
        fine = {
            "character": "Elizabeth Bennet",
            "axis_name": "Experience",
            "description": "She is cautious.",
            "source_observation": ""
        }
        
        is_valid, reason = validate_source_observation_distinctness(fine)
        
        assert is_valid is False

    def test_valid_source_observation(self):
        """Test that valid source_observation passes."""
        fine = {
            "character": "Elizabeth Bennet",
            "axis_name": "Experience",
            "description": "She is cautious.",
            "source_observation": "After reading Darcy's letter, she re-evaluates Wickham's character."
        }
        
        is_valid, reason = validate_source_observation_distinctness(fine)
        
        assert is_valid is True

    @patch('src.services.axis_validator.load_sentence_model_cached')
    def test_full_axis_definition_valid(self, mock_model_loader):
        """Test complete axis definition validation with valid inputs."""
        mock_model = MagicMock()
        mock_model_loader.return_value = mock_model
        
        coarse = {
            "character": "Elizabeth Bennet",
            "axis_name": "Innocence",
            "description": "She is naive, trusting, and optimistic."
        }
        fine = {
            "character": "Elizabeth Bennet",
            "axis_name": "Experience",
            "description": "She is cautious, skeptical, and analytical.",
            "source_observation": "Her change of heart after Darcy's letter."
        }
        
        with patch('src.services.axis_validator.calculate_lexical_overlap', return_value=0.5):
            with patch('src.services.axis_validator.calculate_semantic_distance', return_value=0.2):
                is_valid, reason = validate_axis_definition(coarse, fine)
                
                assert is_valid is True

    @patch('src.services.axis_validator.load_sentence_model_cached')
    def test_full_axis_definition_invalid_overlap(self, mock_model_loader):
        """Test complete axis definition validation with invalid overlap."""
        mock_model = MagicMock()
        mock_model_loader.return_value = mock_model
        
        coarse = {
            "character": "Elizabeth Bennet",
            "axis_name": "Kindness",
            "description": "She is kind and helpful."
        }
        fine = {
            "character": "Elizabeth Bennet",
            "axis_name": "Kindness",
            "description": "She is kind and helpful.",
            "source_observation": "She helps her sister."
        }
        
        with patch('src.services.axis_validator.calculate_lexical_overlap', return_value=0.3):
            with patch('src.services.axis_validator.calculate_semantic_distance', return_value=0.1):
                is_valid, reason = validate_axis_definition(coarse, fine)
                
                assert is_valid is False

    def test_missing_coarse_field(self):
        """Test validation when coarse definition is missing required fields."""
        coarse = {
            "character": "Elizabeth Bennet"
            # Missing axis_name and description
        }
        fine = {
            "character": "Elizabeth Bennet",
            "axis_name": "Experience",
            "description": "She is cautious.",
            "source_observation": "Observation."
        }
        
        # This should fail due to missing required fields in coarse
        is_valid, reason = validate_axis_definition(coarse, fine)
        assert is_valid is False

    def test_missing_fine_field(self):
        """Test validation when fine definition is missing required fields."""
        coarse = {
            "character": "Elizabeth Bennet",
            "axis_name": "Innocence",
            "description": "She is naive."
        }
        fine = {
            "character": "Elizabeth Bennet"
            # Missing axis_name, description, and source_observation
        }
        
        is_valid, reason = validate_axis_definition(coarse, fine)
        assert is_valid is False