"""
Unit tests for the Missing Modality Handler (T039).
"""

import pytest
import logging
from unittest.mock import patch

from src.utils.missing_handler import (
    handle_missing_modality,
    build_input_payload,
    MISSING_MODALITY_PLACEHOLDER
)


class TestHandleMissingModality:
    """Tests for handle_missing_modality function."""

    def test_heterogeneous_condition_returns_none(self):
        """Test that heterogeneous condition returns None (skip)."""
        result = handle_missing_modality("T001", "image", "heterogeneous")
        assert result is None

    def test_unified_condition_returns_placeholder_string(self):
        """Test that unified condition returns a placeholder string."""
        result = handle_missing_modality("T002", "text", "unified")
        assert isinstance(result, str)
        assert MISSING_MODALITY_PLACEHOLDER in result
        assert "T002" in result
        assert "text" in result

    def test_invalid_condition_raises_value_error(self):
        """Test that invalid condition raises ValueError."""
        with pytest.raises(ValueError, match="condition must be"):
            handle_missing_modality("T003", "tabular", "invalid_mode")

    def test_empty_task_id_raises_value_error(self):
        """Test that empty task_id raises ValueError."""
        with pytest.raises(ValueError, match="task_id must be"):
            handle_missing_modality("", "image", "unified")

    def test_empty_modality_raises_value_error(self):
        """Test that empty missing_modality raises ValueError."""
        with pytest.raises(ValueError, match="missing_modality must be"):
            handle_missing_modality("T004", "", "unified")

    @patch('src.utils.missing_handler.logger')
    def test_logging_format_correct(self, mock_logger):
        """Test that the warning log format matches requirements."""
        handle_missing_modality("TASK-XYZ", "audio", "heterogeneous")
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "WARNING: Missing modality audio for task TASK-XYZ" == call_args


class TestBuildInputPayload:
    """Tests for build_input_payload function."""

    def test_no_missing_modalities_returns_copy(self):
        """Test behavior when no modalities are missing."""
        input_data = {"text": "hello", "image": "data"}
        result = build_input_payload("T001", input_data, [], "unified")
        assert result == input_data
        assert result is not input_data  # Should be a copy

    def test_heterogeneous_missing_sets_none(self):
        """Test that missing modalities in heterogeneous mode are set to None."""
        input_data = {"text": "hello"}
        missing = ["image"]
        result = build_input_payload("T001", input_data, missing, "heterogeneous")
        assert result["text"] == "hello"
        assert result["image"] is None

    def test_unified_missing_sets_placeholder(self):
        """Test that missing modalities in unified mode get placeholder string."""
        input_data = {"text": "hello"}
        missing = ["image"]
        result = build_input_payload("T001", input_data, missing, "unified")
        assert result["text"] == "hello"
        assert isinstance(result["image"], str)
        assert MISSING_MODALITY_PLACEHOLDER in result["image"]

    def test_missing_modality_already_in_payload_skipped(self):
        """Test that if a modality is already in payload, it is not overwritten."""
        input_data = {"text": "hello", "image": "existing_data"}
        missing = ["image"]  # Listed as missing but present in data
        result = build_input_payload("T001", input_data, missing, "unified")
        # Should remain "existing_data", not be replaced by placeholder
        assert result["image"] == "existing_data"
        assert MISSING_MODALITY_PLACEHOLDER not in result["image"]