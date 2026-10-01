"""
Unit tests for T018: code/export_snippets.py
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the functions we are testing
from code.export_snippets import (
    load_generation_results,
    calculate_line_count,
    export_to_csv,
    main
)
import config

def test_calculate_line_count_empty():
    assert calculate_line_count("") == 0
    assert calculate_line_count(None) == 0
    assert calculate_line_count("   \n  \n   ") == 0

def test_calculate_line_count_basic():
    code = "def hello():\n    pass\n"
    assert calculate_line_count(code) == 2

def test_calculate_line_count_complex():
    code = """import os
    import sys

    def main():
        print("Hello")
    """
    assert calculate_line_count(code) == 5

def test_export_to_csv_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.csv"
        results = [
            {
                "snippet_id": "s1",
                "model": "StarCoder",
                "prompt_id": "p1",
                "code": "print('hi')",
                "timestamp": "2023-01-01"
            }
        ]
        
        count = export_to_csv(results, output_path)
        
        assert count == 1
        assert output_path.exists()
        
        with open(output_path, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1
        assert rows[0]["snippet_id"] == "s1"
        assert rows[0]["model"] == "StarCoder"
        assert rows[0]["code"] == "print('hi')"
        assert int(rows[0]["line_count"]) == 1

def test_load_generation_results_dict_format():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.json"
        data = {
            "results": [
                {"snippet_id": "1", "model": "m1", "prompt_id": "p1", "code": "x"}
            ]
        }
        with open(input_path, "w") as f:
            json.dump(data, f)
        
        result = load_generation_results(input_path)
        assert len(result) == 1
        assert result[0]["snippet_id"] == "1"

def test_load_generation_results_list_format():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.json"
        data = [
            {"snippet_id": "1", "model": "m1", "prompt_id": "p1", "code": "x"}
        ]
        with open(input_path, "w") as f:
            json.dump(data, f)
        
        result = load_generation_results(input_path)
        assert len(result) == 1

def test_load_generation_results_missing_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_generation_results(input_path)

def test_main_integration():
    """Test the full flow of main() with mock data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup mock config
        mock_project_root = Path(tmpdir)
        data_dir = mock_project_root / "data" / "generated"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = data_dir / "generation_results.json"
        output_file = data_dir / "snippets.csv"
        
        # Create mock results
        mock_results = [
            {"snippet_id": "s1", "model": "M1", "prompt_id": "p1", "code": "def a(): pass"},
            {"snippet_id": "s2", "model": "M2", "prompt_id": "p1", "code": "def b(): pass"},
            {"snippet_id": "s3", "model": "M3", "prompt_id": "p2", "code": "def c(): pass"},
        ]
        with open(results_file, "w") as f:
            json.dump(mock_results, f)
        
        # Patch config.PROJECT_ROOT
        with patch.object(config, 'PROJECT_ROOT', mock_project_root):
            count = main()
        
        assert count == 3
        assert output_file.exists()
        
        with open(output_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        assert rows[0]["snippet_id"] == "s1"
        assert rows[0]["line_count"] == "1"
        assert rows[2]["model"] == "M3"