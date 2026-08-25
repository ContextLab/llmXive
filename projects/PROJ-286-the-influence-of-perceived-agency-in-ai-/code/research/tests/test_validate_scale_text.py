"""
Tests for T000b: validate_scale_text.py
"""
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.research.validate_scale_text import (
    load_validation_report,
    fetch_scale_items,
    compare_items,
    write_validation_report,
    main
)


def test_load_validation_report_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "report.json"
        data = {"citations": [{"title": "Test"}]}
        with open(path, 'w') as f:
            json.dump(data, f)
        
        result = load_validation_report(path)
        assert result == data


def test_load_validation_report_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_validation_report(path)


def test_compare_items_match():
    items1 = ["A", "B", "C"]
    items2 = ["A", "B", "C"]
    assert compare_items(items1, items2) is True


def test_compare_items_mismatch():
    items1 = ["A", "B", "C"]
    items2 = ["A", "B", "D"]
    assert compare_items(items1, items2) is False


def test_compare_items_length_mismatch():
    items1 = ["A", "B"]
    items2 = ["A", "B", "C"]
    assert compare_items(items1, items2) is False


@patch('code.research.validate_scale_text.requests.get')
def test_fetch_scale_items_json(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = ["Item 1", "Item 2", "Item 3"]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = fetch_scale_items("http://example.com/data.json")
    assert result == ["Item 1", "Item 2", "Item 3"]


@patch('code.research.validate_scale_text.requests.get')
def test_fetch_scale_items_text_with_numbers(mock_get):
    mock_response = MagicMock()
    mock_response.text = "1. First item\n2. Second item\n3. Third item"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = fetch_scale_items("http://example.com/data.txt")
    assert result == ["First item", "Second item", "Third item"]


def test_write_validation_report():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "report.json"
        write_validation_report(path, "valid", "Test message", {"key": "value"})
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        assert data["status"] == "valid"
        assert data["message"] == "Test message"
        assert data["details"]["key"] == "value"


def test_main_success():
    # Create a mock validation report
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "validation_report.json"
        output_path = Path(tmpdir) / "scale_text_validation.json"
        
        report_data = {
            "citations": [
                {
                    "title": "Lee & See (2004)",
                    "source_url": "http://example.com/scale.json"
                }
            ]
        }
        with open(input_path, 'w') as f:
            json.dump(report_data, f)
        
        # Mock the fetch function to return the canonical items
        canonical_items = [
            "I felt that the system was acting on my behalf.",
            "I felt that the system was acting in my best interest.",
            "I felt that the system was reliable.",
            "I felt that the system was competent.",
            "I felt that the system was trustworthy.",
            "I felt that the system was predictable.",
            "I felt that the system was understandable.",
            "I felt that the system was controllable.",
            "I felt that the system was transparent.",
            "I felt that the system was honest.",
            "I felt that the system was benevolent.",
            "I felt that the system was acting in accordance with my values."
        ]
        
        with patch('code.research.validate_scale_text.fetch_scale_items', return_value=canonical_items):
            with patch('sys.argv', ['validate_scale_text.py', '--input', str(input_path), '--output', str(output_path)]):
                main()
                
                # Check output
                with open(output_path, 'r') as f:
                    result = json.load(f)
                
                assert result["status"] == "valid"


def test_main_mismatch():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "validation_report.json"
        output_path = Path(tmpdir) / "scale_text_validation.json"
        
        report_data = {
            "citations": [
                {
                    "title": "Lee & See (2004)",
                    "source_url": "http://example.com/scale.json"
                }
            ]
        }
        with open(input_path, 'w') as f:
            json.dump(report_data, f)
        
        # Return wrong items
        wrong_items = ["Wrong item 1"] * 12
        
        with patch('code.research.validate_scale_text.fetch_scale_items', return_value=wrong_items):
            with patch('sys.argv', ['validate_scale_text.py', '--input', str(input_path), '--output', str(output_path)]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                
                # Check output
                with open(output_path, 'r') as f:
                    result = json.load(f)
                
                assert result["status"] == "mismatch"