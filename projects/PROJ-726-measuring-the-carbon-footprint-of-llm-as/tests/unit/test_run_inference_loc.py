"""
Unit tests for run_inference.py functionality, specifically LOC counting and code generation logic.
"""

import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from run_inference import count_loc, generate_code, load_model, load_dataset

class TestLocCounting:
    """Tests for the count_loc function."""

    def test_count_loc_non_empty(self):
        """Test counting lines in a multi-line code string."""
        code = """
        def hello():
            print("Hello")
        """
        assert count_loc(code) == 2

    def test_count_loc_empty_string(self):
        """Test counting lines in an empty string."""
        assert count_loc("") == 0

    def test_count_loc_whitespace_only(self):
        """Test counting lines in whitespace-only string."""
        assert count_loc("   \n  \n   ") == 0

    def test_count_loc_single_line(self):
        """Test counting lines in a single line."""
        assert count_loc("x = 1") == 1

    def test_count_loc_mixed_empty(self):
        """Test counting lines with mixed empty and non-empty lines."""
        code = """
        line1

        line2

        line3
        """
        assert count_loc(code) == 3


class TestModelLoading:
    """Tests for model loading logic (mocked for speed)."""

    def test_load_model_cpu(self, mocker):
        """Test that model loads on CPU."""
        # Mock the transformers classes to avoid actual download
        mock_tokenizer = mocker.patch("run_inference.AutoTokenizer.from_pretrained")
        mock_model = mocker.patch("run_inference.AutoModelForCausalLM.from_pretrained")
        mock_model_instance = mocker.MagicMock()
        mock_model.return_value = mock_model_instance

        model, tokenizer = load_model("gpt2-medium", "cpu")

        mock_model.assert_called_once_with("gpt2-medium")
        mock_model_instance.to.assert_called_once_with("cpu")
        mock_model_instance.eval.assert_called_once()


class TestDatasetLoading:
    """Tests for dataset loading logic."""

    def test_load_dataset_success(self, tmp_path):
        """Test loading a valid dataset."""
        data = [{"prompt_id": "1", "task_id": "test"}]
        file_path = tmp_path / "test.json"
        file_path.write_text("[{\"prompt_id\": \"1\", \"task_id\": \"test\"}]")

        result = load_dataset(file_path)
        assert result == data

    def test_load_dataset_not_found(self, tmp_path):
        """Test loading a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_dataset(tmp_path / "non_existent.json")

    def test_load_dataset_invalid_format(self, tmp_path):
        """Test loading a non-list JSON raises error."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{\"key\": \"value\"}")

        with pytest.raises(ValueError):
            load_dataset(file_path)
