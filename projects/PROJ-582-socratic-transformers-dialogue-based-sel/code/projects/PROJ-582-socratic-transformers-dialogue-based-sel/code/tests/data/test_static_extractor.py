"""
Tests for the static QA extractor module.

These tests verify that the static_extractor module correctly extracts
(question, answer) tuples from GSM8K and MATH datasets and writes them
to JSONL files.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.data.static_extractor import extract_gsm8k, extract_math, extract_static_qa


class TestStaticExtractor:
    """Test cases for static QA extraction functionality."""

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_gsm8k_basic(self, mock_load_dataset):
        """Test basic GSM8K extraction with mocked data."""
        # Mock the dataset
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"question": "What is 2+2?", "answer": "The answer is 4. The final answer is 4."},
            {"question": "What is 3+3?", "answer": "The answer is 6. The final answer is 6."},
        ]))
        mock_load_dataset.return_value = mock_dataset

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_gsm8k.jsonl"
            count = extract_gsm8k(output_path)

            assert count == 2
            assert output_path.exists()

            with open(output_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 2

                # Check first sample
                sample1 = json.loads(lines[0])
                assert sample1["question"] == "What is 2+2?"
                assert sample1["answer"] == "4"
                assert sample1["source"] == "gsm8k"

                # Check second sample
                sample2 = json.loads(lines[1])
                assert sample2["question"] == "What is 3+3?"
                assert sample2["answer"] == "6"
                assert sample2["source"] == "gsm8k"

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_gsm8k_limit(self, mock_load_dataset):
        """Test GSM8K extraction with limit parameter."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"question": f"Question {i}", "answer": f"The answer is {i}. The final answer is {i}."}
            for i in range(100)
        ]))
        mock_load_dataset.return_value = mock_dataset

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_gsm8k_limited.jsonl"
            count = extract_gsm8k(output_path, limit=10)

            assert count == 10

            with open(output_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 10

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_math_basic(self, mock_load_dataset):
        """Test basic MATH extraction with mocked data."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"problem": "Solve for x: x^2 = 4", "solution": "The solution is x=2. \\boxed{2}"},
            {"problem": "What is 5*5?", "solution": "5 times 5 is 25. \\boxed{25}"},
        ]))
        mock_load_dataset.return_value = mock_dataset

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_math.jsonl"
            count = extract_math(output_path)

            assert count == 2
            assert output_path.exists()

            with open(output_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 2

                sample1 = json.loads(lines[0])
                assert sample1["question"] == "Solve for x: x^2 = 4"
                assert sample1["answer"] == "2"
                assert sample1["source"] == "math"

                sample2 = json.loads(lines[1])
                assert sample2["question"] == "What is 5*5?"
                assert sample2["answer"] == "25"
                assert sample2["source"] == "math"

    @patch("src.data.static_extractor.load_dataset")
    def test_extract_math_limit(self, mock_load_dataset):
        """Test MATH extraction with limit parameter."""
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter([
            {"problem": f"Problem {i}", "solution": f"Solution {i}. \\boxed{{{i}}}"}
            for i in range(50)
        ]))
        mock_load_dataset.return_value = mock_dataset

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_math_limited.jsonl"
            count = extract_math(output_path, limit=5)

            assert count == 5

            with open(output_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 5

    @patch("src.data.static_extractor.extract_gsm8k")
    @patch("src.data.static_extractor.extract_math")
    def test_extract_static_qa_combined(self, mock_extract_math, mock_extract_gsm8k):
        """Test combined extraction of both datasets."""
        mock_extract_gsm8k.return_value = 10
        mock_extract_math.return_value = 5

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            results = extract_static_qa(
                output_dir=output_dir,
                gsm8k_limit=10,
                math_limit=5,
                combine=True
            )

            assert "gsm8k" in results
            assert "math" in results
            assert "combined" in results

            assert Path(results["gsm8k"]).exists()
            assert Path(results["math"]).exists()
            assert Path(results["combined"]).exists()

    def test_extract_gsm8k_answer_parsing(self):
        """Test that GSM8K answer parsing correctly extracts final answer."""
        # This is a unit test for the parsing logic itself
        test_cases = [
            ("The answer is 4. The final answer is 4.", "4"),
            ("The answer is 100. The final answer is 100.", "100"),
            ("Some text #### 42", "42"),
            ("No special format here", "No special format here"),
        ]

        for raw_answer, expected in test_cases:
            if "####" in raw_answer:
                final_answer = raw_answer.split("####")[-1].strip()
            else:
                final_answer = raw_answer.strip()
            assert final_answer == expected, f"Failed for: {raw_answer}"

    def test_extract_math_answer_parsing(self):
        """Test that MATH answer parsing correctly extracts boxed answer."""
        test_cases = [
            ("The solution is x=2. \\boxed{2}", "2"),
            ("Answer: \\boxed{42}", "42"),
            ("No boxed answer", "No boxed answer"),
            ("Multiple \\boxed{1} and \\boxed{2}", "1"),  # Should get first
        ]

        for solution, expected in test_cases:
            if "\\boxed{" in solution:
                start_idx = solution.find("\\boxed{") + len("\\boxed{")
                end_idx = solution.find("}", start_idx)
                if end_idx != -1:
                    final_answer = solution[start_idx:end_idx]
                else:
                    final_answer = solution
            else:
                final_answer = solution.strip()
            assert final_answer == expected, f"Failed for: {solution}"
