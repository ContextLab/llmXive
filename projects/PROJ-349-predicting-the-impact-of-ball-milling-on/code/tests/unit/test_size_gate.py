"""
Unit tests for the size gate utility (T015c).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import logging

# Import the module under test
import sys
# Ensure the code directory is in the path if not already
if 'code' not in sys.path:
    sys.path.insert(0, 'code')

from src.utils.size_gate import (
    read_row_count,
    load_flagged_entries,
    trigger_ocr_fallback,
    check_size_gate,
    ROW_COUNT_PATH,
    FLAGGED_PSD_PATH,
    MIN_ROWS_WARNING
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Creates a temporary directory structure for data files."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    return processed_dir

@pytest.fixture
def temp_root(tmp_path):
    """Creates a temporary root to mimic project structure."""
    root = tmp_path
    (root / "data" / "processed").mkdir(parents=True)
    (root / "data").mkdir(exist_ok=True)
    return root

class TestReadRowCount:
    def test_read_row_count_success(self, temp_data_dir):
        count_file = temp_data_dir / "row_count.json"
        count_file.write_text(json.dumps({"count": 500}))
        
        with patch('src.utils.size_gate.ROW_COUNT_PATH', count_file):
            count = read_row_count()
            assert count == 500

    def test_read_row_count_empty(self, temp_data_dir):
        count_file = temp_data_dir / "row_count.json"
        count_file.write_text(json.dumps({"count": 0}))
        
        with patch('src.utils.size_gate.ROW_COUNT_PATH', count_file):
            count = read_row_count()
            assert count == 0

    def test_read_row_count_file_not_found(self, temp_data_dir):
        # Point to a non-existent file
        non_existent = temp_data_dir / "missing.json"
        
        with patch('src.utils.size_gate.ROW_COUNT_PATH', non_existent):
            with pytest.raises(FileNotFoundError):
                read_row_count()

    def test_read_row_count_missing_key(self, temp_data_dir):
        count_file = temp_data_dir / "row_count.json"
        count_file.write_text(json.dumps({"wrong_key": 500}))
        
        with patch('src.utils.size_gate.ROW_COUNT_PATH', count_file):
            with pytest.raises(ValueError):
                read_row_count()

class TestLoadFlaggedEntries:
    def test_load_flagged_entries_success(self, temp_root):
        flagged_file = temp_root / "data" / "flagged_psd.json"
        data = [
            {"experiment_id": "exp_1", "issue_type": "image", "image_path": "/tmp/img.png"},
            {"experiment_id": "exp_2", "issue_type": "image", "image_path": "/tmp/img2.png"}
        ]
        flagged_file.write_text(json.dumps(data))

        with patch('src.utils.size_gate.FLAGGED_PSD_PATH', flagged_file):
            entries = load_flagged_entries()
            assert len(entries) == 2
            assert entries[0]["experiment_id"] == "exp_1"

    def test_load_flagged_entries_file_not_found(self, temp_root):
        # Ensure file doesn't exist
        flagged_file = temp_root / "data" / "flagged_psd.json"
        if flagged_file.exists():
            flagged_file.unlink()

        with patch('src.utils.size_gate.FLAGGED_PSD_PATH', flagged_file):
            entries = load_flagged_entries()
            assert entries == []

    def test_load_flagged_entries_invalid_json(self, temp_root):
        flagged_file = temp_root / "data" / "flagged_psd.json"
        flagged_file.write_text("not valid json")

        with patch('src.utils.size_gate.FLAGGED_PSD_PATH', flagged_file):
            entries = load_flagged_entries()
            assert entries == []

    def test_load_flagged_entries_not_list(self, temp_root):
        flagged_file = temp_root / "data" / "flagged_psd.json"
        flagged_file.write_text(json.dumps({"key": "value"}))

        with patch('src.utils.size_gate.FLAGGED_PSD_PATH', flagged_file):
            entries = load_flagged_entries()
            assert entries == []

class TestTriggerOcrFallback:
    @patch('src.utils.size_gate.extract_psd_from_image')
    def test_trigger_ocr_fallback_success(self, mock_extract, temp_root):
        entries = [
            {"experiment_id": "exp_1", "image_path": "/tmp/img1.png"},
            {"experiment_id": "exp_2", "image_path": "/tmp/img2.png"}
        ]
        mock_extract.return_value = {"d50": 10.5}

        count = trigger_ocr_fallback(entries)
        assert count == 2
        assert mock_extract.call_count == 2
        mock_extract.assert_any_call("/tmp/img1.png", "exp_1")
        mock_extract.assert_any_call("/tmp/img2.png", "exp_2")

    @patch('src.utils.size_gate.extract_psd_from_image')
    def test_trigger_ocr_fallback_missing_image_path(self, mock_extract, temp_root):
        entries = [
            {"experiment_id": "exp_1"}, # Missing image_path
            {"experiment_id": "exp_2", "image_path": "/tmp/img2.png"}
        ]
        
        count = trigger_ocr_fallback(entries)
        # Should skip the first one
        assert count == 1
        mock_extract.assert_called_once_with("/tmp/img2.png", "exp_2")

    @patch('src.utils.size_gate.extract_psd_from_image')
    def test_trigger_ocr_fallback_exception_handling(self, mock_extract, temp_root):
        entries = [
            {"experiment_id": "exp_1", "image_path": "/tmp/img1.png"},
            {"experiment_id": "exp_2", "image_path": "/tmp/img2.png"}
        ]
        mock_extract.side_effect = [
            {"d50": 10.5}, # Success
            RuntimeError("OCR Failed") # Failure
        ]

        count = trigger_ocr_fallback(entries)
        # Should process both (log error for second, but count as attempted/processed in loop logic)
        # The function counts 'processed_count' only on success in the implementation?
        # Let's check implementation: it increments on success.
        # Wait, the implementation increments on success.
        # So count should be 1.
        assert count == 1

    def test_trigger_ocr_fallback_empty_list(self, temp_root):
        count = trigger_ocr_fallback([])
        assert count == 0

class TestCheckSizeGate:
    @patch('src.utils.size_gate.read_row_count')
    @patch('src.utils.size_gate.load_flagged_entries')
    @patch('src.utils.size_gate.trigger_ocr_fallback')
    def test_check_size_gate_above_threshold(
        self, mock_ocr, mock_load, mock_read, temp_root, caplog
    ):
        mock_read.return_value = 200
        mock_load.return_value = []
        
        with caplog.at_level(logging.INFO):
            result = check_size_gate()
        
        assert result is True
        assert "Dataset size (200 rows) meets the target threshold" in caplog.text
        mock_ocr.assert_not_called()

    @patch('src.utils.size_gate.read_row_count')
    @patch('src.utils.size_gate.load_flagged_entries')
    @patch('src.utils.size_gate.trigger_ocr_fallback')
    def test_check_size_gate_below_threshold_no_flagged(
        self, mock_ocr, mock_load, mock_read, temp_root, caplog
    ):
        mock_read.return_value = 100
        mock_load.return_value = []
        
        with caplog.at_level(logging.WARNING):
            result = check_size_gate()
        
        assert result is True
        assert "CRITICAL WARNING" in caplog.text
        mock_ocr.assert_not_called()

    @patch('src.utils.size_gate.read_row_count')
    @patch('src.utils.size_gate.load_flagged_entries')
    @patch('src.utils.size_gate.trigger_ocr_fallback')
    def test_check_size_gate_below_threshold_with_flagged(
        self, mock_ocr, mock_load, mock_read, temp_root, caplog
    ):
        mock_read.return_value = 100
        mock_load.return_value = [{"id": 1}]
        
        with caplog.at_level(logging.WARNING):
            result = check_size_gate()
        
        assert result is True
        assert "CRITICAL WARNING" in caplog.text
        mock_load.assert_called_once()
        mock_ocr.assert_called_once()

    @patch('src.utils.size_gate.read_row_count')
    def test_check_size_gate_file_not_found(self, mock_read, temp_root):
        mock_read.side_effect = FileNotFoundError("File not found")
        
        result = check_size_gate()
        assert result is False