"""
Unit tests for src/analysis/split_dataset.py (T021).
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import sys
# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.analysis.split_dataset import (
    load_llm_detections,
    split_by_llm_flag,
    save_split_datasets,
    run_split_analysis
)
from code.src.detection.schema import LLMCodeDetectionResult


class TestSplitDataset:
    """Test suite for the dataset splitting logic."""

    @pytest.fixture
    def sample_detections(self):
        """Provide a list of sample detection records."""
        return [
            {
                "pr_id": "101",
                "file_path": "src/main.py",
                "llm_code_flag": True,
                "confidence": 0.95
            },
            {
                "pr_id": "102",
                "file_path": "src/utils.py",
                "llm_code_flag": False,
                "confidence": 0.10
            },
            {
                "pr_id": "103",
                "file_path": "src/test.py",
                "llm_code_flag": True,
                "confidence": 0.88
            },
            {
                "pr_id": "104",
                "file_path": "src/missing_flag.py",
                # Missing flag intentionally
                "confidence": 0.50
            }
        ]

    @pytest.fixture
    def temp_input_file(self, sample_detections):
        """Create a temporary input JSON file."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(sample_detections, f)
        path = Path(f.name)
        yield path
        path.unlink()

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_llm_detections_success(self, temp_input_file, sample_detections):
        """Test successful loading of detections."""
        result = load_llm_detections(temp_input_file)
        assert len(result) == len(sample_detections)
        assert result[0]["pr_id"] == "101"

    def test_load_llm_detections_file_not_found(self):
        """Test loading from a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_llm_detections(Path("/nonexistent/path/file.json"))

    def test_load_llm_detections_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises error."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{ invalid json }")
        with pytest.raises(json.JSONDecodeError):
            load_llm_detections(bad_file)

    def test_split_by_llm_flag(self, sample_detections):
        """Test correct splitting based on llm_code_flag."""
        human, llm = split_by_llm_flag(sample_detections)

        # Expected: 102 (False), 104 (None) -> Human
        # Expected: 101 (True), 103 (True) -> LLM
        assert len(human) == 2
        assert len(llm) == 2

        human_ids = [item["pr_id"] for item in human]
        llm_ids = [item["pr_id"] for item in llm]

        assert "102" in human_ids
        assert "104" in human_ids
        assert "101" in llm_ids
        assert "103" in llm_ids

    def test_save_split_datasets(self, sample_detections, temp_output_dir):
        """Test saving split datasets to files."""
        human, llm = split_by_llm_flag(sample_detections)
        human_path, llm_path = save_split_datasets(human, llm, temp_output_dir)

        assert human_path.exists()
        assert llm_path.exists()

        with open(human_path, 'r') as f:
            saved_human = json.load(f)
        with open(llm_path, 'r') as f:
            saved_llm = json.load(f)

        assert len(saved_human) == len(human)
        assert len(saved_llm) == len(llm)

    def test_run_split_analysis_integration(self, temp_input_file, temp_output_dir):
        """Test the full integration of loading, splitting, and saving."""
        result = run_split_analysis(temp_input_file, temp_output_dir)

        assert result["total_input_records"] == 4
        assert result["human_written_count"] == 2
        assert result["llm_generated_count"] == 2
        assert Path(result["human_written_output_path"]).exists()
        assert Path(result["llm_generated_output_path"]).exists()

    def test_run_split_analysis_empty_input(self, temp_output_dir, tmp_path):
        """Test handling of an empty input list."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("[]")

        result = run_split_analysis(empty_file, temp_output_dir)

        assert result["total_input_records"] == 0
        assert result["human_written_count"] == 0
        assert result["llm_generated_count"] == 0