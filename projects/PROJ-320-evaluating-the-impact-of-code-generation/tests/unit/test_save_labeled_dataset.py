"""
Unit tests for T017: save_labeled_dataset.py
"""
import pytest
import os
import sys
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.save_labeled_dataset import LabeledPR, save_labeled_dataset, load_classified_prs

class TestLabeledPRSchema:
    """Tests for the Pydantic validation schema."""

    def test_valid_record(self):
        """Test that a valid record passes validation."""
        data = {
            "pr_id": 123,
            "source_type": "llm",
            "confidence_score": 0.95,
            "flagged": False,
            "detector_score": 0.88
        }
        record = LabeledPR(**data)
        assert record.pr_id == 123
        assert record.source_type == "llm"
        assert record.confidence_score == 0.95

    def test_invalid_source_type(self):
        """Test that invalid source_type raises error."""
        data = {
            "pr_id": 123,
            "source_type": "robot",
            "confidence_score": 0.95,
            "flagged": False,
            "detector_score": 0.88
        }
        with pytest.raises(ValueError):
            LabeledPR(**data)

    def test_confidence_out_of_range(self):
        """Test that confidence_score > 1.0 raises error."""
        data = {
            "pr_id": 123,
            "source_type": "llm",
            "confidence_score": 1.5,
            "flagged": False,
            "detector_score": 0.88
        }
        with pytest.raises(ValueError):
            LabeledPR(**data)

    def test_detector_score_out_of_range(self):
        """Test that detector_score < 0.0 raises error."""
        data = {
            "pr_id": 123,
            "source_type": "human",
            "confidence_score": 0.5,
            "flagged": True,
            "detector_score": -0.1
        }
        with pytest.raises(ValueError):
            LabeledPR(**data)

    def test_case_insensitive_source_type(self):
        """Test that 'LLM' is normalized to 'llm'."""
        data = {
            "pr_id": 123,
            "source_type": "LLM",
            "confidence_score": 0.5,
            "flagged": False,
            "detector_score": 0.5
        }
        record = LabeledPR(**data)
        assert record.source_type == "llm"

class TestSaveLabeledDataset:
    """Tests for the save_labeled_dataset function."""

    @pytest.fixture
    def temp_csv_path(self, tmp_path):
        """Create a temporary CSV path."""
        return tmp_path / "test_output.csv"

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        logger = MagicMock()
        logger.info = MagicMock()
        logger.warning = MagicMock()
        logger.error = MagicMock()
        return logger

    def test_save_valid_records(self, temp_csv_path, mock_logger):
        """Test saving valid records to CSV."""
        prs = [
            {"pr_id": 1, "source_type": "llm", "confidence_score": 0.9, "flagged": False, "detector_score": 0.8},
            {"pr_id": 2, "source_type": "human", "confidence_score": 0.4, "flagged": True, "detector_score": 0.3}
        ]
        
        count = save_labeled_dataset(prs, str(temp_csv_path), mock_logger)
        
        assert count == 2
        assert temp_csv_path.exists()
        
        with open(temp_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['pr_id'] == '1'
            assert rows[0]['source_type'] == 'llm'

    def test_skip_invalid_records(self, temp_csv_path, mock_logger):
        """Test that invalid records are skipped and logged."""
        prs = [
            {"pr_id": 1, "source_type": "llm", "confidence_score": 0.9, "flagged": False, "detector_score": 0.8},
            {"pr_id": 2, "source_type": "invalid", "confidence_score": 0.9, "flagged": False, "detector_score": 0.8}, # Invalid source
            {"pr_id": 3, "source_type": "human", "confidence_score": 1.5, "flagged": False, "detector_score": 0.8} # Invalid score
        ]
        
        count = save_labeled_dataset(prs, str(temp_csv_path), mock_logger)
        
        assert count == 1 # Only the first one is valid
        assert mock_logger.warning.called # Should have logged warnings for invalid ones

    def test_empty_input(self, temp_csv_path, mock_logger):
        """Test saving empty list."""
        prs = []
        count = save_labeled_dataset(prs, str(temp_csv_path), mock_logger)
        assert count == 0
        assert temp_csv_path.exists()
        with open(temp_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            assert len(list(reader)) == 0