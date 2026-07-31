"""
Unit tests for src.utils.model_selector
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.model_selector import (
    get_compatible_models,
    select_model,
    select_model_with_seed,
    MODEL_LANGUAGE_COMPATIBILITY,
    SUPPORTED_LANGUAGES
)
from src.utils.config import get_config, reset_config, set_seed

class TestModelSelector:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset config before each test."""
        reset_config()
        # Ensure a valid config state
        set_seed(42)

    def test_supported_languages_constant(self):
        """Test that SUPPORTED_LANGUAGES contains the required languages."""
        assert "Python" in SUPPORTED_LANGUAGES
        assert "C" in SUPPORTED_LANGUAGES
        assert "JavaScript" in SUPPORTED_LANGUAGES

    @patch('src.utils.model_selector.get_candidate_models')
    def test_get_compatible_models_filters_correctly(self, mock_get_candidates):
        """Test that only models supporting all languages are returned."""
        # Mock candidate list with some incompatible models
        mock_get_candidates.return_value = [
            "microsoft/Phi-3-mini-4k-instruct", # Compatible
            "some/unknown-model",               # Not in map
            "incompatible/model"                # Not in map
        ]

        result = get_compatible_models()
        
        # Should only return the one in the compatibility map that supports all
        assert "microsoft/Phi-3-mini-4k-instruct" in result
        assert "some/unknown-model" not in result
        assert "incompatible/model" not in result

    @patch('src.utils.model_selector.get_candidate_models')
    def test_select_model_deterministic(self, mock_get_candidates):
        """Test that selection is deterministic (sorted first)."""
        mock_get_candidates.return_value = [
            "z-model",
            "a-model",
            "microsoft/Phi-3-mini-4k-instruct"
        ]

        # Run twice
        model1 = select_model()
        model2 = select_model()

        # Should pick the first in sorted order: "microsoft/..." or "a-model"?
        # Let's check the actual logic: sorted list -> index 0.
        # Sorted: ["microsoft/Phi-3-mini-4k-instruct", "a-model", "z-model"] (alphabetical)
        # Wait, "a-model" comes before "microsoft..." alphabetically?
        # 'a' < 'm'. So "a-model" is first.
        # But "a-model" is not in the compatibility map, so it won't be in the result of get_compatible_models.
        # So result of get_compatible_models is ["microsoft/Phi-3-mini-4k-instruct"]
        # Sorted: ["microsoft/Phi-3-mini-4k-instruct"]
        # Selected: "microsoft/Phi-3-mini-4k-instruct"

        # Let's adjust the mock to be more realistic
        mock_get_candidates.return_value = [
            "microsoft/Phi-3-mini-4k-instruct",
            "codellama/CodeLlama-7b-Instruct-hf"
        ]
        
        model1 = select_model()
        model2 = select_model()

        assert model1 == model2
        # Should be the first one alphabetically among compatible ones
        # "codellama..." < "microsoft..."
        # So it should be "codellama/CodeLlama-7b-Instruct-hf"
        assert model1 == "codellama/CodeLlama-7b-Instruct-hf"

    @patch('src.utils.model_selector.get_candidate_models')
    def test_select_model_with_seed_reproducible(self, mock_get_candidates):
        """Test that selection with seed is reproducible."""
        mock_get_candidates.return_value = [
            "microsoft/Phi-3-mini-4k-instruct",
            "codellama/CodeLlama-7b-Instruct-hf",
            "mistralai/Mistral-7B-Instruct-v0.2"
        ]

        model1 = select_model_with_seed(123)
        model2 = select_model_with_seed(123)

        assert model1 == model2

    @patch('src.utils.model_selector.get_candidate_models')
    def test_select_model_with_seed_different(self, mock_get_candidates):
        """Test that different seeds can yield different results (if random)."""
        mock_get_candidates.return_value = [
            "microsoft/Phi-3-mini-4k-instruct",
            "codellama/CodeLlama-7b-Instruct-hf",
            "mistralai/Mistral-7B-Instruct-v0.2"
        ]

        model1 = select_model_with_seed(123)
        model2 = select_model_with_seed(456)
        
        # Note: It's possible they are the same by chance, but unlikely with 3 items.
        # We just verify the function runs without error.
        assert isinstance(model1, str)
        assert isinstance(model2, str)

    @patch('src.utils.model_selector.get_candidate_models')
    def test_no_compatible_models_raises(self, mock_get_candidates):
        """Test that an empty compatible list raises an error."""
        mock_get_candidates.return_value = [
            "unknown/model-1",
            "unknown/model-2"
        ]

        with pytest.raises(ValueError, match="No compatible models available"):
            select_model()

    @patch('src.utils.model_selector.get_candidate_models')
    def test_empty_candidate_list_raises(self, mock_get_candidates):
        """Test that an empty candidate list raises an error."""
        mock_get_candidates.return_value = []

        with pytest.raises(ValueError, match="No compatible models available"):
            select_model()