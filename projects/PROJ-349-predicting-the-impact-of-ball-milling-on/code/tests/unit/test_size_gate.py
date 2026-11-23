"""
Unit tests for the size gate and flagged entry processor (T015c).
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.utils.size_gate import (
    read_row_count,
    load_flagged_entries,
    trigger_ocr_fallback,
    check_size_gate,
    run_size_gate_pipeline
)
from src.exceptions import InsufficientDataError

class TestReadRowCount:
    def test_read_row_count_success(self, temp_dir):
        count_file = Path(temp_dir) / "count.json"
        with open(count_file, 'w') as f:
            json.dump({'count': 200}, f)

        assert read_row_count(count_file) == 200

    def test_read_row_count_file_not_found(self, temp_dir):
        with pytest.raises(FileNotFoundError):
            read_row_count(Path(temp_dir) / "nonexistent.json")

    def test_read_row_count_invalid_json(self, temp_dir):
        count_file = Path(temp_dir) / "bad.json"
        with open(count_file, 'w') as f:
            f.write("not json")
        with pytest.raises(json.JSONDecodeError):
            read_row_count(count_file)

    def test_read_row_count_missing_key(self, temp_dir):
        count_file = Path(temp_dir) / "missing.json"
        with open(count_file, 'w') as f:
            json.dump({'data': 100}, f)
        with pytest.raises(KeyError):
            read_row_count(count_file)


class TestLoadFlaggedEntries:
    def test_load_flagged_entries_success(self, temp_dir):
        flagged_file = Path(temp_dir) / "flagged.json"
        data = [
            {'experiment_id': '1', 'issue_type': 'missing_psd', 'source': 'A'},
            {'experiment_id': '2', 'issue_type': 'missing_psd', 'source': 'B'}
        ]
        with open(flagged_file, 'w') as f:
            json.dump(data, f)

        result = load_flagged_entries(flagged_file)
        assert len(result) == 2
        assert result[0]['experiment_id'] == '1'

    def test_load_flagged_entries_file_not_found(self, temp_dir):
        result = load_flagged_entries(Path(temp_dir) / "nonexistent.json")
        assert result == []

    def test_load_flagged_entries_invalid_json(self, temp_dir):
        flagged_file = Path(temp_dir) / "bad.json"
        with open(flagged_file, 'w') as f:
            f.write("bad json")
        result = load_flagged_entries(flagged_file)
        assert result == []


class TestTriggerOcrFallback:
    @patch('src.utils.size_gate.extract_psd_from_image')
    def test_trigger_ocr_fallback_disabled(self, mock_extract, temp_dir):
        flagged_entries = [{'experiment_id': '1'}]
        config = {'ocr': {'enabled': False}}
        result = trigger_ocr_fallback(flagged_entries, config)
        assert result is None
        mock_extract.assert_not_called()

    @patch('src.utils.size_gate.extract_psd_from_image')
    def test_trigger_ocr_fallback_success(self, mock_extract, temp_dir):
        # Create a dummy image file
        img_path = Path(temp_dir) / "dummy.png"
        img_path.touch()

        flagged_entries = [
            {'experiment_id': '1', 'image_path': str(img_path)}
        ]
        config = {'ocr': {'enabled': True}}
        mock_extract.return_value = {'d10': 1.0, 'd50': 2.0, 'd90': 3.0}

        result = trigger_ocr_fallback(flagged_entries, config)
        assert result is not None
        assert len(result) == 1
        assert result[0]['d10'] == 1.0
        mock_extract.assert_called_once()

    @patch('src.utils.size_gate.extract_psd_from_image')
    def test_trigger_ocr_fallback_missing_image(self, mock_extract, temp_dir):
        flagged_entries = [
            {'experiment_id': '1', 'image_path': '/nonexistent/path.png'}
        ]
        config = {'ocr': {'enabled': True}}
        result = trigger_ocr_fallback(flagged_entries, config)
        assert result is None
        mock_extract.assert_not_called()

    @patch('src.utils.size_gate.extract_psd_from_image')
    def test_trigger_ocr_fallback_exception_handling(self, mock_extract, temp_dir):
        img_path = Path(temp_dir) / "dummy.png"
        img_path.touch()

        flagged_entries = [
            {'experiment_id': '1', 'image_path': str(img_path)}
        ]
        config = {'ocr': {'enabled': True}}
        mock_extract.side_effect = Exception("OCR Failed")

        result = trigger_ocr_fallback(flagged_entries, config)
        # Should return empty list or None if all fail
        assert result is None or result == []


class TestCheckSizeGate:
    def test_check_size_gate_pass(self):
        # Should not raise
        check_size_gate(150, minimum_viable=150)
        check_size_gate(200, minimum_viable=150)

    def test_check_size_gate_fail(self):
        with pytest.raises(SystemExit) as exc_info:
            check_size_gate(149, minimum_viable=150)
        assert exc_info.value.code == 1

    def test_check_size_gate_empty(self):
        with pytest.raises(SystemExit) as exc_info:
            check_size_gate(0, minimum_viable=150)
        assert exc_info.value.code == 1


class TestRunSizeGatePipeline:
    @patch('src.utils.size_gate.load_config')
    @patch('src.utils.size_gate.load_flagged_entries')
    @patch('src.utils.size_gate.trigger_ocr_fallback')
    @patch('src.utils.size_gate.read_row_count')
    @patch('src.utils.size_gate.check_size_gate')
    def test_run_pipeline_success(
        self, mock_check, mock_read, mock_trigger, mock_load_flagged, mock_load_config, temp_dir
    ):
        flagged_file = Path(temp_dir) / "flagged.json"
        row_count_file = Path(temp_dir) / "count.json"

        with open(flagged_file, 'w') as f:
            json.dump([{'id': '1'}], f)
        with open(row_count_file, 'w') as f:
            json.dump({'count': 200}, f)

        mock_load_config.return_value = {'ocr': {'enabled': False}}
        mock_load_flagged.return_value = [{'id': '1'}]
        mock_trigger.return_value = []
        mock_read.return_value = 200

        result = run_size_gate_pipeline(
            row_count_path=row_count_file,
            flagged_path=flagged_file
        )
        assert result == []
        mock_check.assert_called_once_with(200)

    @patch('src.utils.size_gate.load_config')
    @patch('src.utils.size_gate.load_flagged_entries')
    @patch('src.utils.size_gate.trigger_ocr_fallback')
    @patch('src.utils.size_gate.read_row_count')
    @patch('src.utils.size_gate.check_size_gate')
    def test_run_pipeline_halt_on_size(
        self, mock_check, mock_read, mock_trigger, mock_load_flagged, mock_load_config, temp_dir
    ):
        flagged_file = Path(temp_dir) / "flagged.json"
        row_count_file = Path(temp_dir) / "count.json"

        with open(flagged_file, 'w') as f:
            json.dump([{'id': '1'}], f)
        with open(row_count_file, 'w') as f:
            json.dump({'count': 100}, f)

        mock_load_config.return_value = {'ocr': {'enabled': False}}
        mock_load_flagged.return_value = [{'id': '1'}]
        mock_trigger.return_value = []
        mock_read.return_value = 100
        mock_check.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            run_size_gate_pipeline(
                row_count_path=row_count_file,
                flagged_path=flagged_file
            )

# Fixtures
@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def temp_image_file(temp_dir):
    img_path = Path(temp_dir) / "test.png"
    img_path.touch()
    return img_path

@pytest.fixture
def temp_detected_images_json(temp_dir):
    json_path = Path(temp_dir) / "detected.json"
    with open(json_path, 'w') as f:
        json.dump([{"page": 1, "path": "test.png"}], f)
    return json_path

@pytest.fixture
def temp_output_dir(temp_dir):
    return temp_dir