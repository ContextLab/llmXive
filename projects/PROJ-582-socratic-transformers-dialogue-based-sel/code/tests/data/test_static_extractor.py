import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.static_extractor import extract_gsm8k, extract_math, extract_static_qa, write_jsonl

class TestStaticExtractor:
    """Test suite for static QA extractor functionality."""

    @patch('src.data.static_extractor.load_dataset')
    def test_extract_gsm8k(self, mock_load_dataset):
        """Test GSM8K extraction returns correct structure."""
        # Mock dataset
        mock_dataset = [
            {"question": "What is 2+2?", "answer": "The answer is 4."},
            {"question": "What is 3*3?", "answer": "The answer is 9."}
        ]
        mock_load_dataset.return_value = mock_dataset

        records = extract_gsm8k(max_samples=2)

        assert len(records) == 2
        assert all("question" in r for r in records)
        assert all("answer" in r for r in records)
        assert all(r["source"] == "gsm8k" for r in records)
        assert all(r["split"] == "train" for r in records)

    @patch('src.data.static_extractor.load_dataset')
    def test_extract_math(self, mock_load_dataset):
        """Test MATH extraction returns correct structure."""
        # Mock dataset
        mock_dataset = [
            {"problem": "Solve for x: x+2=5", "solution": "x=3"},
            {"problem": "What is the derivative of x^2?", "solution": "2x"}
        ]
        mock_load_dataset.return_value = mock_dataset

        records = extract_math(max_samples=2)

        assert len(records) == 2
        assert all("question" in r for r in records)
        assert all("answer" in r for r in records)
        assert all(r["source"] == "math" for r in records)

    @patch('src.data.static_extractor.extract_gsm8k')
    @patch('src.data.static_extractor.extract_math')
    def test_extract_static_qa_combined(self, mock_math, mock_gsm8k):
        """Test combined extraction returns both sources."""
        mock_gsm8k.return_value = [{"question": "Q1", "answer": "A1", "source": "gsm8k", "split": "train"}]
        mock_math.return_value = [{"question": "Q2", "answer": "A2", "source": "math", "split": "train"}]

        records = extract_static_qa()

        assert len(records) == 2
        assert records[0]["source"] == "gsm8k"
        assert records[1]["source"] == "math"

    def test_write_jsonl(self):
        """Test writing records to JSONL file."""
        records = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"}
        ]

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            temp_path = f.name

        try:
            write_jsonl(records, temp_path)

            with open(temp_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            assert len(lines) == 2
            for line in lines:
                data = json.loads(line)
                assert "question" in data
                assert "answer" in data
        finally:
            os.unlink(temp_path)

    @patch('src.data.static_extractor.load_dataset')
    def test_extract_with_max_samples(self, mock_load_dataset):
        """Test that max_samples limits the output."""
        mock_dataset = [
            {"question": f"Q{i}", "answer": f"A{i}"}
            for i in range(100)
        ]
        mock_load_dataset.return_value = mock_dataset

        records = extract_gsm8k(max_samples=5)

        assert len(records) == 5
        assert all(r["source"] == "gsm8k" for r in records)
