"""
Unit tests for T036: verify_model_availability.py
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Import the module under test
# We need to import the functions directly to test them without running main()
from src.cli.verify_model_availability import (
    check_huggingface_model_availability,
    check_local_quantized_models,
    QUANTIZATION_LEVELS
)


class TestCheckHuggingfaceModelAvailability:
    @patch('src.cli.verify_model_availability.model_info')
    def test_model_found(self, mock_model_info):
        mock_info_instance = MagicMock()
        mock_model_info.return_value = mock_info_instance

        exists, msg = check_huggingface_model_availability("test/model")
        assert exists is True
        assert "found" in msg.lower()
        mock_model_info.assert_called_once_with("test/model")

    @patch('src.cli.verify_model_availability.model_info')
    def test_model_not_found_404(self, mock_model_info):
        mock_model_info.side_effect = Exception("404 Client Error: Not Found")

        exists, msg = check_huggingface_model_availability("nonexistent/model")
        assert exists is False
        assert "not found" in msg.lower()

    @patch('src.cli.verify_model_availability.model_info')
    def test_model_not_accessible_401(self, mock_model_info):
        mock_model_info.side_effect = Exception("401 Client Error: Unauthorized")

        exists, msg = check_huggingface_model_availability("private/model")
        assert exists is False
        assert "not accessible" in msg.lower() or "login" in msg.lower()


class TestCheckLocalQuantizedModels:
    def test_all_models_exist(self, tmp_path):
        # Create dummy files
        for level, filename in QUANTIZATION_LEVELS.items():
            file_path = tmp_path / filename
            file_path.touch() # Create empty file

        results = check_local_quantized_models(tmp_path)

        for level in QUANTIZATION_LEVELS:
            assert level in results
            assert results[level][0] is True
            assert "Found" in results[level][1]

    def test_some_models_missing(self, tmp_path):
        # Create only INT4 file
        int4_file = tmp_path / QUANTIZATION_LEVELS["INT4"]
        int4_file.touch()

        results = check_local_quantized_models(tmp_path)

        # INT4 should be found
        assert results["INT4"][0] is True

        # Others should be missing
        assert results["INT8"][0] is False
        assert "Missing" in results["INT8"][1]

        assert results["FP8"][0] is False
        assert "Missing" in results["FP8"][1]

    def test_directory_empty(self, tmp_path):
        results = check_local_quantized_models(tmp_path)

        for level in QUANTIZATION_LEVELS:
            assert results[level][0] is False
            assert "Missing" in results[level][1]

# Note: Testing the main() function with sys.exit requires more complex mocking
# of sys.exit and print, which is often better handled in integration tests.
# These unit tests focus on the logic of the helper functions.