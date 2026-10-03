import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import sys

from code.research.validate_scale_text import (
    load_validation_report,
    fetch_scale_items_from_spec,
    compare_items,
    write_validation_report,
    main
)

def test_load_validation_report_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"items": ["Item 1", "Item 2"]}, f)
        f.flush()
        path = Path(f.name)
    
    data = load_validation_report(path)
    assert data["items"] == ["Item 1", "Item 2"]
    path.unlink()

def test_load_validation_report_missing():
    with pytest.raises(FileNotFoundError):
        load_validation_report(Path("/nonexistent/file.json"))

def test_compare_items_match():
    s = ["Item 1", "Item 2"]
    p = ["Item 1", "Item 2"]
    assert compare_items(s, p) is True

def test_compare_items_mismatch():
    s = ["Item 1", "Item 2"]
    p = ["Item 1", "Item 3"]
    assert compare_items(s, p) is False

def test_compare_items_length_mismatch():
    s = ["Item 1"]
    p = ["Item 1", "Item 2"]
    assert compare_items(s, p) is False

def test_fetch_scale_items_json():
    content = "```json\n[\"Q1\", \"Q2\"]\n```"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        f.flush()
        path = Path(f.name)
    
    items = fetch_scale_items_from_spec(path)
    assert items == ["Q1", "Q2"]
    path.unlink()

def test_fetch_scale_items_text_with_numbers():
    content = "```json\n[\"1. Question One\", \"2. Question Two\"]\n```"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        f.flush()
        path = Path(f.name)
    
    items = fetch_scale_items_from_spec(path)
    assert items == ["1. Question One", "2. Question Two"]
    path.unlink()

def test_write_validation_report():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "report.md"
        details = {
            "timestamp": "2023-01-01",
            "source_file": "src.json",
            "spec_file": "spec.md",
            "item_count": 1,
            "match_result": True,
            "message": "OK"
        }
        write_validation_report(out_path, "VERIFIED", details)
        assert out_path.exists()
        content = out_path.read_text()
        assert "VERIFIED" in content
        assert "OK" in content

def test_main_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create source log
        source_log = tmp_path / "item_source_log.json"
        json.dump({"items": ["A", "B"]}, source_log.open('w'))
        
        # Create spec file
        spec_file = tmp_path / "trust_scale_items.md"
        spec_file.write_text("```json\n[\"A\", \"B\"]\n```")
        
        # Output
        out_report = tmp_path / "verification_report.md"
        
        with patch('sys.argv', ['main', 
                                '--source-log', str(source_log),
                                '--spec-file', str(spec_file),
                                '--output-report', str(out_report)]):
            main()
        
        assert out_report.exists()
        assert "VERIFIED" in out_report.read_text()

def test_main_mismatch():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create source log
        source_log = tmp_path / "item_source_log.json"
        json.dump({"items": ["A", "B"]}, source_log.open('w'))
        
        # Create spec file with mismatch
        spec_file = tmp_path / "trust_scale_items.md"
        spec_file.write_text("```json\n[\"A\", \"C\"]\n```")
        
        out_report = tmp_path / "verification_report.md"
        
        with patch('sys.argv', ['main', 
                                '--source-log', str(source_log),
                                '--spec-file', str(spec_file),
                                '--output-report', str(out_report)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
        
        assert out_report.exists()
        assert "MISMATCH" in out_report.read_text()