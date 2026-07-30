"""
Unit tests for the model_selector module (T004a).
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.model_selector import (
    select_model,
    _check_language_compatibility,
    _load_model_compatibility_matrix,
    REQUIRED_LANGUAGES,
    SELECTION_SEED
)
from src.utils.config import get_candidate_models, reset_config

class TestModelSelector:
    """Tests for deterministic model selection logic."""

    def test_load_compatibility_matrix(self):
        """Test that the compatibility matrix loads correctly."""
        matrix = _load_model_compatibility_matrix()
        assert isinstance(matrix, dict)
        assert "codellama/CodeLlama-7b-Instruct-hf" in matrix
        assert "python" in matrix["codellama/CodeLlama-7b-Instruct-hf"]

    def test_check_language_compatibility_true(self):
        """Test compatibility check returns True when model supports all languages."""
        model = "codellama/CodeLlama-7b-Instruct-hf"
        # This model supports all required languages by definition in the matrix
        assert _check_language_compatibility(model, REQUIRED_LANGUAGES) is True

    def test_check_language_compatibility_false(self):
        """Test compatibility check returns False when model misses a language."""
        # Phi-2 is defined as having limited C/C++ support in our matrix
        model = "microsoft/phi-2"
        # REQUIRED_LANGUAGES includes 'c' and 'cpp'
        assert _check_language_compatibility(model, REQUIRED_LANGUAGES) is False

    @patch('src.utils.model_selector.get_candidate_models')
    @patch('src.utils.model_selector.get_project_root')
    def test_select_model_success(self, mock_root, mock_candidates):
        """Test successful model selection."""
        # Setup mocks
        mock_root.return_value = Path("/fake/project")
        mock_candidates.return_value = [
            "microsoft/phi-2", # Not compatible
            "codellama/CodeLlama-7b-Instruct-hf" # Compatible
        ]

        # Create a temporary directory for logs
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "model_selection.log"
            
            # Mock the open function to avoid file system issues in test
            with patch('src.utils.model_selector.open', create=True) as mock_open:
                mock_open.return_value.__enter__ = lambda s: s
                mock_open.return_value.__exit__ = lambda s, *args: None

                selected = select_model(log_path=log_path)
                
                assert selected == "codellama/CodeLlama-7b-Instruct-hf"
                # Verify log was written (mocked)
                assert mock_open.called

    @patch('src.utils.model_selector.get_candidate_models')
    @patch('src.utils.model_selector.get_project_root')
    def test_select_model_no_compatible(self, mock_root, mock_candidates):
        """Test that selection fails loudly if no compatible model is found."""
        mock_root.return_value = Path("/fake/project")
        # All candidates are incompatible
        mock_candidates.return_value = [
            "microsoft/phi-2", 
            "some/other-small-model"
        ]

        # Mock compatibility check to always return False for these
        with patch('src.utils.model_selector._check_language_compatibility', return_value=False):
            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = Path(tmpdir) / "model_selection.log"
                with patch('src.utils.model_selector.open', create=True) as mock_open:
                    mock_open.return_value.__enter__ = lambda s: s
                    mock_open.return_value.__exit__ = lambda s, *args: None
                    
                    with pytest.raises(ValueError) as excinfo:
                        select_model(log_path=log_path)
                    
                    assert "No compatible model found" in str(excinfo.value)

    def test_seed_is_fixed(self):
        """Verify the selection seed is a constant."""
        assert SELECTION_SEED == 42

    @patch('src.utils.model_selector.get_candidate_models')
    @patch('src.utils.model_selector.get_project_root')
    def test_selection_is_deterministic(self, mock_root, mock_candidates):
        """Test that selection is deterministic across multiple calls."""
        mock_root.return_value = Path("/fake/project")
        mock_candidates.return_value = [
            "codellama/CodeLlama-7b-Instruct-hf",
            "bigcode/starcoder2-3b"
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "model_selection.log"
            with patch('src.utils.model_selector.open', create=True) as mock_open:
                mock_open.return_value.__enter__ = lambda s: s
                mock_open.return_value.__exit__ = lambda s, *args: None

                result1 = select_model(log_path=log_path)
                result2 = select_model(log_path=log_path)

                assert result1 == result2
                assert result1 == "codellama/CodeLlama-7b-Instruct-hf"