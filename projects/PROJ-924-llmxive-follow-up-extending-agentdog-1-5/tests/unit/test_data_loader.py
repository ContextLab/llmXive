"""
Unit tests for data_loader module.
Tests streaming fetch functions and error handling.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.data_loader import (
    LoudFailureError,
    fetch_advbench,
    fetch_hf4,
    load_jsonl_file,
    save_jsonl_file,
)


class TestFetchAdvBench:
    """Tests for fetch_advbench function."""

    def test_fetch_advbench_success(self):
        """Test successful fetch of AdvBench dataset."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"text": "Sample jailbreak attempt 1"},
            {"text": "Sample jailbreak attempt 2"},
        ]))

        with patch("code.data_loader.load_dataset", return_value=mock_dataset):
            result = fetch_advbench()

        assert len(result) == 2
        assert result[0]["label"] == "jailbreak"
        assert result[1]["label"] == "jailbreak"
        assert "text" in result[0]

    def test_fetch_advbench_missing_text_field(self):
        """Test that missing 'text' field raises LoudFailureError."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"wrong_field": "test"},
        ]))

        with patch("code.data_loader.load_dataset", return_value=mock_dataset):
            with pytest.raises(LoudFailureError, match="missing 'text' field"):
                fetch_advbench()

    def test_fetch_advbench_empty_dataset(self):
        """Test that empty dataset raises LoudFailureError."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([]))

        with patch("code.data_loader.load_dataset", return_value=mock_dataset):
            with pytest.raises(LoudFailureError, match="returned empty results"):
                fetch_advbench()

    def test_fetch_advbench_network_failure(self):
        """Test that network failure raises LoudFailureError."""
        with patch("code.data_loader.load_dataset", side_effect=Exception("Network error")):
            with pytest.raises(LoudFailureError, match="Failed to fetch AdvBench"):
                fetch_advbench()

    def test_fetch_advbench_saves_to_file(self):
        """Test that fetch_advbench saves to file when output_path provided."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"text": "Sample jailbreak attempt"},
        ]))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_advbench.jsonl"
            with patch("code.data_loader.load_dataset", return_value=mock_dataset):
                result = fetch_advbench(output_path)

            assert result[0]["text"] == "Sample jailbreak attempt"
            assert output_path.exists()
            
            # Verify file content
            loaded = load_jsonl_file(output_path)
            assert len(loaded) == 1
            assert loaded[0]["label"] == "jailbreak"


class TestFetchHF4:
    """Tests for fetch_hf4 function."""

    def test_fetch_hf4_success(self):
        """Test successful fetch of HF4 dataset."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"text": "Sample safe response 1"},
            {"text": "Sample safe response 2"},
        ]))

        with patch("code.data_loader.load_dataset", return_value=mock_dataset):
            result = fetch_hf4()

        assert len(result) == 2
        assert result[0]["label"] == "safe"
        assert result[1]["label"] == "safe"
        assert "text" in result[0]

    def test_fetch_hf4_missing_text_field(self):
        """Test that missing 'text' field raises LoudFailureError."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"wrong_field": "test"},
        ]))

        with patch("code.data_loader.load_dataset", return_value=mock_dataset):
            with pytest.raises(LoudFailureError, match="missing 'text' field"):
                fetch_hf4()

    def test_fetch_hf4_empty_dataset(self):
        """Test that empty dataset raises LoudFailureError."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([]))

        with patch("code.data_loader.load_dataset", return_value=mock_dataset):
            with pytest.raises(LoudFailureError, match="returned empty results"):
                fetch_hf4()

    def test_fetch_hf4_network_failure(self):
        """Test that network failure raises LoudFailureError."""
        with patch("code.data_loader.load_dataset", side_effect=Exception("Network error")):
            with pytest.raises(LoudFailureError, match="Failed to fetch HF4"):
                fetch_hf4()

    def test_fetch_hf4_saves_to_file(self):
        """Test that fetch_hf4 saves to file when output_path provided."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"text": "Sample safe response"},
        ]))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_hf4.jsonl"
            with patch("code.data_loader.load_dataset", return_value=mock_dataset):
                result = fetch_hf4(output_path)

            assert result[0]["text"] == "Sample safe response"
            assert output_path.exists()
            
            # Verify file content
            loaded = load_jsonl_file(output_path)
            assert len(loaded) == 1
            assert loaded[0]["label"] == "safe"


class TestJSONLFileIO:
    """Tests for JSONL file I/O functions."""

    def test_save_and_load_jsonl_file(self):
        """Test round-trip save and load of JSONL file."""
        test_data = [
            {"text": "Sample 1", "label": "jailbreak"},
            {"text": "Sample 2", "label": "safe"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"
            
            save_jsonl_file(test_data, file_path)
            assert file_path.exists()
            
            loaded_data = load_jsonl_file(file_path)
            assert len(loaded_data) == 2
            assert loaded_data[0]["text"] == "Sample 1"
            assert loaded_data[1]["label"] == "safe"

    def test_load_jsonl_file_missing_file(self):
        """Test that loading missing file raises LoudFailureError."""
        with pytest.raises(LoudFailureError, match="not found"):
            load_jsonl_file(Path("/nonexistent/file.jsonl"))

    def test_load_jsonl_file_invalid_json(self):
        """Test that invalid JSON raises LoudFailureError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "invalid.jsonl"
            with open(file_path, "w") as f:
                f.write("not valid json\n")
            
            with pytest.raises(LoudFailureError, match="Invalid JSON"):
                load_jsonl_file(file_path)
