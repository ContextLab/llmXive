"""
Unit tests for the Model Selector module.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.model_selector import select_model, get_compatible_models, SUPPORTED_LANGUAGES, PRIMARY_MODEL_ID
from src.utils.config import CANDIDATE_MODELS


class TestModelSelector:
    """Tests for model selection logic."""

    def test_select_model_single_language(self):
        """Test selection with a single supported language."""
        model = select_model(["python"])
        assert model == PRIMARY_MODEL_ID

    def test_select_model_multiple_languages(self):
        """Test selection with multiple supported languages."""
        model = select_model(["python", "c", "javascript"])
        assert model == PRIMARY_MODEL_ID

    def test_select_model_unsupported_language(self):
        """Test selection fails when no model supports the language."""
        # Simulate a language not in SUPPORTED_LANGUAGES
        # We need to mock get_compatible_models to return empty for this specific case
        # or rely on the logic in get_compatible_models if it strictly filters.
        # Since get_compatible_models currently only returns PRIMARY_MODEL_ID if
        # the input is a subset of SUPPORTED_LANGUAGES, passing an unsupported lang
        # should result in an empty list.
        
        # Note: The current implementation of get_compatible_models returns []
        # if the input languages are not a subset of SUPPORTED_LANGUAGES.
        with pytest.raises(ValueError) as exc_info:
            select_model(["cobol"])
        
        assert "No compatible model found" in str(exc_info.value)

    def test_select_model_deterministic(self):
        """Test that selection is deterministic across calls."""
        model1 = select_model(["python", "c"])
        model2 = select_model(["python", "c"])
        assert model1 == model2

    def test_get_compatible_models_empty_input(self):
        """Test compatibility check with empty list."""
        result = get_compatible_models([])
        assert result == []

    def test_get_compatible_models_subset(self):
        """Test that a subset of supported languages returns the model."""
        result = get_compatible_models(["python"])
        assert PRIMARY_MODEL_ID in result

    def test_get_compatible_models_superset(self):
        """Test that a superset of supported languages returns empty."""
        # If we pass a language not in SUPPORTED_LANGUAGES, it should return empty
        result = get_compatible_models(["python", "unknown_lang"])
        assert result == []

if __name__ == "__main__":
    pytest.main([__file__, "-v"])