"""
Contract and Integration tests for T013: Static QA Extractor.

These tests verify that the static extractor correctly processes real data
from GSM8K and MATH datasets (mocked for unit tests) and writes valid JSONL
files to the expected output paths.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.static_extractor import extract_gsm8k, extract_math, extract_static_qa


class TestStaticExtractor:
    """Tests for the static extractor module."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_gsm8k_basic(self, mock_load_dataset, temp_output_dir):
        """Test basic extraction of GSM8K data."""
        # Mock dataset
        mock_data = [
            {"question": "What is 2+2?", "answer": "The answer is 2+2=4. #### 4"},
            {"question": "What is 3*3?", "answer": "3 times 3 is 9. #### 9"},
        ]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = lambda self: iter(mock_data)
        mock_load_dataset.return_value = mock_dataset

        output_path = temp_output_dir / "gsm8k_test.jsonl"
        count = extract_gsm8k(output_path, limit=2)

        assert count == 2
        assert output_path.exists()

        # Verify content
        with open(output_path, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        
        # Check first record
        rec1 = json.loads(lines[0])
        assert rec1["source"] == "gsm8k"
        assert rec1["question"] == "What is 2+2?"
        assert rec1["answer"] == "4"  # Extracted final answer

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_gsm8k_answer_extraction(self, mock_load_dataset, temp_output_dir):
        """Test that GSM8K answer extraction handles various formats."""
        mock_data = [
            {"question": "Q1", "answer": "Step 1. #### 10"},
            {"question": "Q2", "answer": "Just the answer: 5"},  # No ####
        ]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = lambda self: iter(mock_data)
        mock_load_dataset.return_value = mock_dataset

        output_path = temp_output_dir / "gsm8k_test.jsonl"
        extract_gsm8k(output_path, limit=2)

        with open(output_path, "r") as f:
            recs = [json.loads(line) for line in f]

        assert recs[0]["answer"] == "10"
        assert recs[1]["answer"] == "Just the answer: 5"  # Kept as is

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_math_basic(self, mock_load_dataset, temp_output_dir):
        """Test basic extraction of MATH data."""
        mock_data = [
            {
                "problem": "Find x.",
                "solution": "The solution is \\boxed{42}."
            },
            {
                "problem": "Calculate area.",
                "solution": "Area is 100."  # No boxed
            },
        ]
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = lambda self: iter(mock_data)
        mock_load_dataset.return_value = mock_dataset

        output_path = temp_output_dir / "math_test.jsonl"
        count = extract_math(output_path, limit=2)

        assert count == 2
        assert output_path.exists()

        with open(output_path, "r") as f:
            recs = [json.loads(line) for line in f]

        assert recs[0]["source"] == "math"
        assert recs[0]["answer"] == "42"
        assert recs[1]["answer"] == "Area is 100."

    @patch("src.data.static_extractor.get_config")
    @patch("src.data.static_extractor.extract_gsm8k")
    @patch("src.data.static_extractor.extract_math")
    def test_extract_static_qa_integration(self, mock_math, mock_gsm8k, mock_config, temp_output_dir):
        """Test the main integration function."""
        mock_config.return_value = {
            "data_dir": str(temp_output_dir),
            "data_limit": 10
        }
        mock_gsm8k.return_value = 5
        mock_math.return_value = 3

        results = extract_static_qa()

        assert results["gsm8k"] == 5
        assert results["math"] == 3
        mock_gsm8k.assert_called_once()
        mock_math.assert_called_once()

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_gsm8k_load_error(self, mock_load_dataset, temp_output_dir):
        """Test handling of dataset loading errors."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        output_path = temp_output_dir / "gsm8k_error.jsonl"
        
        with pytest.raises(RuntimeError, match="Failed to load GSM8K dataset"):
            extract_gsm8k(output_path)

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_math_load_error(self, mock_load_dataset, temp_output_dir):
        """Test handling of dataset loading errors."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        output_path = temp_output_dir / "math_error.jsonl"
        
        with pytest.raises(RuntimeError, match="Failed to load MATH dataset"):
            extract_math(output_path)
