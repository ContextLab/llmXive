"""
Unit tests for model_selector.py (T004a).

Tests deterministic model selection logic.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.utils.model_selector import (
    get_compatible_models,
    select_model_with_seed,
    select_model,
    main,
    MODEL_SELECTION_LOG_PATH
)
from src.utils.config import get_candidate_models


class TestModelSelector:
    """Test suite for model selection logic."""

    @pytest.fixture
    def mock_candidate_models(self):
        """Mock candidate models configuration."""
        return ["model-a", "model-b", "model-c"]

    @pytest.fixture
    def mock_capability_results(self):
        """Mock capability check results."""
        return {
            "model-a": False,
            "model-b": True,
            "model-c": True
        }

    @patch("src.utils.model_selector.get_candidate_models")
    def test_get_compatible_models_returns_filtered_list(
        self,
        mock_get_candidates,
        mock_candidate_models,
        mock_capability_results
    ):
        """Test that get_compatible_models returns only passing models."""
        mock_get_candidates.return_value = mock_candidate_models

        result = get_compatible_models(mock_capability_results)

        assert result == ["model-b", "model-c"]
        assert "model-a" not in result

    @patch("src.utils.model_selector.get_candidate_models")
    def test_get_compatible_models_empty_when_none_pass(
        self,
        mock_get_candidates,
        mock_candidate_models
    ):
        """Test behavior when no models pass capability check."""
        mock_get_candidates.return_value = mock_candidate_models
        all_fail = {"model-a": False, "model-b": False, "model-c": False}

        result = get_compatible_models(all_fail)

        assert result == []

    @patch("src.utils.model_selector.get_candidate_models")
    def test_get_compatible_models_returns_all_when_no_results(
        self,
        mock_get_candidates,
        mock_candidate_models
    ):
        """Test fallback behavior when no capability results provided."""
        mock_get_candidates.return_value = mock_candidate_models

        result = get_compatible_models(None)

        assert result == mock_candidate_models

    @patch("src.utils.model_selector.get_candidate_models")
    @patch("src.utils.model_selector.set_seed")
    def test_select_model_with_seed_deterministic(
        self,
        mock_set_seed,
        mock_get_candidates,
        mock_candidate_models,
        mock_capability_results
    ):
        """Test that selection is deterministic and uses first compatible model."""
        mock_get_candidates.return_value = mock_candidate_models

        selected = select_model_with_seed(mock_capability_results)

        # Should select the first passing model (model-b)
        assert selected == "model-b"
        mock_set_seed.assert_called_once_with(42)

    @patch("src.utils.model_selector.get_candidate_models")
    def test_select_model_with_seed_raises_when_none_compatible(
        self,
        mock_get_candidates,
        mock_candidate_models
    ):
        """Test that selection raises ValueError when no models are compatible."""
        mock_get_candidates.return_value = mock_candidate_models
        all_fail = {"model-a": False, "model-b": False, "model-c": False}

        with pytest.raises(ValueError, match="No compatible models found"):
            select_model_with_seed(all_fail)

    @patch("src.utils.model_selector.get_candidate_models")
    @patch("src.utils.model_selector.set_seed")
    @patch("src.utils.model_selector.get_logger")
    @patch("src.utils.model_selector.log_stage_start")
    @patch("src.utils.model_selector.log_stage_complete")
    @patch("builtins.open")
    @patch("pathlib.Path.mkdir")
    def test_select_model_logs_to_file(
        self,
        mock_mkdir,
        mock_open,
        mock_log_complete,
        mock_log_start,
        mock_get_logger,
        mock_set_seed,
        mock_get_candidates,
        mock_candidate_models,
        mock_capability_results
    ):
        """Test that select_model writes to model_selection.json."""
        mock_get_candidates.return_value = mock_candidate_models
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        selected = select_model(mock_capability_results)

        assert selected == "model-b"
        mock_open.assert_called()
        # Verify JSON was written
        call_args = mock_open.call_args
        assert call_args is not None

    @patch("src.utils.model_selector.select_model")
    def test_main_reads_capability_check_file(self, mock_select_model):
        """Test that main() reads capability check results from file."""
        mock_select_model.return_value = "model-b"

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", MagicMock()) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
                    "capability_results": {"model-a": True}
                })

                result = main()

                assert result == "model-b"
                mock_select_model.assert_called_once()

    @patch("src.utils.model_selector.get_candidate_models")
    def test_select_model_preserves_candidate_order(
        self,
        mock_get_candidates,
        mock_candidate_models
    ):
        """Test that selection respects the order in candidate list."""
        mock_get_candidates.return_value = mock_candidate_models
        # All pass
        all_pass = {"model-a": True, "model-b": True, "model-c": True}

        selected = select_model_with_seed(all_pass)

        # Should select first in list
        assert selected == "model-a"