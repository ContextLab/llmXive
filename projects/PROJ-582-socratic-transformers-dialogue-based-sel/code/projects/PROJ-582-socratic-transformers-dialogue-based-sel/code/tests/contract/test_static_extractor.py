"""
Tests for the static QA extractor functionality.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.static_extractor import extract_gsm8k, extract_math, extract_static_qa, write_jsonl


class TestStaticExtractor:
    """Test suite for static QA extraction functions."""

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_gsm8k_success(self, mock_load_dataset):
        """Test successful extraction from GSM8K dataset."""
        # Mock dataset
        mock_dataset = [
            {"question": "What is 2+2?", "answer": "The answer is 4."},
            {"question": "What is 3*3?", "answer": "The answer is 9."},
        ]
        mock_load_dataset.return_value = mock_dataset

        result = extract_gsm8k()

        assert len(result) == 2
        assert result[0]["question"] == "What is 2+2?"
        assert result[0]["answer"] == "The answer is 4."
        assert result[0]["source"] == "gsm8k"
        assert result[1]["source"] == "gsm8k"

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_math_success(self, mock_load_dataset):
        """Test successful extraction from MATH dataset."""
        # Mock dataset
        mock_dataset = [
            {"problem": "Solve for x: x+5=10", "solution": "x=5"},
            {"problem": "What is 5^2?", "solution": "25"},
        ]
        mock_load_dataset.return_value = mock_dataset

        result = extract_math()

        assert len(result) == 2
        assert result[0]["question"] == "Solve for x: x+5=10"
        assert result[0]["answer"] == "x=5"
        assert result[0]["source"] == "math"

    def test_write_jsonl(self):
        """Test writing data to JSONL file."""
        test_data = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test.jsonl"
            write_jsonl(test_data, output_path)

            assert output_path.exists()
            with open(output_path, "r") as f:
                lines = f.readlines()

            assert len(lines) == 2
            parsed_data = [json.loads(line) for line in lines]
            assert parsed_data[0]["question"] == "Q1"
            assert parsed_data[1]["answer"] == "A2"

    @patch("src.data.static_extractor.extract_gsm8k")
    @patch("src.data.static_extractor.extract_math")
    def test_extract_static_qa_integration(self, mock_extract_math, mock_extract_gsm8k):
        """Test the full extraction pipeline."""
        # Mock return values
        mock_extract_gsm8k.return_value = [
            {"question": "GSM8K Q", "answer": "GSM8K A", "source": "gsm8k"}
        ]
        mock_extract_math.return_value = [
            {"question": "MATH Q", "answer": "MATH A", "source": "math"}
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "static_tuples.jsonl"
            result_path = extract_static_qa(output_path)

            assert result_path == output_path
            assert output_path.exists()

            with open(output_path, "r") as f:
                lines = f.readlines()

            assert len(lines) == 2
            parsed = [json.loads(line) for line in lines]
            assert any(item["source"] == "gsm8k" for item in parsed)
            assert any(item["source"] == "math" for item in parsed)

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_gsm8k_empty_fields(self, mock_load_dataset):
        """Test handling of empty question/answer fields."""
        mock_dataset = [
            {"question": "", "answer": "Valid answer"},
            {"question": "Valid question", "answer": ""},
            {"question": "Good question", "answer": "Good answer"},
        ]
        mock_load_dataset.return_value = mock_dataset

        result = extract_gsm8k()

        # Should only include the one with both fields
        assert len(result) == 1
        assert result[0]["question"] == "Good question"

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_math_empty_fields(self, mock_load_dataset):
        """Test handling of empty problem/solution fields in MATH."""
        mock_dataset = [
            {"problem": "", "solution": "Valid solution"},
            {"problem": "Valid problem", "solution": ""},
            {"problem": "Good problem", "solution": "Good solution"},
        ]
        mock_load_dataset.return_value = mock_dataset

        result = extract_math()

        assert len(result) == 1
        assert result[0]["question"] == "Good problem"