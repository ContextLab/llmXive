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
from datasets import Dataset

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.data.static_extractor import extract_gsm8k, extract_math, extract_static_qa


class TestStaticExtractor:
    """Test cases for static data extraction functions."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for raw and processed data."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_dir = Path(tmp_dir) / "raw"
            processed_dir = Path(tmp_dir) / "processed"
            raw_dir.mkdir()
            processed_dir.mkdir()
            yield raw_dir, processed_dir

    @pytest.fixture
    def mock_gsm8k_data(self, temp_dirs):
        """Create mock GSM8K JSONL file."""
        raw_dir, _ = temp_dirs
        data = [
            {"question": "What is 2+2?", "answer": "4"},
            {"question": "What is 10*10?", "answer": "100"},
            {"question": "Missing answer", "answer": ""},
            {"question": "", "answer": "Empty question"}
        ]
        file_path = raw_dir / "train.jsonl"
        with open(file_path, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        return file_path

    @pytest.fixture
    def mock_math_data(self, temp_dirs):
        """Create mock MATH JSONL file."""
        raw_dir, _ = temp_dirs
        data = [
            {"problem": "Solve for x: 2x = 4", "solution": "x = 2"},
            {"problem": "Geometry problem", "solution": "Area = pi*r^2"},
            {"problem": "Missing solution", "solution": ""},
            {"problem": "", "solution": "Empty problem"}
        ]
        file_path = raw_dir / "train.jsonl"
        with open(file_path, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
        return file_path

    def test_extract_gsm8k_valid(self, temp_dirs, mock_gsm8k_data):
        """Test extraction of valid GSM8K samples."""
        raw_dir, processed_dir = temp_dirs
        output_path = processed_dir / "static_gsm8k.jsonl"
        
        count = extract_gsm8k(raw_dir / "gsm8k", output_path)
        
        assert count == 2  # Only 2 valid samples (skipping empty answer/question)
        assert output_path.exists()
        
        with open(output_path) as f:
            lines = f.readlines()
            assert len(lines) == 2
            for line in lines:
                record = json.loads(line)
                assert "question" in record
                assert "answer" in record
                assert record["source"] == "gsm8k"

    def test_extract_gsm8k_invalid_skipped(self, temp_dirs, mock_gsm8k_data):
        """Test that invalid GSM8K samples are skipped."""
        raw_dir, processed_dir = temp_dirs
        output_path = processed_dir / "static_gsm8k.jsonl"
        
        count = extract_gsm8k(raw_dir / "gsm8k", output_path)
        
        assert count == 2  # Should skip the 2 invalid ones

    def test_extract_math_valid(self, temp_dirs, mock_math_data):
        """Test extraction of valid MATH samples."""
        raw_dir, processed_dir = temp_dirs
        output_path = processed_dir / "static_math.jsonl"
        
        count = extract_math(raw_dir / "math", output_path)
        
        assert count == 2
        assert output_path.exists()
        
        with open(output_path) as f:
            lines = f.readlines()
            assert len(lines) == 2
            for line in lines:
                record = json.loads(line)
                assert "question" in record
                assert "answer" in record
                assert record["source"] == "math"

    def test_extract_static_qa_integration(self, temp_dirs, mock_gsm8k_data, mock_math_data):
        """Test the full extraction pipeline."""
        raw_dir, processed_dir = temp_dirs
        
        # Mock the config to use our temp directories
        mock_config = MagicMock()
        mock_config.data_raw_dir = str(raw_dir)
        mock_config.data_processed_dir = str(processed_dir)
        
        # We need to create the subdirectories for gsm8k and math
        (raw_dir / "gsm8k").mkdir()
        (raw_dir / "math").mkdir()
        
        # Move mock files to correct locations
        gsm8k_src = raw_dir / "train.jsonl"
        math_src = raw_dir / "train.jsonl"
        
        # Re-create files in correct subdirs for the test
        gsm8k_path = raw_dir / "gsm8k" / "train.jsonl"
        math_path = raw_dir / "math" / "train.jsonl"
        
        # Copy content
        with open(gsm8k_src) as f_in:
            with open(gsm8k_path, 'w') as f_out:
                f_out.write(f_in.read())
        with open(math_src) as f_in:
            with open(math_path, 'w') as f_out:
                f_out.write(f_in.read())
        
        results = extract_static_qa(mock_config, max_samples_per_dataset=10)
        
        assert "gsm8k" in results
        assert "math" in results
        assert "combined" in results
        assert results["gsm8k"] == 2
        assert results["math"] == 2
        assert results["combined"] == 4

    def test_extract_gsm8k_max_samples(self, temp_dirs, mock_gsm8k_data):
        """Test that max_samples limits the output."""
        raw_dir, processed_dir = temp_dirs
        output_path = processed_dir / "static_gsm8k.jsonl"
        
        count = extract_gsm8k(raw_dir / "gsm8k", output_path, max_samples=1)
        
        assert count == 1
        with open(output_path) as f:
            assert len(f.readlines()) == 1
