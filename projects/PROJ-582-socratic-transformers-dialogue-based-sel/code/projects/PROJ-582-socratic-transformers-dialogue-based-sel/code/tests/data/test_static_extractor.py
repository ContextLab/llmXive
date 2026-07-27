"""
Tests for the static QA extractor (T013).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Adjust path for imports if running directly
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.static_extractor import extract_gsm8k, extract_math, extract_static_qa


class TestStaticExtractor:
    """Test suite for static data extraction."""

    def test_extract_gsm8k_structure(self, tmp_path):
        """Verify GSM8K extraction produces correct schema."""
        mock_dataset = [
            {"question": "What is 2+2?", "answer": "The answer is 4."},
            {"question": "What is 3*3?", "answer": "The answer is 9."}
        ]

        output_file = tmp_path / "gsm8k_test.jsonl"

        with patch("src.data.static_extractor.load_dataset") as mock_load:
            mock_load.return_value = mock_dataset
            result = extract_gsm8k(output_file, limit=2)

        assert len(result) == 2
        assert output_file.exists()

        with open(output_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 2

            for line in lines:
                record = json.loads(line)
                assert "source" in record
                assert record["source"] == "gsm8k"
                assert "question" in record
                assert "answer" in record
                assert record["type"] == "static_baseline"

    def test_extract_math_structure(self, tmp_path):
        """Verify MATH extraction produces correct schema."""
        mock_dataset = [
            {"problem": "Solve for x: x+1=2", "solution": "x=1", "answer": "1"},
            {"problem": "What is 10/2?", "solution": "10 divided by 2 is 5.", "answer": "5"}
        ]

        output_file = tmp_path / "math_test.jsonl"

        with patch("src.data.static_extractor.load_dataset") as mock_load:
            mock_load.return_value = mock_dataset
            result = extract_math(output_file, limit=2)

        assert len(result) == 2
        assert output_file.exists()

        with open(output_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 2

            for line in lines:
                record = json.loads(line)
                assert "source" in record
                assert record["source"] == "math"
                assert "question" in record
                assert "answer" in record
                assert record["type"] == "static_baseline"

    def test_extract_static_qa_integration(self, tmp_path):
        """Test the full extraction pipeline with mocked datasets."""
        gsm8k_mock = [
            {"question": "GSM Q1", "answer": "A1"},
            {"question": "GSM Q2", "answer": "A2"}
        ]
        math_mock = [
            {"problem": "MATH P1", "solution": "S1", "answer": "A1"},
            {"problem": "MATH P2", "solution": "S2", "answer": "A2"}
        ]

        with patch("src.data.static_extractor.load_dataset") as mock_load:
            # Mock returns different datasets based on call arguments or simply return a list
            # Since load_dataset is called twice with different args, we need side_effect
            def side_effect(*args, **kwargs):
                if args[0] == "gsm8k":
                    return gsm8k_mock
                elif args[0] == "hendrycks/competition_math":
                    return math_mock
                return []

            mock_load.side_effect = side_effect

            results = extract_static_qa(
                gsm8k_limit=2,
                math_limit=2,
                base_output_dir=tmp_path
            )

            assert "gsm8k" in results
            assert "math" in results

            # Verify files exist and contain data
            with open(results["gsm8k"], "r") as f:
                gsm8k_lines = f.readlines()
                assert len(gsm8k_lines) == 2

            with open(results["math"], "r") as f:
                math_lines = f.readlines()
                assert len(math_lines) == 2

    def test_empty_dataset_handling(self, tmp_path):
        """Ensure extraction handles empty datasets gracefully."""
        output_file = tmp_path / "empty_test.jsonl"

        with patch("src.data.static_extractor.load_dataset") as mock_load:
            mock_load.return_value = []
            result = extract_gsm8k(output_file, limit=0)

        assert len(result) == 0
        assert output_file.exists()
        assert output_file.stat().st_size == 0